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
    AtCoderSyncState,
    PlatformAccount,
    PlatformRatingEvent,
    PlatformStatsSnapshot,
)

User = get_user_model()


def normalized_event(
    contest_id: str,
    occurred_at: datetime,
    *,
    is_rated: bool = True,
    old_rating: int | None = 1000,
    new_rating: int | None = 1100,
    performance: int | None = 1200,
) -> dict:
    return {
        "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
        "external_contest_id": contest_id,
        "contest_name": f"Contest {contest_id}",
        "rank": 100,
        "performance": performance,
        "inner_performance": performance,
        "old_rating": old_rating,
        "new_rating": new_rating,
        "rating_change": (
            new_rating - old_rating
            if new_rating is not None and old_rating is not None
            else None
        ),
        "is_rated": is_rated,
        "occurred_at": occurred_at,
        "metadata": {"contest_screen_name": f"{contest_id}.contest.atcoder.jp"},
    }


def normalized_profile(events: list[dict]) -> dict:
    rated = [event for event in events if event["is_rated"]]
    latest = rated[-1] if rated else None
    return {
        "handle": "atcoder_user",
        "profile_url": "https://atcoder.jp/users/atcoder_user",
        "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
        "rating_events": events,
        "current_rating": latest["new_rating"] if latest else None,
        "max_rating": max((event["new_rating"] for event in rated), default=None),
        "rated_contest_count": len(rated),
        "last_rated_at": latest["occurred_at"] if latest else None,
        "last_performance": latest["performance"] if latest else None,
    }


