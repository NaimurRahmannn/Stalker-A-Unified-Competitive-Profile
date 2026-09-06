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


class PublicProfileEndpointTests(APITestCase):
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
        self.url = f"/api/v1/profile/{self.user.username}/"

    def test_public_profile_does_not_require_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unknown_username_returns_404(self):
        response = self.client.get("/api/v1/profile/missing-user/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_profile_returns_public_user_fields_without_email(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["user"],
            {
                "id": self.user.id,
                "username": "niamur",
                "full_name": "Niamur Rahman",
                "avatar": None,
                "bio": "Competitive programmer",
                "country": "Bangladesh",
                "institution": "My University",
                "github_url": "https://github.com/example",
                "linkedin_url": "https://linkedin.com/in/example",
            },
        )
        self.assertNotIn("email", response.data["user"])

    def test_public_profile_includes_only_requested_users_platforms(self):
        own_account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="my_leetcode_handle",
        )
        PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["platforms"]), 1)
        self.assertEqual(response.data["platforms"][0]["id"], own_account.id)
        self.assertEqual(response.data["platforms"][0]["handle"], "my_leetcode_handle")

    def test_non_codeforces_platform_stats_are_null(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="my_leetcode_handle",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["platforms"][0]["platform"], "leetcode")
        self.assertIsNone(response.data["platforms"][0]["stats"])

    def test_missing_codeforces_stats_are_null(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["platforms"][0]["stats"])

    def test_public_profile_includes_synced_codeforces_stats(self):
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

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        platform = response.data["platforms"][0]
        self.assertEqual(platform["platform"], "codeforces")
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
        self.assertNotIn("raw_user_info", platform["stats"])
        self.assertNotIn("raw_rating_history", platform["stats"])

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_public_profile_endpoint_does_not_call_external_apis(self, mocked_profile):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_profile.assert_not_called()

    def test_public_profile_includes_atcoder_without_sync_internals(self):
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

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        platform = response.data["platforms"][0]
        self.assertEqual(platform["stats"]["current_rating"], 1542)
        self.assertEqual(platform["stats"]["rating_color"], "cyan")
        self.assertFalse(platform["stats"]["submission_stats_complete"])
        self.assertNotIn("atcoder_sync_state", platform)
        summary = response.data["competitive_programming"]["summary"]
        self.assertEqual(summary["solved_count"], 428)
        self.assertFalse(summary["solved_count_complete"])

    def test_public_profile_includes_leetcode_stats_and_unified_totals(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="leetcode-user",
        )
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
            data_updated_at=timezone.now(),
            rating_history=[{"internal": "not exposed here"}],
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = response.data["platforms"][0]["stats"]
        self.assertEqual(stats["display_name"], "Example User")
        self.assertEqual(stats["solved_total"], 100)
        self.assertEqual(stats["current_contest_rating"], 1842.75)
        self.assertNotIn("rating_history", stats)
        summary = response.data["competitive_programming"]["summary"]
        self.assertEqual(summary["active_platforms"], 1)
        self.assertEqual(summary["solved_count"], 100)
        self.assertTrue(summary["solved_count_complete"])
