from datetime import datetime
from datetime import timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import (
    AtCoderStats,
    CodeforcesStats,
    LeetCodeStats,
    PlatformAccount,
)

User = get_user_model()


class DashboardMeEndpointTests(APITestCase):
    url = "/api/v1/dashboard/me/"

    def setUp(self):
        self.user = User.objects.create_user(
            username="niamur",
            email="niamur@example.com",
            password="StrongPassword123!",
            full_name="Niamur Rahman",
        )
        self.user.bio = "Competitive programmer"
        self.user.country = "Bangladesh"
        self.user.institution = "My University"
        self.user.github_url = "https://github.com/example"
        self.user.linkedin_url = "https://linkedin.com/in/example"
        self.user.save()

        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_user_cannot_access_dashboard(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_with_no_platform_accounts_gets_empty_platforms_list(self):
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["user"],
            {
                "id": self.user.id,
                "username": "niamur",
                "email": "niamur@example.com",
                "full_name": "Niamur Rahman",
                "avatar": "",
                "bio": "Competitive programmer",
                "country": "Bangladesh",
                "institution": "My University",
                "github_url": "https://github.com/example",
                "linkedin_url": "https://linkedin.com/in/example",
            },
        )
        self.assertEqual(response.data["platforms"], [])

    def test_authenticated_user_with_unverified_platform_accounts_gets_stats_null(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["platforms"]), 1)
        platform = response.data["platforms"][0]
        self.assertEqual(platform["platform"], "codeforces")
        self.assertEqual(platform["handle"], "tourist")
        self.assertFalse(platform["is_verified"])
        self.assertIsNone(platform["last_synced_at"])
        self.assertIsNone(platform["stats"])

    def test_authenticated_user_with_synced_codeforces_account_gets_codeforces_stats(self):
        synced_at = timezone.now()
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
            is_verified=True,
            last_synced_at=synced_at,
        )
        stats = CodeforcesStats.objects.create(
            platform_account=account,
            handle="tourist",
            rating=3900,
            max_rating=3900,
            rank="legendary grandmaster",
            max_rank="legendary grandmaster",
            solved_count=2000,
            attempted_count=2500,
            accepted_submission_count=3000,
            contest_count=100,
            last_online_at=synced_at,
            registered_at=datetime(2012, 1, 1, tzinfo=datetime_timezone.utc),
            raw_user_info={"handle": "tourist"},
            raw_rating_history=[{"contestId": 1}],
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        platform = response.data["platforms"][0]
        self.assertEqual(platform["platform"], "codeforces")
        self.assertTrue(platform["is_verified"])
        self.assertEqual(
            platform["stats"],
            {
                "rating": 3900,
                "max_rating": 3900,
                "rank": "legendary grandmaster",
                "max_rank": "legendary grandmaster",
                "solved_count": 2000,
                "attempted_count": 2500,
                "accepted_submission_count": 3000,
                "contest_count": 100,
                "last_online_at": stats.last_online_at.isoformat().replace("+00:00", "Z"),
                "registered_at": stats.registered_at.isoformat().replace("+00:00", "Z"),
                "updated_at": stats.updated_at.isoformat().replace("+00:00", "Z"),
            },
        )

    def test_dashboard_only_returns_current_users_platform_accounts(self):
        own_account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="other_leetcode",
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["platforms"]), 1)
        self.assertEqual(response.data["platforms"][0]["id"], own_account.id)

    def test_dashboard_does_not_expose_another_users_platform_accounts_or_stats(self):
        own_account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="my_leetcode_handle",
        )
        other_account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
            is_verified=True,
            last_synced_at=timezone.now(),
        )
        CodeforcesStats.objects.create(
            platform_account=other_account,
            handle="tourist",
            rating=3900,
            raw_user_info={"secret": "other-user-data"},
            raw_rating_history=[{"contestId": 1}],
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["platforms"]), 1)
        self.assertEqual(response.data["platforms"][0]["id"], own_account.id)
        self.assertEqual(response.data["platforms"][0]["handle"], "my_leetcode_handle")
        self.assertIsNone(response.data["platforms"][0]["stats"])

    def test_stats_is_null_for_platforms_without_implemented_stats(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="my_leetcode_handle",
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["platforms"][0]["platform"], "leetcode")
        self.assertIsNone(response.data["platforms"][0]["stats"])

    def test_codeforces_stats_does_not_expose_raw_fields(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
            is_verified=True,
        )
        CodeforcesStats.objects.create(
            platform_account=account,
            handle="tourist",
            rating=3900,
            raw_user_info={"handle": "tourist"},
            raw_rating_history=[{"contestId": 1}],
        )
        self.authenticate()

        response = self.client.get(self.url)

        stats = response.data["platforms"][0]["stats"]
        self.assertNotIn("raw_user_info", stats)
        self.assertNotIn("raw_rating_history", stats)

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_dashboard_endpoint_does_not_call_external_apis(self, mocked_profile):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_profile.assert_not_called()

    def test_dashboard_includes_atcoder_and_completeness_aware_summary(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="atcoder-user",
        )
        AtCoderStats.objects.create(
            platform_account=account,
            current_rating=1542,
            max_rating=1681,
            rated_contest_count=47,
            solved_count=428,
            attempted_count=501,
            accepted_submission_count=683,
            indexed_submission_count=900,
            submission_backfill_complete=False,
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data["platforms"][0]["stats"]
        self.assertEqual(stats["current_rating"], 1542)
        self.assertEqual(stats["rating_color"], "cyan")
        self.assertFalse(stats["submission_stats_complete"])
        summary = response.data["competitive_programming"]["summary"]
        self.assertEqual(summary["solved_count"], 428)
        self.assertFalse(summary["solved_count_complete"])

    def test_dashboard_includes_leetcode_stats_without_history_payload(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="leetcode-user",
        )
        LeetCodeStats.objects.create(
            platform_account=account,
            solved_total=75,
            solved_easy=35,
            solved_medium=30,
            solved_hard=10,
            problem_stats_complete=True,
            current_contest_rating=1600.5,
            attended_contest_count=8,
            data_updated_at=timezone.now(),
            rating_history=[{"internal": "not exposed here"}],
        )
        self.authenticate()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data["platforms"][0]["stats"]
        self.assertEqual(stats["solved_total"], 75)
        self.assertEqual(stats["current_contest_rating"], 1600.5)
        self.assertNotIn("rating_history", stats)
        summary = response.data["competitive_programming"]["summary"]
        self.assertEqual(summary["solved_count"], 75)
        self.assertTrue(summary["solved_count_complete"])