@override_settings(ATCODER_PROBLEMS_SYNC_ENABLED=False)
class AtCoderSynchronizationTests(APITestCase):
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
        self.sync_url = reverse("platform-account-sync", args=[self.account.pk])
        self.first_event = normalized_event(
            "abc100",
            datetime(2024, 1, 1, tzinfo=datetime_timezone.utc),
            old_rating=1000,
            new_rating=1200,
            performance=1300,
        )
        self.second_event = normalized_event(
            "abc200",
            datetime(2024, 2, 1, tzinfo=datetime_timezone.utc),
            old_rating=1200,
            new_rating=1150,
            performance=1100,
        )

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_first_sync_persists_stats_events_snapshot_and_validation(self, mocked_fetch):
        mocked_fetch.return_value = normalized_profile(
            [self.first_event, self.second_event]
        )

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_verified)
        self.assertIsNotNone(self.account.handle_validated_at)
        self.assertIsNone(self.account.ownership_verified_at)
        self.assertTrue(response.data["handle_validated"])
        self.assertFalse(response.data["ownership_verified"])
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1150)
        self.assertEqual(stats.max_rating, 1200)
        self.assertEqual(stats.rated_contest_count, 2)
        self.assertEqual(stats.last_performance, 1100)
        self.assertEqual(PlatformRatingEvent.objects.count(), 2)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)
        self.assertEqual(response.data["atcoder_stats"]["rating_color"], "green")
        self.assertEqual(len(response.data["atcoder_rating_history"]), 2)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_repeated_identical_sync_is_idempotent(self, mocked_fetch):
        mocked_fetch.return_value = normalized_profile(
            [self.first_event, self.second_event]
        )
        self.assertEqual(self.client.post(self.sync_url).status_code, status.HTTP_200_OK)
        self._expire_cooldown()

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PlatformRatingEvent.objects.count(), 2)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_rating_sync_preserves_independent_submission_metrics(self, mocked_fetch):
        AtCoderStats.objects.create(
            platform_account=self.account,
            solved_count=428,
            attempted_count=501,
            accepted_submission_count=683,
            indexed_submission_count=941,
            submission_backfill_complete=True,
            submission_data_updated_at=timezone.now(),
        )
        mocked_fetch.return_value = normalized_profile([self.first_event])

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1200)
        self.assertEqual(stats.solved_count, 428)
        self.assertEqual(stats.attempted_count, 501)
        self.assertEqual(stats.accepted_submission_count, 683)
        self.assertEqual(stats.indexed_submission_count, 941)
        snapshot = PlatformStatsSnapshot.objects.get(platform_account=self.account)
        self.assertEqual(snapshot.solved_count, 428)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_new_contest_adds_only_one_event_and_updates_derived_stats(self, mocked_fetch):
        mocked_fetch.side_effect = [
            normalized_profile([self.first_event]),
            normalized_profile([self.first_event, self.second_event]),
        ]
        self.client.post(self.sync_url)
        self._expire_cooldown()

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PlatformRatingEvent.objects.count(), 2)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1150)
        self.assertEqual(stats.max_rating, 1200)
        self.assertEqual(stats.rated_contest_count, 2)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 2)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_unrated_event_does_not_change_rated_derived_stats(self, mocked_fetch):
        unrated = normalized_event(
            "practice",
            datetime(2024, 3, 1, tzinfo=datetime_timezone.utc),
            is_rated=False,
            old_rating=None,
            new_rating=None,
            performance=None,
        )
        mocked_fetch.return_value = normalized_profile([self.first_event, unrated])

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1200)
        self.assertEqual(stats.rated_contest_count, 1)
        self.assertEqual(PlatformRatingEvent.objects.count(), 2)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_empty_history_is_valid_and_keeps_ratings_unknown(self, mocked_fetch):
        mocked_fetch.return_value = normalized_profile([])

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertIsNone(stats.current_rating)
        self.assertIsNone(stats.max_rating)
        self.assertEqual(stats.rated_contest_count, 0)
        self.assertEqual(PlatformRatingEvent.objects.count(), 0)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_failed_sync_preserves_cached_stats_history_and_snapshot(self, mocked_fetch):
        mocked_fetch.return_value = normalized_profile([self.first_event])
        self.client.post(self.sync_url)
        self._expire_cooldown()
        old_updated_at = AtCoderStats.objects.get(
            platform_account=self.account
        ).rating_data_updated_at
        mocked_fetch.side_effect = ProviderSchemaError("Unexpected provider response.")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1200)
        self.assertEqual(stats.rating_data_updated_at, old_updated_at)
        self.assertEqual(PlatformRatingEvent.objects.count(), 1)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_failed_first_sync_creates_no_snapshot(self, mocked_fetch):
        mocked_fetch.side_effect = ExternalServiceError("AtCoder unavailable.")

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(AtCoderStats.objects.exists())
        self.assertFalse(PlatformRatingEvent.objects.exists())
        self.assertFalse(PlatformStatsSnapshot.objects.exists())

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_provider_rate_limit_maps_to_429_without_writes(self, mocked_fetch):
        mocked_fetch.side_effect = ProviderRateLimitError("AtCoder rate limited.")

        response = self.client.post(self.sync_url)
        immediate_retry = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(
            immediate_retry.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
        self.assertFalse(AtCoderStats.objects.exists())
        mocked_fetch.assert_called_once()

    @override_settings(ATCODER_SYNC_COOLDOWN_SECONDS=3600)
    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_atcoder_uses_configurable_conservative_cooldown(self, mocked_fetch):
        self.account.last_synced_at = timezone.now() - timedelta(minutes=10)
        self.account.save(update_fields=["last_synced_at"])
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1200,
            rating_data_updated_at=self.account.last_synced_at,
        )

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["sources"]["rating"]["status"],
            "skipped_fresh",
        )
        self.assertGreaterEqual(
            response.data["sources"]["rating"]["details"][
                "retry_after_seconds"
            ],
            3000,
        )
        mocked_fetch.assert_not_called()

    @override_settings(ATCODER_HISTORY_SYNC_ENABLED=False)
    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_provider_kill_switch_blocks_sync_and_preserves_cached_data(self, mocked_fetch):
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1542,
            max_rating=1600,
            rated_contest_count=50,
            rating_data_updated_at=timezone.now(),
        )

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(
            AtCoderStats.objects.get(platform_account=self.account).current_rating,
            1542,
        )
        mocked_fetch.assert_not_called()

    def test_user_cannot_sync_another_users_atcoder_account(self):
        other_account = PlatformAccount.objects.create(
            user=self.other_user,
            platform=PlatformAccount.Platform.ATCODER,
            handle="other_atcoder",
        )

        response = self.client.post(
            reverse("platform-account-sync", args=[other_account.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_atcoder_handle_is_rejected_on_connection(self):
        self.account.delete()

        response = self.client.post(
            reverse("platform-account-list"),
            {"platform": "atcoder", "handle": "unsafe/handle"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("handle", response.data)

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_atcoder_handle_change_invalidates_only_its_cached_state(self, mocked_fetch):
        mocked_fetch.return_value = normalized_profile([self.first_event])
        self.client.post(self.sync_url)

        response = self.client.patch(
            reverse("platform-account-detail", args=[self.account.pk]),
            {"handle": "new_atcoder_user"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["handle_validated"])
        self.assertFalse(response.data["ownership_verified"])
        self.assertIsNone(response.data["last_synced_at"])
        self.assertIsNone(response.data["atcoder_stats"])
        self.assertEqual(response.data["atcoder_rating_history"], [])
        self.assertFalse(AtCoderStats.objects.exists())
        self.assertFalse(PlatformRatingEvent.objects.exists())
        self.assertFalse(PlatformStatsSnapshot.objects.exists())

    @patch(
        "apps.connectors.providers.atcoder.connector.AtCoderConnector.fetch_normalized_profile"
    )
    def test_platform_reads_use_cached_data_without_external_calls(self, mocked_fetch):
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1542,
            max_rating=1600,
            rated_contest_count=10,
            rating_data_updated_at=timezone.now(),
        )

        response = self.client.get(reverse("platform-account-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["atcoder_stats"]["current_rating"], 1542)
        mocked_fetch.assert_not_called()

    @patch(
        "apps.connectors.providers.atcoder.client.AtCoderHistoryClient.get_algorithm_rating_history"
    )
    def test_dashboard_and_public_profile_reads_never_call_atcoder(self, mocked_history):
        dashboard_response = self.client.get("/api/v1/dashboard/me/")
        self.client.force_authenticate(user=None)
        profile_response = self.client.get(f"/api/v1/profile/{self.user.username}/")

        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        mocked_history.assert_not_called()

    @patch(
        "apps.connectors.providers.atcoder.client.AtCoderHistoryClient.get_algorithm_rating_history"
    )
    def test_schema_change_does_not_replace_valid_cached_values(self, mocked_history):
        AtCoderStats.objects.create(
            platform_account=self.account,
            current_rating=1542,
            max_rating=1600,
            rated_contest_count=10,
            rating_data_updated_at=timezone.now(),
        )
        mocked_history.return_value = [
            {
                "IsRated": True,
                "ContestScreenName": "abc999.contest.atcoder.jp",
                "EndTime": "2024-01-01T00:00:00+09:00",
                # Required rated OldRating/NewRating deliberately missing.
            }
        ]

        response = self.client.post(self.sync_url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        stats = AtCoderStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.current_rating, 1542)
        self.assertEqual(stats.rated_contest_count, 10)
        self.assertFalse(PlatformRatingEvent.objects.exists())

    def _expire_cooldown(self):
        self.account.refresh_from_db()
        self.account.last_synced_at = timezone.now() - timedelta(hours=2)
        self.account.last_sync_attempted_at = timezone.now() - timedelta(hours=2)
        self.account.save(
            update_fields=["last_synced_at", "last_sync_attempted_at"]
        )
        AtCoderSyncState.objects.filter(platform_account=self.account).update(
            rating_sync_attempted_at=timezone.now() - timedelta(hours=2),
            submission_sync_attempted_at=timezone.now() - timedelta(hours=2),
        )
