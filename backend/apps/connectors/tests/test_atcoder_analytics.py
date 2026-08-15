from datetime import datetime, timedelta
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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


class AtCoderAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="atcoder-analytics-user",
            email="atcoder-analytics@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse("atcoder-analytics")

    def test_endpoint_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.client."
        "AtCoderHistoryClient.get_algorithm_rating_history"
    )
    def test_no_account_returns_empty_database_only_contract(
        self,
        mocked_history,
        mocked_submissions,
    ):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "platform": "atcoder",
                "account": None,
                "sync": None,
                "stats": None,
                "rating_history": [],
                "recent_activity": [],
                "snapshots": [],
            },
        )
        mocked_history.assert_not_called()
        mocked_submissions.assert_not_called()

    def test_connected_never_synced_account_has_no_fabricated_stats(self):
        account = self._create_account()
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account"]["id"], account.id)
        self.assertEqual(
            response.data["account"]["profile_url"],
            "https://atcoder.jp/users/atcoder_user",
        )
        self.assertEqual(response.data["sync"]["status"], "never_synced")
        self.assertEqual(response.data["sync"]["rating"]["status"], "never")
        self.assertEqual(
            response.data["sync"]["submissions"]["progress"]["status"],
            "not_started",
        )
        self.assertIsNone(response.data["stats"])
        self.assertEqual(response.data["rating_history"], [])
        self.assertEqual(response.data["recent_activity"], [])
        self.assertEqual(response.data["snapshots"], [])

    @patch(
        "apps.connectors.providers.atcoder.problems_client."
        "AtCoderProblemsClient.get_user_submissions"
    )
    @patch(
        "apps.connectors.providers.atcoder.client."
        "AtCoderHistoryClient.get_algorithm_rating_history"
    )
    def test_full_success_returns_normalized_bounded_analytics_without_http(
        self,
        mocked_history,
        mocked_submissions,
    ):
        account = self._create_account()
        now = timezone.now()
        stats = AtCoderStats.objects.create(
            platform_account=account,
            current_rating=1542,
            max_rating=1681,
            rated_contest_count=47,
            last_performance=1602,
            rating_data_updated_at=now,
            solved_count=428,
            attempted_count=501,
            accepted_submission_count=683,
            indexed_submission_count=941,
            submission_data_updated_at=now,
            submission_backfill_complete=True,
        )
        AtCoderSyncState.objects.create(
            platform_account=account,
            overall_status=AtCoderSyncState.OverallStatus.SUCCESS,
            rating_status=AtCoderSyncState.SourceStatus.SUCCESS,
            rating_sync_attempted_at=now,
            submission_status=AtCoderSyncState.SourceStatus.SUCCESS,
            submission_sync_attempted_at=now,
        )
        AtCoderSubmissionSyncState.objects.create(
            platform_account=account,
            last_submission_epoch=124,
            last_submission_id=24,
            backfill_complete=True,
            progress_status=(
                AtCoderSubmissionSyncState.ProgressStatus.CAUGHT_UP
            ),
            submission_data_updated_at=now,
        )
        self._create_rating_event(
            account,
            "abc350",
            datetime(2024, 4, 20, tzinfo=datetime_timezone.utc),
            new_rating=1542,
        )
        self._create_rating_event(
            account,
            "abc100",
            datetime(2020, 1, 1, tzinfo=datetime_timezone.utc),
            new_rating=800,
        )
        self._create_rating_event(
            account,
            "ahc001",
            datetime(2021, 1, 1, tzinfo=datetime_timezone.utc),
            new_rating=1000,
            discipline="heuristic",
        )
        self._create_submissions(account, 25)
        older = PlatformStatsSnapshot.objects.create(
            platform_account=account,
            captured_at=now - timedelta(days=1),
            rating=1500,
            solved_count=None,
            contest_count=46,
            metadata={"submission_stats_complete": False},
        )
        newer = PlatformStatsSnapshot.objects.create(
            platform_account=account,
            captured_at=now,
            rating=1542,
            solved_count=428,
            contest_count=47,
            metadata={
                "submission_stats_complete": True,
                "private_internal_value": "not exposed",
            },
        )
        self.client.force_authenticate(self.user)

        with self.assertNumQueries(4):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["current_rating"], stats.current_rating)
        self.assertEqual(response.data["stats"]["rating_color"], "cyan")
        self.assertTrue(response.data["stats"]["submission_stats_complete"])
        self.assertEqual(
            [item["contest_id"] for item in response.data["rating_history"]],
            ["abc100", "abc350"],
        )
        self.assertNotIn("discipline", response.data["rating_history"][0])
        self.assertNotIn("metadata", response.data["rating_history"][0])
        self.assertEqual(len(response.data["recent_activity"]), 20)
        self.assertEqual(
            response.data["recent_activity"][0]["submission_id"],
            24,
        )
        self.assertTrue(response.data["recent_activity"][0]["accepted"])
        self.assertNotIn("provider_epoch_second", response.data["recent_activity"][0])
        self.assertEqual(
            [item["captured_at"] for item in response.data["snapshots"]],
            [
                older.captured_at.isoformat().replace("+00:00", "Z"),
                newer.captured_at.isoformat().replace("+00:00", "Z"),
            ],
        )
        self.assertIsNone(response.data["snapshots"][0]["solved_count"])
        self.assertFalse(
            response.data["snapshots"][0]["submission_stats_complete"]
        )
        self.assertTrue(
            response.data["snapshots"][1]["submission_stats_complete"]
        )
        self.assertNotIn("metadata", response.data["snapshots"][1])
        mocked_history.assert_not_called()
        mocked_submissions.assert_not_called()

    def test_partial_provider_states_return_cached_data_with_http_200(self):
        account = self._create_account()
        now = timezone.now()
        stats = AtCoderStats.objects.create(
            platform_account=account,
            current_rating=1500,
            rating_data_updated_at=now,
            solved_count=200,
            submission_data_updated_at=now - timedelta(days=1),
        )
        state = AtCoderSyncState.objects.create(
            platform_account=account,
            overall_status=AtCoderSyncState.OverallStatus.PARTIAL,
            rating_status=AtCoderSyncState.SourceStatus.SUCCESS,
            submission_status=AtCoderSyncState.SourceStatus.FAILED,
            submission_error_code="rate_limited",
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sync"]["status"], "partial")
        self.assertFalse(response.data["sync"]["rating"]["using_cached_data"])
        self.assertTrue(
            response.data["sync"]["submissions"]["using_cached_data"]
        )
        self.assertEqual(
            response.data["sync"]["submissions"]["error_code"],
            "rate_limited",
        )
        self.assertEqual(response.data["stats"]["solved_count"], 200)

        state.rating_status = AtCoderSyncState.SourceStatus.FAILED
        state.rating_error_code = "network_error"
        state.submission_status = AtCoderSyncState.SourceStatus.SUCCESS
        state.submission_error_code = ""
        state.save(
            update_fields=[
                "rating_status",
                "rating_error_code",
                "submission_status",
                "submission_error_code",
            ]
        )
        stats.submission_backfill_complete = True
        stats.save(update_fields=["submission_backfill_complete"])

        reverse_response = self.client.get(self.url)

        self.assertEqual(reverse_response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            reverse_response.data["sync"]["rating"]["using_cached_data"]
        )
        self.assertEqual(
            reverse_response.data["sync"]["rating"]["error_code"],
            "network_error",
        )
        self.assertEqual(
            reverse_response.data["sync"]["submissions"]["status"],
            "success",
        )

    def test_backfilling_and_blocked_states_keep_known_counts_usable(self):
        account = self._create_account()
        now = timezone.now()
        AtCoderStats.objects.create(
            platform_account=account,
            solved_count=220,
            attempted_count=300,
            indexed_submission_count=500,
            submission_data_updated_at=now,
            submission_backfill_complete=False,
        )
        sync_state = AtCoderSyncState.objects.create(
            platform_account=account,
            overall_status=AtCoderSyncState.OverallStatus.SUCCESS,
            rating_status=AtCoderSyncState.SourceStatus.DISABLED,
            submission_status=AtCoderSyncState.SourceStatus.SUCCESS,
        )
        progress = AtCoderSubmissionSyncState.objects.create(
            platform_account=account,
            progress_status=AtCoderSubmissionSyncState.ProgressStatus.BACKFILLING,
            backfill_complete=False,
            submission_data_updated_at=now,
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.data["stats"]["solved_count"], 220)
        self.assertFalse(response.data["stats"]["submission_stats_complete"])
        self.assertEqual(
            response.data["sync"]["submissions"]["progress"]["status"],
            "backfilling",
        )

        sync_state.overall_status = AtCoderSyncState.OverallStatus.PARTIAL
        sync_state.submission_status = AtCoderSyncState.SourceStatus.BLOCKED
        sync_state.submission_error_code = "saturated_timestamp_boundary"
        sync_state.save(
            update_fields=[
                "overall_status",
                "submission_status",
                "submission_error_code",
            ]
        )
        progress.progress_status = AtCoderSubmissionSyncState.ProgressStatus.BLOCKED
        progress.blocked_reason = "saturated_timestamp_boundary"
        progress.save(update_fields=["progress_status", "blocked_reason"])

        blocked_response = self.client.get(self.url)

        self.assertEqual(blocked_response.status_code, status.HTTP_200_OK)
        self.assertEqual(blocked_response.data["sync"]["status"], "partial")
        submission_sync = blocked_response.data["sync"]["submissions"]
        self.assertEqual(submission_sync["status"], "blocked")
        self.assertEqual(
            submission_sync["progress"]["error_code"],
            "saturated_timestamp_boundary",
        )
        self.assertEqual(
            blocked_response.data["stats"]["indexed_submission_count"],
            500,
        )

    def test_generic_platform_payload_excludes_heavy_rating_history(self):
        account = self._create_account()
        AtCoderStats.objects.create(platform_account=account, current_rating=1200)
        for index in range(5):
            self._create_rating_event(
                account,
                f"abc{index}",
                datetime(2024, 1, index + 1, tzinfo=datetime_timezone.utc),
                new_rating=1000 + index,
            )
        self.client.force_authenticate(self.user)

        with self.assertNumQueries(1):
            response = self.client.get(reverse("platform-account-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertNotIn("atcoder_rating_history", response.data[0])

    def test_snapshot_history_is_bounded_to_latest_180_in_chronological_order(self):
        account = self._create_account()
        start = datetime(2020, 1, 1, tzinfo=datetime_timezone.utc)
        PlatformStatsSnapshot.objects.bulk_create(
            [
                PlatformStatsSnapshot(
                    platform_account=account,
                    captured_at=start + timedelta(days=index),
                    rating=800 + index,
                    solved_count=index,
                    contest_count=index,
                    metadata={"submission_stats_complete": True},
                )
                for index in range(185)
            ]
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        snapshots = response.data["snapshots"]
        self.assertEqual(len(snapshots), 180)
        self.assertEqual(snapshots[0]["rating"], 805)
        self.assertEqual(snapshots[-1]["rating"], 984)

    def _create_account(self) -> PlatformAccount:
        return PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="atcoder_user",
        )

    @staticmethod
    def _create_rating_event(
        account: PlatformAccount,
        contest_id: str,
        occurred_at: datetime,
        *,
        new_rating: int,
        discipline: str = PlatformRatingEvent.Discipline.ALGORITHM,
    ) -> PlatformRatingEvent:
        return PlatformRatingEvent.objects.create(
            platform_account=account,
            discipline=discipline,
            external_contest_id=contest_id,
            contest_name=f"Contest {contest_id}",
            rank=100,
            performance=new_rating + 50,
            inner_performance=new_rating + 50,
            old_rating=new_rating - 100,
            new_rating=new_rating,
            rating_change=100,
            is_rated=True,
            occurred_at=occurred_at,
            metadata={"raw": "not exposed"},
        )

    @staticmethod
    def _create_submissions(account: PlatformAccount, count: int) -> None:
        base_time = datetime(2024, 1, 1, tzinfo=datetime_timezone.utc)
        AtCoderSubmission.objects.bulk_create(
            [
                AtCoderSubmission(
                    platform_account=account,
                    external_submission_id=index,
                    external_contest_id="abc350",
                    external_problem_id=f"abc350_{index}",
                    verdict="AC" if index % 2 == 0 else "WA",
                    language="C++ 23 (gcc 12.2)",
                    submitted_at=base_time + timedelta(seconds=index),
                    provider_epoch_second=index,
                    metadata={"point": 100.0},
                )
                for index in range(count)
            ]
        )
