from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderSyncDisabledError,
)
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    PlatformAccount,
)
from apps.connectors.providers.atcoder.submission_service import (
    AtCoderSubmissionIngestionService,
)

User = get_user_model()


def submission(
    submission_id: int,
    epoch_second: int,
    problem_id: str,
    result: str,
) -> dict:
    return {
        "id": submission_id,
        "epoch_second": epoch_second,
        "problem_id": problem_id,
        "contest_id": problem_id.rsplit("_", 1)[0],
        "user_id": "atcoder_user",
        "language": "Python (CPython 3.11.4)",
        "point": 100.0 if result == "AC" else 0.0,
        "length": 256,
        "result": result,
        "execution_time": 30,
    }


class FakeAtCoderProblemsClient:
    def __init__(self, batches=None, error=None):
        self.batches = list(batches or [])
        self.error = error
        self.calls: list[tuple[str, int]] = []

    def get_user_submissions(self, handle, from_second):
        self.calls.append((handle, from_second))
        if self.error is not None:
            raise self.error
        return self.batches.pop(0) if self.batches else []


class AtCoderSubmissionIngestionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPassword123!",
        )
        self.account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="atcoder_user",
        )

    def test_first_batch_persists_submissions_and_calculates_exact_metrics(self):
        batch = [
            submission(1, 100, "abc100_a", "WA"),
            submission(2, 101, "abc100_a", "WA"),
            submission(3, 102, "abc100_a", "AC"),
            submission(4, 103, "abc100_a", "AC"),
            submission(5, 104, "abc100_b", "WA"),
            submission(6, 105, "abc100_b", "TLE"),
            submission(7, 106, "abc100_c", "CE"),
            submission(8, 107, "abc100_c", "AC"),
        ]
        client = FakeAtCoderProblemsClient([batch])

        result = AtCoderSubmissionIngestionService(client=client).sync(self.account)

        self.assertEqual(result.indexed_submission_count, 8)
        self.assertTrue(result.backfill_complete)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.attempted_count, 3)
        self.assertEqual(stats.solved_count, 2)
        self.assertEqual(stats.accepted_submission_count, 3)
        self.assertEqual(stats.indexed_submission_count, 8)
        self.assertTrue(stats.submission_backfill_complete)
        self.assertIsNotNone(stats.submission_data_updated_at)

    def test_four_attempts_on_one_problem_have_distinct_metric_semantics(self):
        batch = [
            submission(1, 100, "abc100_a", "WA"),
            submission(2, 101, "abc100_a", "WA"),
            submission(3, 102, "abc100_a", "AC"),
            submission(4, 103, "abc100_a", "AC"),
        ]

        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([batch])
        ).sync(self.account)

        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.attempted_count, 1)
        self.assertEqual(stats.solved_count, 1)
        self.assertEqual(stats.accepted_submission_count, 2)
        self.assertEqual(stats.indexed_submission_count, 4)

    def test_submission_ingestion_preserves_independent_rating_fields(self):
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1542,
            max_rating=1600,
            rated_contest_count=25,
            rating_data_updated_at=timezone.now(),
        )

        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient(
                [[submission(1, 100, "abc100_a", "AC")]]
            )
        ).sync(self.account)

        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1542)
        self.assertEqual(stats.max_rating, 1600)
        self.assertEqual(stats.rated_contest_count, 25)
        self.assertEqual(stats.solved_count, 1)

    def test_repeated_batch_is_idempotent(self):
        batch = [submission(1, 100, "abc100_a", "AC")]
        service = AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([batch])
        )
        service.sync(self.account)

        second_client = FakeAtCoderProblemsClient([batch])
        AtCoderSubmissionIngestionService(client=second_client).sync(self.account)

        self.assertEqual(AtCoderSubmission.objects.count(), 1)
        self.assertEqual(
            AtCoderStats.objects.get(
                platform_account=self.account
            ).indexed_submission_count,
            1,
        )
        self.assertEqual(second_client.calls, [("atcoder_user", 100)])

    def test_repeated_submission_can_update_a_finalized_verdict(self):
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient(
                [[submission(1, 100, "abc100_a", "WJ")]]
            )
        ).sync(self.account)

        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient(
                [[submission(1, 100, "abc100_a", "AC")]]
            )
        ).sync(self.account)

        self.assertEqual(AtCoderSubmission.objects.count(), 1)
        self.assertEqual(AtCoderSubmission.objects.get().verdict, "AC")
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.solved_count, 1)
        self.assertEqual(stats.accepted_submission_count, 1)

    def test_same_second_boundary_is_refetched_without_skipping_new_id(self):
        first = [
            submission(10, 100, "abc100_a", "WA"),
            submission(11, 100, "abc100_a", "AC"),
        ]
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([first])
        ).sync(self.account)
        second_client = FakeAtCoderProblemsClient(
            [first + [submission(12, 100, "abc100_b", "AC")]]
        )

        AtCoderSubmissionIngestionService(client=second_client).sync(self.account)

        state = AtCoderSubmissionSyncState.objects.get(platform_account=self.account)
        self.assertEqual(second_client.calls, [("atcoder_user", 100)])
        self.assertEqual(state.last_submission_epoch, 100)
        self.assertEqual(state.last_submission_id, 12)
        self.assertEqual(AtCoderSubmission.objects.count(), 3)

    def test_first_sync_is_bounded_and_later_sync_resumes_from_cursor(self):
        full_page = [
            submission(index, index, f"abc{index}_a", "WA")
            for index in range(1, 501)
        ]
        first_client = FakeAtCoderProblemsClient([full_page])

        first_result = AtCoderSubmissionIngestionService(
            client=first_client,
            max_pages=1,
        ).sync(self.account)

        self.assertFalse(first_result.backfill_complete)
        self.assertEqual(first_result.progress_status, "backfilling")
        self.assertEqual(first_result.pages_fetched, 1)
        self.assertEqual(first_client.calls, [("atcoder_user", 0)])
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertFalse(stats.submission_backfill_complete)

        final_page = [
            submission(500, 500, "abc500_a", "WA"),
            submission(501, 501, "abc501_a", "AC"),
        ]
        later_client = FakeAtCoderProblemsClient([final_page])
        later_result = AtCoderSubmissionIngestionService(
            client=later_client,
            max_pages=1,
        ).sync(self.account)

        self.assertEqual(later_client.calls, [("atcoder_user", 500)])
        self.assertTrue(later_result.backfill_complete)
        self.assertEqual(later_result.indexed_submission_count, 501)

    def test_bounded_multi_page_run_stops_on_final_partial_page(self):
        full_page = [
            submission(index, index, f"abc{index}_a", "WA")
            for index in range(1, 501)
        ]
        final_page = [
            submission(500, 500, "abc500_a", "WA"),
            submission(501, 501, "abc501_a", "AC"),
        ]
        client = FakeAtCoderProblemsClient([full_page, final_page])

        result = AtCoderSubmissionIngestionService(
            client=client,
            max_pages=2,
        ).sync(self.account)

        self.assertEqual(result.pages_fetched, 2)
        self.assertTrue(result.backfill_complete)
        self.assertEqual(client.calls, [("atcoder_user", 0), ("atcoder_user", 500)])

    def test_saturated_same_second_boundary_stops_without_skipping(self):
        same_second_page = [
            submission(index, 100, f"abc100_{index}", "WA")
            for index in range(1, 501)
        ]
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([same_second_page]),
            max_pages=1,
        ).sync(self.account)
        repeated_client = FakeAtCoderProblemsClient([same_second_page])

        result = AtCoderSubmissionIngestionService(
            client=repeated_client,
            max_pages=2,
        ).sync(self.account)

        self.assertEqual(repeated_client.calls, [("atcoder_user", 100)])
        self.assertFalse(result.backfill_complete)
        self.assertEqual(result.progress_status, "blocked")
        self.assertEqual(result.error_code, "saturated_timestamp_boundary")
        self.assertEqual(result.last_submission_epoch, 100)
        self.assertEqual(result.last_submission_id, 500)
        self.assertEqual(AtCoderSubmission.objects.count(), 500)

    def test_empty_first_page_is_valid_complete_zero_state(self):
        result = AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([[]])
        ).sync(self.account)

        self.assertTrue(result.backfill_complete)
        self.assertEqual(result.progress_status, "caught_up")
        self.assertEqual(result.indexed_submission_count, 0)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.solved_count, 0)
        self.assertEqual(stats.attempted_count, 0)
        self.assertTrue(stats.submission_backfill_complete)

    def test_recent_submission_ordering_is_newest_first(self):
        batch = [
            submission(1, 100, "abc100_a", "WA"),
            submission(3, 101, "abc100_b", "AC"),
            submission(2, 101, "abc100_c", "TLE"),
        ]
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([batch])
        ).sync(self.account)

        ids = list(
            AtCoderSubmission.objects.values_list(
                "external_submission_id", flat=True
            )
        )

        self.assertEqual(ids, [3, 2, 1])

    def test_cursor_and_rows_roll_back_when_persistence_fails(self):
        initial = [submission(1, 100, "abc100_a", "AC")]
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient([initial])
        ).sync(self.account)
        old_state = AtCoderSubmissionSyncState.objects.get(
            platform_account=self.account
        )
        old_cursor = (
            old_state.last_submission_epoch,
            old_state.last_submission_id,
        )

        with patch.object(
            AtCoderStats.objects,
            "update_or_create",
            side_effect=IntegrityError("forced failure"),
        ):
            with self.assertRaises(IntegrityError):
                AtCoderSubmissionIngestionService(
                    client=FakeAtCoderProblemsClient(
                        [[submission(2, 101, "abc100_b", "AC")]]
                    )
                ).sync(self.account)

        state = AtCoderSubmissionSyncState.objects.get(platform_account=self.account)
        self.assertEqual(
            (state.last_submission_epoch, state.last_submission_id),
            old_cursor,
        )
        self.assertFalse(
            AtCoderSubmission.objects.filter(external_submission_id=2).exists()
        )

    def test_provider_failures_preserve_cached_data_state_and_freshness(self):
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient(
                [[submission(1, 100, "abc100_a", "AC")]]
            )
        ).sync(self.account)
        old_state = AtCoderSubmissionSyncState.objects.get(
            platform_account=self.account
        )
        old_updated_at = old_state.submission_data_updated_at
        failures = (
            ProviderRateLimitError("rate limited"),
            ExternalServiceError("server failure"),
            ExternalServiceError("timeout"),
            ProviderSchemaError("malformed JSON"),
            ProviderSyncDisabledError("disabled"),
        )

        for failure in failures:
            with self.subTest(failure=type(failure).__name__):
                with self.assertRaises(type(failure)):
                    AtCoderSubmissionIngestionService(
                        client=FakeAtCoderProblemsClient(error=failure)
                    ).sync(self.account)
                state = AtCoderSubmissionSyncState.objects.get(
                    platform_account=self.account
                )
                stats = AtCoderStats.objects.get(platform_account=self.account)
                self.assertEqual(state.last_submission_epoch, 100)
                self.assertEqual(state.submission_data_updated_at, old_updated_at)
                self.assertEqual(stats.solved_count, 1)
                self.assertEqual(stats.indexed_submission_count, 1)
                self.assertEqual(AtCoderSubmission.objects.count(), 1)

    def test_persisted_timestamp_is_timezone_aware(self):
        AtCoderSubmissionIngestionService(
            client=FakeAtCoderProblemsClient(
                [[submission(1, 1700000000, "abc100_a", "AC")]]
            )
        ).sync(self.account)

        stored = AtCoderSubmission.objects.get()
        self.assertEqual(
            stored.submitted_at,
            datetime.fromtimestamp(1700000000, tz=datetime_timezone.utc),
        )
