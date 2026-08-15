from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    ProviderRateLimitError,
    ProviderSchemaError,
)
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    AtCoderSyncState,
    PlatformAccount,
    PlatformRatingEvent,
    PlatformStatsSnapshot,
)

User = get_user_model()


def rating_profile(rating: int = 1200, contest_id: str = "abc100") -> dict:
    occurred_at = datetime(2024, 1, 1, tzinfo=datetime_timezone.utc)
    return {
        "handle": "atcoder_user",
        "profile_url": "https://atcoder.jp/users/atcoder_user",
        "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
        "rating_events": [
            {
                "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
                "external_contest_id": contest_id,
                "contest_name": f"Contest {contest_id}",
                "rank": 10,
                "performance": rating + 50,
                "inner_performance": rating + 50,
                "old_rating": rating - 100,
                "new_rating": rating,
                "rating_change": 100,
                "is_rated": True,
                "occurred_at": occurred_at,
                "metadata": {},
            }
        ],
        "current_rating": rating,
        "max_rating": rating,
        "rated_contest_count": 1,
        "last_rated_at": occurred_at,
        "last_performance": rating + 50,
    }


def raw_submission(
    submission_id: int = 1,
    epoch_second: int = 100,
    result: str = "AC",
) -> dict:
    return {
        "id": submission_id,
        "epoch_second": epoch_second,
        "problem_id": f"abc100_{submission_id}",
        "contest_id": "abc100",
        "user_id": "atcoder_user",
        "language": "Python (CPython 3.11)",
        "point": 100.0 if result == "AC" else 0.0,
        "length": 100,
        "result": result,
        "execution_time": 10,
    }


