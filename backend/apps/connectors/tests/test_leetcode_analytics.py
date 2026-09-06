from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import (
    LeetCodeStats,
    LeetCodeSyncState,
    PlatformAccount,
    PlatformStatsSnapshot,
)

User = get_user_model()


class LeetCodeAnalyticsTests(APITestCase):
    url = "/api/v1/competitive-programming/leetcode/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="leetcode-analytics",
            email="leetcode-analytics@example.com",
            password="StrongPassword123!",
        )

    def test_endpoint_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_no_account_returns_empty_database_only_contract(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["platform"], "leetcode")
        self.assertIsNone(response.data["account"])
        self.assertIsNone(response.data["stats"])
        self.assertEqual(response.data["rating_history"], [])
        self.assertEqual(response.data["recent_activity"], [])
        self.assertEqual(response.data["snapshots"], [])

    @patch(
        "apps.connectors.providers.leetcode.adapter."
        "LeetCodeAlfaAdapter.get_profile"
    )
    def test_returns_normalized_cached_analytics_without_provider_call(
        self,
        mocked_profile,
    ):
        account = self._create_account()
        updated_at = timezone.now()
        LeetCodeStats.objects.create(
            platform_account=account,
            display_name="Example User",
            solved_total=100,
            solved_easy=50,
            solved_medium=40,
            solved_hard=10,
            problem_stats_complete=True,
            current_contest_rating=1842.75,
            attended_contest_count=12,
            contest_global_ranking=12345,
            rating_history=[
                {
                    "contest_title": "Weekly Contest 401",
                    "occurred_at": "2026-02-01T00:00:00+00:00",
                    "rating": 1842.75,
                    "ranking": 400,
                    "problems_solved": 3,
                    "total_problems": 4,
                    "finish_time_seconds": 3500,
                },
                {"provider_field": "ignored"},
                {
                    "contest_title": "Weekly Contest 400",
                    "occurred_at": "2026-01-01T00:00:00+00:00",
                    "rating": 1725.5,
                    "ranking": None,
                    "problems_solved": None,
                    "total_problems": None,
                    "finish_time_seconds": None,
                },
            ],
            data_updated_at=updated_at,
        )
        LeetCodeSyncState.objects.create(
            platform_account=account,
            status=LeetCodeSyncState.Status.FAILED,
            last_attempted_at=updated_at,
            last_successful_at=updated_at,
            failure_reason="timeout",
        )
        PlatformStatsSnapshot.objects.create(
            platform_account=account,
            captured_at=datetime(
                2026,
                1,
                1,
                tzinfo=datetime_timezone.utc,
            ),
            rating=1725.5,
            solved_count=90,
            contest_count=11,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["solved_total"], 100)
        self.assertEqual(response.data["stats"]["solved_hard"], 10)
        self.assertEqual(response.data["sync"]["status"], "failed")
        self.assertEqual(response.data["sync"]["error_code"], "timeout")
        self.assertTrue(response.data["sync"]["using_cached_data"])
        history = response.data["rating_history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["platform"], "leetcode")
        self.assertIsNone(history[0]["old_rating"])
        self.assertIsNone(history[0]["rating_change"])
        self.assertEqual(history[1]["old_rating"], 1725.5)
        self.assertEqual(history[1]["new_rating"], 1842.75)
        self.assertEqual(history[1]["rating_change"], 117.25)
        self.assertEqual(response.data["snapshots"][0]["rating"], 1725.5)
        mocked_profile.assert_not_called()

    def test_connected_account_without_stats_handles_missing_data(self):
        self._create_account()
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["stats"])
        self.assertEqual(response.data["sync"]["status"], "never_synced")
        self.assertEqual(response.data["rating_history"], [])

    def test_empty_or_malformed_history_is_safe(self):
        account = self._create_account()
        stats = LeetCodeStats.objects.create(
            platform_account=account,
            rating_history=[],
        )
        LeetCodeStats.objects.filter(pk=stats.pk).update(
            rating_history={"unexpected": "shape"}
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating_history"], [])

    def test_handle_change_clears_cached_leetcode_analytics(self):
        account = self._create_account()
        LeetCodeStats.objects.create(
            platform_account=account,
            solved_total=100,
            problem_stats_complete=True,
        )
        LeetCodeSyncState.objects.create(
            platform_account=account,
            status=LeetCodeSyncState.Status.SUCCESS,
        )
        PlatformStatsSnapshot.objects.create(
            platform_account=account,
            solved_count=100,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            f"/api/v1/platform-accounts/{account.pk}/",
            {"handle": "new-leetcode-user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(LeetCodeStats.objects.exists())
        self.assertFalse(LeetCodeSyncState.objects.exists())
        self.assertFalse(PlatformStatsSnapshot.objects.exists())

    def _create_account(self) -> PlatformAccount:
        return PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="leetcode-user",
            profile_url="https://leetcode.com/u/leetcode-user/",
        )
