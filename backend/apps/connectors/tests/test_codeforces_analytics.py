from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import CodeforcesStats, PlatformAccount, PlatformStatsSnapshot


User = get_user_model()


class CodeforcesAnalyticsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="analytics-user",
            email="analytics@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other-analytics-user",
            email="other-analytics@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse("codeforces-analytics")

    def test_endpoint_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_returns_empty_state_without_connected_account(self):
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["account"])
        self.assertIsNone(response.data["stats"])
        self.assertEqual(response.data["rating_history"], [])
        self.assertEqual(response.data["recent_activity"], [])
        self.assertEqual(response.data["snapshots"], [])

    def test_endpoint_returns_connected_unsynced_account(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["account"]["id"], account.id)
        self.assertIsNone(response.data["stats"])
        self.assertTrue(response.data["account"]["can_sync"])

    def test_endpoint_returns_normalized_owned_analytics(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
            is_verified=True,
            last_synced_at=timezone.now(),
        )
        stats = CodeforcesStats.objects.create(
            platform_account=account,
            handle="tourist",
            rating=3900,
            max_rating=4000,
            solved_count=2000,
            attempted_count=2500,
            accepted_submission_count=3000,
            contest_count=2,
            raw_user_info={"private": "not exposed"},
            raw_rating_history=[
                {
                    "contestId": 2,
                    "contestName": "Round 2",
                    "rank": 10,
                    "oldRating": 3800,
                    "newRating": 3900,
                    "ratingUpdateTimeSeconds": 200,
                },
                {
                    "contestId": 1,
                    "contestName": "Round 1",
                    "rank": 20,
                    "oldRating": 3700,
                    "newRating": 3800,
                    "ratingUpdateTimeSeconds": 100,
                },
            ],
            recent_activity=[
                {
                    "submission_id": 3,
                    "contest_id": None,
                    "problem_index": None,
                    "problem_name": "Optional fields",
                    "problem_rating": None,
                    "verdict": "OK",
                    "language": None,
                    "submitted_at": "2026-01-01T00:00:00Z",
                },
                {"malformed": True},
            ],
        )
        PlatformStatsSnapshot.objects.create(
            platform_account=account,
            rating=3900,
            solved_count=2000,
            contest_count=2,
        )
        other_account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="other",
        )
        PlatformStatsSnapshot.objects.create(platform_account=other_account, rating=1000)
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["rating"], stats.rating)
        self.assertEqual(
            [item["contest_id"] for item in response.data["rating_history"]],
            [1, 2],
        )
        self.assertEqual(response.data["rating_history"][1]["rating_change"], 100)
        self.assertEqual(len(response.data["recent_activity"]), 1)
        self.assertEqual(response.data["recent_activity"][0]["problem_rating"], None)
        self.assertEqual(len(response.data["snapshots"]), 1)
        self.assertNotIn("raw_user_info", response.data["stats"])
        self.assertNotIn("raw_rating_history", response.data["stats"])

    def test_empty_history_and_activity_are_safe(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="new-user",
        )
        CodeforcesStats.objects.create(
            platform_account=account,
            handle="new-user",
            raw_rating_history={},
            recent_activity={},
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating_history"], [])
        self.assertEqual(response.data["recent_activity"], [])
