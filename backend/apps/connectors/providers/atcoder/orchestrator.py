import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderNetworkError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderServerError,
    ProviderSyncDisabledError,
    ProviderTimeoutError,
    UnsupportedSourceError,
)
from apps.connectors.models import AtCoderStats, AtCoderSyncState, PlatformAccount
from apps.connectors.providers.atcoder.connector import AtCoderConnector
from apps.connectors.providers.atcoder.submission_service import (
    AtCoderSubmissionIngestionService,
)

logger = logging.getLogger(__name__)


class OverallSyncStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SourceSyncStatus(StrEnum):
    SUCCESS = "success"
    SKIPPED_FRESH = "skipped_fresh"
    FAILED = "failed"
    BLOCKED = "blocked"
    DISABLED = "disabled"


class SyncErrorCode(StrEnum):
    PROVIDER_DISABLED = "provider_disabled"
    RATE_LIMITED = "rate_limited"
    ACCESS_DENIED = "access_denied"
    TIMEOUT = "timeout"
    UPSTREAM_SERVER_ERROR = "upstream_server_error"
    SCHEMA_CHANGED = "schema_changed"
    NETWORK_ERROR = "network_error"
    INVALID_ACCOUNT = "invalid_account"
    SATURATED_TIMESTAMP_BOUNDARY = "saturated_timestamp_boundary"
    PROVIDER_ERROR = "provider_error"
    COOLDOWN_ACTIVE = "cooldown_active"


@dataclass(frozen=True)
class ProviderSyncResult:
    source: str
    status: SourceSyncStatus
    updated: bool = False
    using_cached_data: bool = False
    updated_at: datetime | None = None
    attempted_at: datetime | None = None
    error_code: SyncErrorCode | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status in {
            SourceSyncStatus.SUCCESS,
            SourceSyncStatus.SKIPPED_FRESH,
        }

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "updated": self.updated,
            "updated_at": self.updated_at,
            "attempted_at": self.attempted_at,
            "using_cached_data": self.using_cached_data,
            "error_code": self.error_code.value if self.error_code else None,
            "message": self.message,
        }
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class AtCoderSyncResult:
    status: OverallSyncStatus
    attempted_at: datetime
    rating: ProviderSyncResult
    submissions: ProviderSyncResult

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "attempted_at": self.attempted_at,
            "sources": {
                "rating": self.rating.as_dict(),
                "submissions": self.submissions.as_dict(),
            },
        }