@override_settings(
    ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS=0,
    ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS=0,
    ATCODER_PROBLEMS_MIN_REQUEST_INTERVAL_SECONDS=0,
)
class AtCoderOrchestrationTests(APITestCase):
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
        self.client.force_authenticate(user=self.user)
        self.sync_url = reverse("platform-account-sync", args=[self.account.pk])

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_both_sources_succeed(self, mocked_rating, mocked_submissions):
        mocked_rating.return_value = rating_profile()
        mocked_submissions.return_value = [raw_submission()]

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["sources"]["rating"]["status"], "success")
        self.assertEqual(
            response.data["sources"]["submissions"]["status"], "success"
        )
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertIsNotNone(stats.rating_data_updated_at)
        self.assertIsNotNone(stats.submission_data_updated_at)
        self.account.refresh_from_db()
        self.assertIsNotNone(self.account.last_sync_attempted_at)
        self.assertIsNotNone(self.account.last_synced_at)
        state = AtCoderSyncState.objects.get(platform_account=self.account)
        self.assertEqual(state.overall_status, AtCoderSyncState.OverallStatus.SUCCESS)
        self.assertIsNone(self.account.ownership_verified_at)

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_rating_success_submission_failure_is_partial_and_preserves_cache(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        old_submission_freshness = timezone.now()
        AtCoderStats.objects.create(
            platform_account=self.account,
            solved_count=428,
            attempted_count=500,
            submission_data_updated_at=old_submission_freshness,
            submission_backfill_complete=True,
        )
        mocked_rating.return_value = rating_profile(1400)
        mocked_submissions.side_effect = ProviderRateLimitError("limited")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "partial")
        self.assertEqual(response.data["sources"]["rating"]["status"], "success")
        submission_result = response.data["sources"]["submissions"]
        self.assertEqual(submission_result["status"], "failed")
        self.assertEqual(submission_result["error_code"], "rate_limited")
        self.assertTrue(submission_result["using_cached_data"])
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1400)
        self.assertEqual(stats.solved_count, 428)
        self.assertEqual(
            stats.submission_data_updated_at,
            old_submission_freshness,
        )
        self.assertGreater(stats.rating_data_updated_at, old_submission_freshness)

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_rating_failure_submission_success_is_partial_and_preserves_cache(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        old_rating_freshness = timezone.now()
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1542,
            max_rating=1600,
            rating_data_updated_at=old_rating_freshness,
        )
        mocked_rating.side_effect = ProviderSchemaError("changed")
        mocked_submissions.return_value = [raw_submission()]

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "partial")
        rating_result = response.data["sources"]["rating"]
        self.assertEqual(rating_result["status"], "failed")
        self.assertEqual(rating_result["error_code"], "schema_changed")
        self.assertTrue(rating_result["using_cached_data"])
        self.assertEqual(
            response.data["sources"]["submissions"]["status"], "success"
        )
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1542)
        self.assertEqual(stats.rating_data_updated_at, old_rating_freshness)
        self.assertGreater(stats.submission_data_updated_at, old_rating_freshness)

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_both_sources_fail_and_all_cached_data_is_preserved(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        old_freshness = timezone.now()
        stats = AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1500,
            solved_count=428,
            rating_data_updated_at=old_freshness,
            submission_data_updated_at=old_freshness,
            submission_backfill_complete=True,
        )
        PlatformStatsSnapshot.objects.create(
            platform_account=self.account,
            rating=1500,
            solved_count=428,
        )
        mocked_rating.side_effect = ExternalServiceError("history failed")
        mocked_submissions.side_effect = ExternalServiceError("submissions failed")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "failed")
        stats.refresh_from_db()
        self.assertEqual(stats.current_rating, 1500)
        self.assertEqual(stats.solved_count, 428)
        self.assertEqual(stats.rating_data_updated_at, old_freshness)
        self.assertEqual(stats.submission_data_updated_at, old_freshness)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)
        self.account.refresh_from_db()
        self.assertIsNone(self.account.last_synced_at)

    @override_settings(
        ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS=3600,
        ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS=0,
    )
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_history_cooldown_does_not_block_eligible_submissions(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        mocked_rating.return_value = rating_profile()
        mocked_submissions.return_value = [raw_submission()]
        self.client.post(self.sync_url)

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["sources"]["rating"]["status"], "skipped_fresh"
        )
        self.assertEqual(
            response.data["sources"]["submissions"]["status"], "success"
        )
        self.assertEqual(mocked_rating.call_count, 1)
        self.assertEqual(mocked_submissions.call_count, 2)

    @override_settings(
        ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS=3600,
        ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS=3600,
    )
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_both_fresh_sources_skip_without_provider_calls(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        mocked_rating.return_value = rating_profile()
        mocked_submissions.return_value = [raw_submission()]
        self.client.post(self.sync_url)

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(
            response.data["sources"]["rating"]["status"], "skipped_fresh"
        )
        self.assertEqual(
            response.data["sources"]["submissions"]["status"],
            "skipped_fresh",
        )
        self.assertEqual(mocked_rating.call_count, 1)
        self.assertEqual(mocked_submissions.call_count, 1)

    @override_settings(
        ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS=3600,
        ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS=3600,
    )
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_submission_cooldown_does_not_block_eligible_history(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        mocked_rating.return_value = rating_profile()
        mocked_submissions.return_value = [raw_submission()]
        self.client.post(self.sync_url)
        AtCoderSyncState.objects.filter(platform_account=self.account).update(
            rating_sync_attempted_at=timezone.now() - timedelta(hours=2)
        )

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sources"]["rating"]["status"], "success")
        self.assertEqual(
            response.data["sources"]["submissions"]["status"],
            "skipped_fresh",
        )
        self.assertEqual(mocked_rating.call_count, 2)
        self.assertEqual(mocked_submissions.call_count, 1)

    @override_settings(ATCODER_HISTORY_SYNC_ENABLED=False)
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions",
        return_value=[],
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_disabled_history_is_neutral_when_submissions_succeed(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["sources"]["rating"]["status"], "disabled")
        mocked_rating.assert_not_called()
        mocked_submissions.assert_called_once()

    @override_settings(ATCODER_PROBLEMS_SYNC_ENABLED=False)
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile",
        return_value=rating_profile(),
    )
    def test_disabled_submissions_are_neutral_when_history_succeeds(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(
            response.data["sources"]["submissions"]["status"], "disabled"
        )
        mocked_rating.assert_called_once()
        mocked_submissions.assert_not_called()

    @override_settings(
        ATCODER_HISTORY_SYNC_ENABLED=False,
        ATCODER_PROBLEMS_SYNC_ENABLED=False,
    )
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_both_disabled_return_controlled_failed_result(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["status"], "failed")
        mocked_rating.assert_not_called()
        mocked_submissions.assert_not_called()

    @override_settings(ATCODER_PROBLEMS_MAX_PAGES_PER_SYNC=2)
    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile",
        return_value=rating_profile(),
    )
    def test_saturated_submission_boundary_is_explicit_and_safe(
        self,
        mocked_rating,
        mocked_submissions,
    ):
        saturated_page = [raw_submission(index, 100, "WA") for index in range(1, 501)]
        mocked_submissions.side_effect = [saturated_page, saturated_page]

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "partial")
        source = response.data["sources"]["submissions"]
        self.assertEqual(source["status"], "blocked")
        self.assertEqual(
            source["error_code"],
            "saturated_timestamp_boundary",
        )
        state = AtCoderSubmissionSyncState.objects.get(
            platform_account=self.account
        )
        self.assertEqual(state.progress_status, "blocked")
        self.assertEqual(state.last_submission_epoch, 100)
        self.assertEqual(state.last_submission_id, 500)
        self.assertEqual(AtCoderSubmission.objects.count(), 500)

    @override_settings(ATCODER_PROBLEMS_SYNC_ENABLED=False)
    @patch(
        "apps.connectors.providers.atcoder.connector."
        "AtCoderConnector.fetch_normalized_profile"
    )
    def test_incomplete_submission_stats_never_create_fake_zero_snapshots(
        self,
        mocked_rating,
    ):
        stats = AtCoderStats.objects.create(
            platform_account=self.account,
            solved_count=428,
            submission_backfill_complete=True,
        )
        mocked_rating.return_value = rating_profile(1200, "abc100")
        self.client.post(self.sync_url)

        stats.refresh_from_db()
        stats.submission_backfill_complete = False
        stats.save(update_fields=["submission_backfill_complete"])
        mocked_rating.return_value = rating_profile(1300, "abc200")
        self.client.post(self.sync_url)

        stats.refresh_from_db()
        stats.solved_count = 441
        stats.submission_backfill_complete = True
        stats.save(update_fields=["solved_count", "submission_backfill_complete"])
        mocked_rating.return_value = rating_profile(1400, "abc300")
        self.client.post(self.sync_url)

        snapshots = list(
            PlatformStatsSnapshot.objects.filter(
                platform_account=self.account
            ).order_by("id")
        )
        self.assertEqual(
            [snapshot.solved_count for snapshot in snapshots],
            [428, None, 441],
        )
        self.assertFalse(snapshots[1].metadata["submission_stats_complete"])
        self.assertTrue(snapshots[1].metadata["rating_complete"])

    def test_handle_change_clears_combined_source_state(self):
        AtCoderSyncState.objects.create(
            platform_account=self.account,
            overall_status=AtCoderSyncState.OverallStatus.PARTIAL,
            rating_status=AtCoderSyncState.SourceStatus.SUCCESS,
            submission_status=AtCoderSyncState.SourceStatus.FAILED,
            submission_error_code="rate_limited",
        )

        response = self.client.patch(
            reverse("platform-account-detail", args=[self.account.pk]),
            {"handle": "new_atcoder_user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["atcoder_sync_state"])
        self.assertFalse(AtCoderSyncState.objects.exists())
