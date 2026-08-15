from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.base.exceptions import ProviderRateLimitError
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    PlatformAccount,
)


User = get_user_model()


def raw_submission(submission_id=1, epoch_second=100, result="AC"):
    return {
        "id": submission_id,
        "epoch_second": epoch_second,
        "problem_id": "abc100_a",
        "contest_id": "abc100",
        "user_id": "atcoder_user",
        "language": "C++ 20 (gcc 12.2)",
        "point": 100.0,
        "length": 200,
        "result": result,
        "execution_time": 10,
    }


class AtCoderSubmissionAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="StrongPassword123!",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="StrongPassword123!",
        )
        self.account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="atcoder_user",
        )
        self.client.force_authenticate(user=self.user)
        self.overview_url = reverse(
            "platform-account-atcoder-submissions",
            args=[self.account.pk],
        )
        self.sync_url = reverse(
            "platform-account-sync-submissions",
            args=[self.account.pk],
        )

    @patch(
        "apps.connectors.providers.atcoder.problems_client.AtCoderProblemsClient.get_user_submissions"
    )
    def test_user_can_sync_owned_atcoder_submissions(self, mocked_get):
        mocked_get.return_value = [raw_submission()]

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["solved_count"], 1)
        self.assertEqual(response.data["stats"]["attempted_count"], 1)
        self.assertEqual(response.data["stats"]["accepted_submission_count"], 1)
        self.assertEqual(response.data["stats"]["indexed_submission_count"], 1)
        self.assertTrue(response.data["stats"]["submission_backfill_complete"])
        self.assertEqual(len(response.data["recent_submissions"]), 1)
        self.assertEqual(response.data["sync"]["pages_fetched"], 1)
        self.account.refresh_from_db()
        self.assertIsNone(self.account.ownership_verified_at)
        self.assertIsNone(self.account.handle_validated_at)

    def test_user_cannot_read_or_sync_another_users_account(self):
        other_account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="other_user",
        )

        read_response = self.client.get(
            reverse("platform-account-atcoder-submissions", args=[other_account.pk])
        )
        sync_response = self.client.post(
            reverse("platform-account-sync-submissions", args=[other_account.pk])
        )

        self.assertEqual(read_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(sync_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_atcoder_account_is_rejected(self):
        self.account.platform = PlatformAccount.Platform.CODEFORCES
        self.account.save(update_fields=["platform"])

        self.assertEqual(
            self.client.get(self.overview_url).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.client.post(self.sync_url).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @override_settings(ATCODER_PROBLEMS_SYNC_ENABLED=False)
    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_kill_switch_returns_controlled_error_without_request(self, mocked_get):
        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        mocked_get.assert_not_called()
        self.assertFalse(AtCoderSubmissionSyncState.objects.exists())

    @patch(
        "apps.connectors.providers.atcoder.problems_client.AtCoderProblemsClient.get_user_submissions"
    )
    def test_provider_rate_limit_maps_to_429_without_mutation(self, mocked_get):
        mocked_get.side_effect = ProviderRateLimitError("rate limited")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(AtCoderSubmission.objects.exists())
        self.assertFalse(AtCoderSubmissionSyncState.objects.exists())

    @patch(
        "apps.connectors.providers.atcoder.problems_client.AtCoderProblemsClient.get_user_submissions"
    )
    def test_cached_overview_is_bounded_and_never_calls_provider(self, mocked_get):
        AtCoderStats.objects.create(
            platform_account=self.account,
            solved_count=25,
            attempted_count=30,
            accepted_submission_count=40,
            indexed_submission_count=45,
            submission_backfill_complete=True,
            submission_data_updated_at=timezone.now(),
        )
        AtCoderSubmissionSyncState.objects.create(
            platform_account=self.account,
            last_submission_epoch=124,
            last_submission_id=24,
            backfill_complete=True,
            submission_data_updated_at=timezone.now(),
        )
        AtCoderSubmission.objects.bulk_create(
            [
                AtCoderSubmission(
                    platform_account=self.account,
                    external_submission_id=index,
                    external_contest_id="abc100",
                    external_problem_id=f"abc100_{index}",
                    verdict="AC",
                    submitted_at=datetime.fromtimestamp(
                        100 + index,
                        tz=datetime_timezone.utc,
                    ),
                    provider_epoch_second=100 + index,
                )
                for index in range(25)
            ]
        )

        response = self.client.get(self.overview_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["recent_submissions"]), 20)
        self.assertEqual(
            response.data["recent_submissions"][0]["external_submission_id"],
            24,
        )
        mocked_get.assert_not_called()

    def test_standard_account_list_does_not_include_submission_history(self):
        AtCoderStats.objects.create(
            platform_account=self.account,
            indexed_submission_count=1,
            submission_backfill_complete=False,
        )

        response = self.client.get(reverse("platform-account-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["atcoder_stats"]["indexed_submission_count"], 1)
        self.assertNotIn("recent_submissions", response.data[0])

    @patch(
        "apps.connectors.providers.atcoder.problems_client.AtCoderProblemsClient.get_user_submissions"
    )
    def test_dashboard_and_public_profile_never_call_atcoder_problems(
        self,
        mocked_get,
    ):
        dashboard_response = self.client.get("/api/v1/dashboard/me/")
        self.client.force_authenticate(user=None)
        profile_response = self.client.get(f"/api/v1/profile/{self.user.username}/")

        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        mocked_get.assert_not_called()

    def test_handle_change_deletes_stale_submission_cache_and_state(self):
        AtCoderStats.objects.create(
            platform_account=self.account,
            indexed_submission_count=1,
        )
        AtCoderSubmissionSyncState.objects.create(
            platform_account=self.account,
            last_submission_epoch=100,
            last_submission_id=1,
        )
        AtCoderSubmission.objects.create(
            platform_account=self.account,
            external_submission_id=1,
            external_contest_id="abc100",
            external_problem_id="abc100_a",
            verdict="AC",
            submitted_at=datetime.fromtimestamp(100, tz=datetime_timezone.utc),
            provider_epoch_second=100,
        )

        response = self.client.patch(
            reverse("platform-account-detail", args=[self.account.pk]),
            {"handle": "new_atcoder_user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["atcoder_stats"])
        self.assertFalse(AtCoderStats.objects.exists())
        self.assertFalse(AtCoderSubmissionSyncState.objects.exists())
        self.assertFalse(AtCoderSubmission.objects.exists())
