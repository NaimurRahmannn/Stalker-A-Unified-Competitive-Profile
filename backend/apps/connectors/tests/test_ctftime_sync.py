import json
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.connectors.models import (
    CTFTeamProfile,
    CTFtimeSyncState,
    CTFYearlyRanking,
    PlatformAccount,
)
from apps.connectors.providers.ctftime.exceptions import (
    CTFtimeProviderRateLimitError,
    CTFtimeTeamNotFoundError,
)
from apps.connectors.providers.ctftime.persistence import CTFtimePersistenceMapper


@override_settings(CTFTIME_SYNC_ENABLED=True, CTFTIME_SYNC_COOLDOWN_SECONDS=60)
class CTFtimeAccountSyncTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ctfuser", email="ctf@example.com", password="password"
        )
        self.client.force_authenticate(self.user)
        self.account = PlatformAccount.objects.create(
            user=self.user, platform=PlatformAccount.Platform.CTFTIME, handle="1005"
        )
        fixture_path = (
            Path(__file__).parents[1]
            / "providers"
            / "ctftime"
            / "tests"
            / "fixtures"
            / "team_profile.json"
        )
        self.payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.sync_url = reverse("platform-account-sync", args=[self.account.pk])
        self.detail_url = reverse("platform-account-detail", args=[self.account.pk])

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_sync_fetches_once_and_exposes_profile_rankings_and_state(self, get_team_info):
        self.payload["rating"]["2025"]["organizer_points"] = 7.5
        get_team_info.return_value = self.payload

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        get_team_info.assert_called_once_with("1005")
        self.assertEqual(response.data["profile_url"], "https://ctftime.org/team/1005")
        self.assertTrue(response.data["is_verified"])
        self.assertIsNotNone(response.data["last_synced_at"])
        self.assertEqual(response.data["ctftime_sync_state"]["status"], "success")
        self.assertEqual(response.data["ctf_team_profile"]["name"], self.payload["name"])
        self.assertEqual(len(response.data["ctf_team_profile"]["yearly_rankings"]), 3)
        self.assertEqual(
            response.data["ctf_team_profile"]["yearly_rankings"][0]["organizer_points"],
            7.5,
        )
        self.assertFalse(response.data["can_sync"])
        self.assertGreater(response.data["sync_cooldown_seconds"], 0)
        self.assertEqual(CTFYearlyRanking.objects.count(), 3)

        detail = self.client.get(self.detail_url)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["ctf_team_profile"]["external_team_id"], "1005")
        self.assertEqual(
            CTFYearlyRanking.objects.get(team_profile__platform_account=self.account, year=2025)
            .organizer_points,
            7.5,
        )

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_cooldown_rejects_second_request_without_fetching(self, get_team_info):
        get_team_info.return_value = self.payload
        self.assertEqual(self.client.post(self.sync_url).status_code, status.HTTP_200_OK)

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertGreater(response.data["retry_after_seconds"], 0)
        get_team_info.assert_called_once()

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_missing_team_records_failure_and_returns_400(self, get_team_info):
        get_team_info.side_effect = CTFtimeTeamNotFoundError("Team 1005 not found")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        state = CTFtimeSyncState.objects.get(platform_account=self.account)
        self.assertEqual(state.status, CTFtimeSyncState.Status.FAILED)
        self.assertEqual(state.failure_reason, "invalid_team_id")
        self.assertEqual(state.consecutive_failure_count, 1)
        self.assertIsNotNone(state.last_attempted_at)
        self.assertFalse(CTFTeamProfile.objects.filter(platform_account=self.account).exists())

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_provider_rate_limit_records_failure_and_returns_429(self, get_team_info):
        get_team_info.side_effect = CTFtimeProviderRateLimitError("Rate limited")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        state = CTFtimeSyncState.objects.get(platform_account=self.account)
        self.assertEqual(state.failure_reason, "rate_limited")

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_invalid_response_keeps_profile_empty(self, get_team_info):
        get_team_info.return_value = {**self.payload, "id": 1234}

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            CTFtimeSyncState.objects.get(platform_account=self.account).failure_reason,
            "invalid_response",
        )
        self.assertFalse(CTFTeamProfile.objects.filter(platform_account=self.account).exists())

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_stale_running_state_can_recover(self, get_team_info):
        get_team_info.return_value = self.payload
        CTFtimeSyncState.objects.create(
            platform_account=self.account,
            status=CTFtimeSyncState.Status.RUNNING,
            last_attempted_at=timezone.now() - timedelta(minutes=10),
        )

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ctftime_sync_state"]["status"], "success")

    @override_settings(CTFTIME_SYNC_ENABLED=False)
    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_disabled_sync_returns_503_without_fetch(self, get_team_info):
        self.assertFalse(self.client.get(self.detail_url).data["can_sync"])

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        get_team_info.assert_not_called()

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_handle_edit_clears_ctftime_data(self, get_team_info):
        get_team_info.return_value = self.payload
        self.assertEqual(self.client.post(self.sync_url).status_code, status.HTTP_200_OK)

        response = self.client.patch(self.detail_url, {"handle": "1234"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data["ctf_team_profile"])
        self.assertIsNone(response.data["ctftime_sync_state"])
        self.assertTrue(response.data["can_sync"])
        self.assertFalse(CTFTeamProfile.objects.filter(platform_account=self.account).exists())
        self.assertFalse(CTFtimeSyncState.objects.filter(platform_account=self.account).exists())
        self.assertFalse(CTFYearlyRanking.objects.exists())

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_platform_edit_clears_ctftime_data(self, get_team_info):
        get_team_info.return_value = self.payload
        self.assertEqual(self.client.post(self.sync_url).status_code, status.HTTP_200_OK)

        response = self.client.patch(
            self.detail_url,
            {"platform": "codeforces", "handle": "tourist"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CTFTeamProfile.objects.filter(platform_account=self.account).exists())
        self.assertFalse(CTFtimeSyncState.objects.filter(platform_account=self.account).exists())

    @patch("apps.connectors.providers.ctftime.client.CTFtimeClient.get_team_info")
    def test_database_error_rolls_back_profile_and_marks_failure(self, get_team_info):
        get_team_info.return_value = self.payload
        original = CTFtimePersistenceMapper.persist_sync_data

        def fail_after_persist(account, data):
            original(account, data)
            raise RuntimeError("database write failed")

        with patch(
            "apps.connectors.providers.ctftime.sync_service."
            "CTFtimePersistenceMapper.persist_sync_data",
            side_effect=fail_after_persist,
        ), patch("apps.connectors.providers.ctftime.sync_service.logger"):
            response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(CTFTeamProfile.objects.filter(platform_account=self.account).exists())
        self.assertFalse(CTFYearlyRanking.objects.exists())
        self.assertEqual(
            CTFtimeSyncState.objects.get(platform_account=self.account).failure_reason,
            "sync_error",
        )
        self.account.refresh_from_db()
        self.assertIsNone(self.account.last_synced_at)

    def test_non_numeric_team_id_is_rejected_on_create_and_edit(self):
        edit_response = self.client.patch(
            self.detail_url, {"handle": "not-an-id"}, format="json"
        )
        self.account.delete()
        create_response = self.client.post(
            reverse("platform-account-list"),
            {"platform": "ctftime", "handle": "not-an-id"},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(edit_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("handle", create_response.data)
        self.assertIn("handle", edit_response.data)