class AtCoderSyncOrchestrator:
    """Coordinate AtCoder's independent rating and submission sources."""

    def __init__(
        self,
        rating_connector: AtCoderConnector | None = None,
        submission_service: AtCoderSubmissionIngestionService | None = None,
    ):
        self.rating_connector = rating_connector or AtCoderConnector()
        self.submission_service = (
            submission_service or AtCoderSubmissionIngestionService()
        )

    def sync(self, platform_account: PlatformAccount) -> AtCoderSyncResult:
        self._validate_account(platform_account)
        attempted_at = timezone.now()
        state, _ = AtCoderSyncState.objects.get_or_create(
            platform_account=platform_account
        )
        PlatformAccount.objects.filter(pk=platform_account.pk).update(
            last_sync_attempted_at=attempted_at
        )

        rating = self.sync_rating_source(platform_account, state, attempted_at)
        submissions = self.sync_submission_source(
            platform_account,
            state,
            attempted_at,
        )
        overall = self.combine_status(rating, submissions)

        state.overall_status = overall.value
        state.save(update_fields=["overall_status", "updated_at"])
        if rating.updated or submissions.updated:
            PlatformAccount.objects.filter(pk=platform_account.pk).update(
                last_synced_at=attempted_at
            )

        logger.info(
            "AtCoder combined synchronization finished",
            extra={
                "platform": "atcoder",
                "platform_account_id": platform_account.pk,
                "overall_status": overall.value,
                "rating_status": rating.status.value,
                "rating_error_code": (
                    rating.error_code.value if rating.error_code else None
                ),
                "submission_status": submissions.status.value,
                "submission_error_code": (
                    submissions.error_code.value if submissions.error_code else None
                ),
            },
        )
        return AtCoderSyncResult(
            status=overall,
            attempted_at=attempted_at,
            rating=rating,
            submissions=submissions,
        )

    def sync_submissions_only(
        self,
        platform_account: PlatformAccount,
    ) -> ProviderSyncResult:
        """Compatibility path used by the temporary /sync-submissions action."""
        self._validate_account(platform_account)
        state, _ = AtCoderSyncState.objects.get_or_create(
            platform_account=platform_account
        )
        return self.sync_submission_source(platform_account, state, timezone.now())

    def sync_rating_source(
        self,
        platform_account: PlatformAccount,
        state: AtCoderSyncState,
        now: datetime,
    ) -> ProviderSyncResult:
        freshness = self._rating_freshness(platform_account)
        if not settings.ATCODER_HISTORY_SYNC_ENABLED:
            result = self._disabled_result("atcoder_history", freshness)
            self._store_source_result(state, "rating", result)
            return result
        cooldown_reference = (
            state.rating_sync_attempted_at
            or platform_account.last_sync_attempted_at
            or platform_account.last_synced_at
        )
        remaining = self._remaining_cooldown(
            cooldown_reference,
            settings.ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS,
            now,
        )
        if remaining:
            result = self._fresh_skip_result(
                "atcoder_history",
                freshness,
                cooldown_reference,
                remaining,
                state.rating_error_code,
            )
            self._store_source_result(state, "rating", result)
            return result

        self._mark_attempt(state, "rating", now)
        try:
            self.rating_connector.sync(
                platform_account,
                update_account_sync_metadata=False,
            )
            freshness = self._rating_freshness(platform_account)
            result = ProviderSyncResult(
                source="atcoder_history",
                status=SourceSyncStatus.SUCCESS,
                updated=True,
                updated_at=freshness,
                attempted_at=now,
            )
        except Exception as exc:
            result = self._failure_result(
                "atcoder_history",
                exc,
                freshness,
                now,
            )
        self._store_source_result(state, "rating", result)
        self._log_source(platform_account, result)
        return result

    def sync_submission_source(
        self,
        platform_account: PlatformAccount,
        state: AtCoderSyncState,
        now: datetime,
    ) -> ProviderSyncResult:
        freshness = self._submission_freshness(platform_account)
        if not settings.ATCODER_PROBLEMS_SYNC_ENABLED:
            result = self._disabled_result("atcoder_problems", freshness)
            self._store_source_result(state, "submission", result)
            return result
        remaining = self._remaining_cooldown(
            state.submission_sync_attempted_at,
            settings.ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS,
            now,
        )
        if remaining:
            result = self._fresh_skip_result(
                "atcoder_problems",
                freshness,
                state.submission_sync_attempted_at,
                remaining,
                state.submission_error_code,
            )
            self._store_source_result(state, "submission", result)
            return result

        self._mark_attempt(state, "submission", now)
        try:
            ingestion = self.submission_service.sync(platform_account)
            freshness = ingestion.updated_at or self._submission_freshness(
                platform_account
            )
            if ingestion.error_code == SyncErrorCode.SATURATED_TIMESTAMP_BOUNDARY:
                result = ProviderSyncResult(
                    source="atcoder_problems",
                    status=SourceSyncStatus.BLOCKED,
                    updated=True,
                    updated_at=freshness,
                    attempted_at=now,
                    error_code=SyncErrorCode.SATURATED_TIMESTAMP_BOUNDARY,
                    message=(
                        "Submission pagination is blocked at a saturated timestamp "
                        "boundary; cached data was preserved."
                    ),
                    details=self._submission_details(ingestion),
                )
            else:
                result = ProviderSyncResult(
                    source="atcoder_problems",
                    status=SourceSyncStatus.SUCCESS,
                    updated=True,
                    updated_at=freshness,
                    attempted_at=now,
                    details=self._submission_details(ingestion),
                )
        except Exception as exc:
            current_freshness = self._submission_freshness(platform_account)
            result = self._failure_result(
                "atcoder_problems",
                exc,
                current_freshness,
                now,
                updated=(
                    current_freshness is not None
                    and current_freshness != freshness
                ),
            )
        self._store_source_result(state, "submission", result)
        self._log_source(platform_account, result)
        return result

    @staticmethod
    def combine_status(
        rating: ProviderSyncResult,
        submissions: ProviderSyncResult,
    ) -> OverallSyncStatus:
        active = [
            result
            for result in (rating, submissions)
            if result.status != SourceSyncStatus.DISABLED
        ]
        if not active:
            return OverallSyncStatus.FAILED
        healthy_count = sum(result.is_healthy for result in active)
        if healthy_count == len(active):
            return OverallSyncStatus.SUCCESS
        if healthy_count:
            return OverallSyncStatus.PARTIAL
        return OverallSyncStatus.FAILED

    @staticmethod
    def _validate_account(platform_account: PlatformAccount) -> None:
        if platform_account.platform != PlatformAccount.Platform.ATCODER:
            raise UnsupportedSourceError(
                "Combined AtCoder synchronization requires an AtCoder account."
            )

    @staticmethod
    def _remaining_cooldown(
        attempted_at: datetime | None,
        cooldown_seconds: int,
        now: datetime,
    ) -> int:
        if attempted_at is None or cooldown_seconds <= 0:
            return 0
        remaining = cooldown_seconds - (now - attempted_at).total_seconds()
        return max(0, math.ceil(remaining))

    @staticmethod
    def _rating_freshness(platform_account: PlatformAccount) -> datetime | None:
        return AtCoderStats.objects.filter(
            platform_account=platform_account
        ).values_list("rating_data_updated_at", flat=True).first()

    @staticmethod
    def _submission_freshness(
        platform_account: PlatformAccount,
    ) -> datetime | None:
        return AtCoderStats.objects.filter(
            platform_account=platform_account
        ).values_list("submission_data_updated_at", flat=True).first()

    @staticmethod
    def _disabled_result(
        source: str,
        freshness: datetime | None,
    ) -> ProviderSyncResult:
        return ProviderSyncResult(
            source=source,
            status=SourceSyncStatus.DISABLED,
            using_cached_data=freshness is not None,
            updated_at=freshness,
            error_code=SyncErrorCode.PROVIDER_DISABLED,
            message="This synchronization source is disabled by configuration.",
        )

    @staticmethod
    def _fresh_skip_result(
        source: str,
        freshness: datetime | None,
        attempted_at: datetime | None,
        retry_after_seconds: int,
        previous_error_code: str,
    ) -> ProviderSyncResult:
        if freshness is None:
            try:
                error_code = SyncErrorCode(previous_error_code)
            except ValueError:
                error_code = SyncErrorCode.COOLDOWN_ACTIVE
            return ProviderSyncResult(
                source=source,
                status=SourceSyncStatus.BLOCKED,
                attempted_at=attempted_at,
                error_code=error_code,
                message=(
                    "Source cooldown is active and no successfully cached data "
                    "is available yet."
                ),
                details={"retry_after_seconds": retry_after_seconds},
            )
        return ProviderSyncResult(
            source=source,
            status=SourceSyncStatus.SKIPPED_FRESH,
            using_cached_data=freshness is not None,
            updated_at=freshness,
            attempted_at=attempted_at,
            message="Source is still within its account cooldown.",
            details={"retry_after_seconds": retry_after_seconds},
        )

    @classmethod
    def _failure_result(
        cls,
        source: str,
        exc: Exception,
        freshness: datetime | None,
        attempted_at: datetime,
        updated: bool = False,
    ) -> ProviderSyncResult:
        error_code, message = cls._normalize_error(exc)
        return ProviderSyncResult(
            source=source,
            status=SourceSyncStatus.FAILED,
            updated=updated,
            using_cached_data=freshness is not None,
            updated_at=freshness,
            attempted_at=attempted_at,
            error_code=error_code,
            message=message,
        )

    @staticmethod
    def _normalize_error(exc: Exception) -> tuple[SyncErrorCode, str]:
        mapping: tuple[tuple[type[Exception], SyncErrorCode, str], ...] = (
            (
                InvalidExternalAccountError,
                SyncErrorCode.INVALID_ACCOUNT,
                "The AtCoder account could not be validated.",
            ),
            (
                ProviderSyncDisabledError,
                SyncErrorCode.PROVIDER_DISABLED,
                "This synchronization source is disabled by configuration.",
            ),
            (
                ProviderRateLimitError,
                SyncErrorCode.RATE_LIMITED,
                "The provider rate limit was reached. Cached data was preserved.",
            ),
            (
                ProviderAccessDeniedError,
                SyncErrorCode.ACCESS_DENIED,
                "The provider denied access. Cached data was preserved.",
            ),
            (
                ProviderTimeoutError,
                SyncErrorCode.TIMEOUT,
                "The provider timed out. Cached data was preserved.",
            ),
            (
                ProviderNetworkError,
                SyncErrorCode.NETWORK_ERROR,
                "The provider could not be reached. Cached data was preserved.",
            ),
            (
                ProviderServerError,
                SyncErrorCode.UPSTREAM_SERVER_ERROR,
                "The provider is temporarily unavailable. Cached data was preserved.",
            ),
            (
                ProviderSchemaError,
                SyncErrorCode.SCHEMA_CHANGED,
                "The provider response was incompatible. Cached data was preserved.",
            ),
            (
                ExternalServiceError,
                SyncErrorCode.PROVIDER_ERROR,
                "The provider synchronization failed. Cached data was preserved.",
            ),
        )
        for exception_type, code, message in mapping:
            if isinstance(exc, exception_type):
                return code, message
        logger.exception("Unexpected AtCoder synchronization failure", exc_info=exc)
        return (
            SyncErrorCode.PROVIDER_ERROR,
            "The synchronization failed. Cached data was preserved.",
        )

    @staticmethod
    def _mark_attempt(
        state: AtCoderSyncState,
        source_field: str,
        attempted_at: datetime,
    ) -> None:
        field_name = f"{source_field}_sync_attempted_at"
        setattr(state, field_name, attempted_at)
        state.save(update_fields=[field_name, "updated_at"])

    @staticmethod
    def _store_source_result(
        state: AtCoderSyncState,
        source_field: str,
        result: ProviderSyncResult,
    ) -> None:
        status_field = f"{source_field}_status"
        error_field = f"{source_field}_error_code"
        setattr(state, status_field, result.status.value)
        setattr(
            state,
            error_field,
            result.error_code.value if result.error_code else "",
        )
        state.save(update_fields=[status_field, error_field, "updated_at"])

    @staticmethod
    def _submission_details(ingestion) -> dict[str, Any]:
        return {
            "pages_fetched": ingestion.pages_fetched,
            "indexed_submission_count": ingestion.indexed_submission_count,
            "backfill_complete": ingestion.backfill_complete,
            "progress_status": ingestion.progress_status,
        }

    @staticmethod
    def _log_source(
        platform_account: PlatformAccount,
        result: ProviderSyncResult,
    ) -> None:
        logger.info(
            "AtCoder source synchronization finished",
            extra={
                "platform": "atcoder",
                "source": result.source,
                "platform_account_id": platform_account.pk,
                "source_status": result.status.value,
                "error_code": (
                    result.error_code.value if result.error_code else None
                ),
                "updated": result.updated,
                "using_cached_data": result.using_cached_data,
            },
        )
