from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
)
from apps.connectors.models import CodeforcesStats, PlatformAccount
from apps.connectors.providers.codeforces.mapper import calculate_solved_stats


User = get_user_model()


class PlatformAccountAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="niamur",
            email="niamur@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.list_url = reverse("platform-account-list")

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_authenticated_user_can_create_platform_account(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["platform"], "codeforces")
        self.assertEqual(response.data["handle"], "niamur")
        self.assertEqual(response.data["profile_url"], "")
        self.assertFalse(response.data["is_verified"])
        self.assertIsNone(response.data["last_synced_at"])
        self.assertEqual(PlatformAccount.objects.get().user, self.user)

    def test_unauthenticated_user_cannot_create_platform_account(self):
        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(PlatformAccount.objects.count(), 0)

    def test_authenticated_user_can_list_only_their_own_platform_accounts(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["handle"], "niamur")

    def test_user_cannot_access_another_users_platform_account(self):
        account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.get(reverse("platform-account-detail", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_add_same_platform_twice(self):
        PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "another_handle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("platform", response.data)
        self.assertEqual(PlatformAccount.objects.filter(user=self.user).count(), 1)

    def test_user_can_update_their_handle(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.patch(
            reverse("platform-account-detail", args=[account.pk]),
            {"handle": "new_handle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["handle"], "new_handle")
        account.refresh_from_db()
        self.assertEqual(account.handle, "new_handle")

    def test_user_can_delete_their_platform_account(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.delete(reverse("platform-account-detail", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PlatformAccount.objects.filter(pk=account.pk).exists())

    def test_invalid_platform_returns_400(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "invalid", "handle": "niamur"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("platform", response.data)

    def test_empty_handle_returns_400(self):
        self.authenticate()

        response = self.client.post(
            self.list_url,
            {"platform": "codeforces", "handle": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("handle", response.data)

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_authenticated_user_can_sync_their_own_codeforces_account(self, mocked_profile):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="Tourist",
        )
        last_online_at = timezone.now()
        registered_at = timezone.now()
        mocked_profile.return_value = {
            "handle": "tourist",
            "rating": 3900,
            "max_rating": 3900,
            "rank": "legendary grandmaster",
            "max_rank": "legendary grandmaster",
            "solved_count": 2000,
            "attempted_count": 2500,
            "accepted_submission_count": 3000,
            "contest_count": 100,
            "last_online_at": last_online_at,
            "registered_at": registered_at,
            "raw_user_info": {"handle": "tourist"},
            "raw_rating_history": [{"contestId": 1}],
        }
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["handle"], "tourist")
        self.assertTrue(response.data["is_verified"])
        self.assertIsNotNone(response.data["last_synced_at"])
        self.assertIn("codeforces_stats", response.data)
        self.assertEqual(response.data["codeforces_stats"]["handle"], "tourist")
        self.assertEqual(response.data["codeforces_stats"]["rating"], 3900)

        account.refresh_from_db()
        self.assertTrue(account.is_verified)
        self.assertIsNotNone(account.last_synced_at)
        self.assertEqual(account.handle, "tourist")
        self.assertTrue(CodeforcesStats.objects.filter(platform_account=account).exists())

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_sync_updates_existing_codeforces_stats(self, mocked_profile):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        CodeforcesStats.objects.create(
            platform_account=account,
            handle="tourist",
            rating=3800,
            solved_count=10,
        )
        mocked_profile.return_value = {
            "handle": "tourist",
            "rating": 3900,
            "max_rating": 3900,
            "rank": "legendary grandmaster",
            "max_rank": "legendary grandmaster",
            "solved_count": 2000,
            "attempted_count": 2500,
            "accepted_submission_count": 3000,
            "contest_count": 100,
            "last_online_at": timezone.now(),
            "registered_at": timezone.now(),
            "raw_user_info": {"handle": "tourist"},
            "raw_rating_history": [{"contestId": 1}],
        }
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CodeforcesStats.objects.count(), 1)
        stats = CodeforcesStats.objects.get(platform_account=account)
        self.assertEqual(stats.rating, 3900)
        self.assertEqual(stats.solved_count, 2000)

    def test_sync_fails_if_platform_is_not_codeforces(self):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="niamur",
        )
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Sync is currently only available for Codeforces.")

    def test_sync_fails_if_user_tries_to_sync_another_users_account(self):
        account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_sync_handles_invalid_codeforces_handle_with_400(self, mocked_profile):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="invalid_handle",
        )
        mocked_profile.side_effect = InvalidExternalAccountError("Codeforces handle was not found.")
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Codeforces handle was not found.")

    @patch("apps.connectors.providers.codeforces.connector.CodeforcesConnector.fetch_normalized_profile")
    def test_sync_handles_codeforces_network_failure_with_503(self, mocked_profile):
        account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.CODEFORCES,
            handle="tourist",
        )
        mocked_profile.side_effect = ExternalServiceError("Codeforces API is currently unavailable.")
        self.authenticate()

        response = self.client.post(reverse("platform-account-sync", args=[account.pk]))

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["detail"], "Codeforces API is currently unavailable.")


class CodeforcesStatsCalculationTests(SimpleTestCase):
    def test_calculate_solved_stats_counts_unique_problems_and_accepted_submissions(self):
        submissions = [
            {
                "problem": {"contestId": 1, "index": "A", "name": "Problem A"},
                "verdict": "OK",
            },
            {
                "problem": {"contestId": 1, "index": "A", "name": "Problem A"},
                "verdict": "OK",
            },
            {
                "problem": {"contestId": 1, "index": "B", "name": "Problem B"},
                "verdict": "WRONG_ANSWER",
            },
            {
                "problem": {"contestId": 1, "index": "C", "name": "Problem C"},
                "verdict": "OK",
            },
        ]

        stats = calculate_solved_stats(submissions)

        self.assertEqual(stats["solved_count"], 2)
        self.assertEqual(stats["attempted_count"], 3)
        self.assertEqual(stats["accepted_submission_count"], 3)
