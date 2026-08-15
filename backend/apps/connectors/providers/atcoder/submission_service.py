import logging
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    PlatformAccount,
)
from apps.connectors.providers.atcoder.problems_client import AtCoderProblemsClient
from apps.connectors.providers.atcoder.problems_mapper import (
    normalize_atcoder_submissions,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AtCoderSubmissionSyncResult:
    pages_fetched: int
    indexed_submission_count: int
    backfill_complete: bool
    last_submission_epoch: int
    last_submission_id: int


class AtCoderSubmissionIngestionService:
    """Incrementally cache AtCoderProblems submissions for one AtCoder account."""

    def __init__(
        self,
        client: AtCoderProblemsClient | None = None,
        max_pages: int | None = None,
    ):
        self.client = client or AtCoderProblemsClient()
        configured_pages = (
            max_pages
            if max_pages is not None
            else settings.ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC
        )
        self.max_pages = max(1, configured_pages)

    def sync(
        self,
        platform_account: PlatformAccount,
    ) -> AtCoderSubmissionSyncResult:
        if platform_account.platform != PlatformAccount.Platform.ATCODER:
            raise UnsupportedSourceError(
                "Submission synchronization is only supported for AtCoder accounts."
            )

        existing_state = AtCoderSubmissionSyncState.objects.filter(
            platform_account=platform_account
        ).first()
        cursor_epoch = (
            existing_state.last_submission_epoch if existing_state is not None else 0
        )
        cursor_id = existing_state.last_submission_id if existing_state is not None else 0
        pages_fetched = 0
        indexed_count = AtCoderSubmission.objects.filter(
            platform_account=platform_account
        ).count()
        backfill_complete = existing_state.backfill_complete if existing_state else False

        for page_number in range(1, self.max_pages + 1):
            raw_batch = self.client.get_user_submissions(
                platform_account.handle,
                from_second=cursor_epoch,
            )
            pages_fetched += 1
            normalized_batch = normalize_atcoder_submissions(
                raw_batch,
                expected_handle=platform_account.handle,
            )
            page_complete = (
                len(raw_batch) < AtCoderProblemsClient.PROVIDER_PAGE_LIMIT
            )
            previous_cursor = (cursor_epoch, cursor_id)

            state, stats = self._persist_batch(
                platform_account=platform_account,
                submissions=normalized_batch,
                page_complete=page_complete,
            )
            cursor_epoch = state.last_submission_epoch
            cursor_id = state.last_submission_id
            indexed_count = stats.indexed_submission_count
            backfill_complete = state.backfill_complete

            logger.info(
                "AtCoderProblems submission batch synchronized",
                extra={
                    "provider": "atcoder_problems",
                    "operation": "user_submissions",
                    "platform_account_id": platform_account.pk,
                    "page": page_number,
                    "batch_count": len(normalized_batch),
                    "backfill_complete": backfill_complete,
                },
            )

            if page_complete:
                break

            if (cursor_epoch, cursor_id) <= previous_cursor:
                # The API cursor is timestamp-only and inclusive. Refuse to skip a
                # saturated same-second boundary that cannot advance safely.
                break

        return AtCoderSubmissionSyncResult(
            pages_fetched=pages_fetched,
            indexed_submission_count=indexed_count,
            backfill_complete=backfill_complete,
            last_submission_epoch=cursor_epoch,
            last_submission_id=cursor_id,
        )

    @staticmethod
    def _persist_batch(
        platform_account: PlatformAccount,
        submissions: list[dict],
        page_complete: bool,
    ) -> tuple[AtCoderSubmissionSyncState, AtCoderStats]:
        updated_at = timezone.now()

        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
                platform=PlatformAccount.Platform.ATCODER,
                handle=platform_account.handle,
            )
            state, _ = AtCoderSubmissionSyncState.objects.select_for_update().get_or_create(
                platform_account=locked_account
            )

            AtCoderSubmission.objects.bulk_create(
                [
                    AtCoderSubmission(
                        platform_account=locked_account,
                        **submission,
                    )
                    for submission in submissions
                ],
                update_conflicts=True,
                update_fields=[
                    "external_contest_id",
                    "external_problem_id",
                    "verdict",
                    "language",
                    "submitted_at",
                    "provider_epoch_second",
                    "execution_time_ms",
                    "code_size_bytes",
                    "metadata",
                ],
                unique_fields=["platform_account", "external_submission_id"],
            )

            if submissions:
                latest = max(
                    submissions,
                    key=lambda item: (
                        item["provider_epoch_second"],
                        item["external_submission_id"],
                    ),
                )
                latest_cursor = (
                    latest["provider_epoch_second"],
                    latest["external_submission_id"],
                )
                if latest_cursor > (
                    state.last_submission_epoch,
                    state.last_submission_id,
                ):
                    state.last_submission_epoch, state.last_submission_id = latest_cursor

            state.backfill_complete = page_complete
            state.submission_data_updated_at = updated_at
            state.save(
                update_fields=[
                    "last_submission_epoch",
                    "last_submission_id",
                    "backfill_complete",
                    "submission_data_updated_at",
                    "updated_at",
                ]
            )

            queryset = AtCoderSubmission.objects.filter(
                platform_account=locked_account
            )
            metrics = queryset.aggregate(
                indexed_submission_count=Count("id"),
                accepted_submission_count=Count("id", filter=Q(verdict="AC")),
                attempted_count=Count("external_problem_id", distinct=True),
                solved_count=Count(
                    "external_problem_id",
                    filter=Q(verdict="AC"),
                    distinct=True,
                ),
            )

            stats, _ = AtCoderStats.objects.update_or_create(
                platform_account=locked_account,
                defaults={
                    "solved_count": metrics["solved_count"],
                    "attempted_count": metrics["attempted_count"],
                    "accepted_submission_count": metrics[
                        "accepted_submission_count"
                    ],
                    "indexed_submission_count": metrics[
                        "indexed_submission_count"
                    ],
                    "submission_data_updated_at": updated_at,
                    "submission_backfill_complete": page_complete,
                },
            )

        return state, stats
