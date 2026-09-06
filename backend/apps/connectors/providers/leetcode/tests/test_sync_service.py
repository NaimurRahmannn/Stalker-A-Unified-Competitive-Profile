from datetime import datetime, timezone
from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.connectors.models import (
    LeetCodeStats,
    LeetCodeSyncState,
    PlatformAccount,
    PlatformStatsSnapshot,
)
from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)
from apps.connectors.providers.leetcode.exceptions import (
    LeetCodeInvalidResponseError,
    LeetCodeProviderTimeoutError,
    LeetCodeProviderUnavailableError,
    LeetCodeUserNotFoundError,
)
from apps.connectors.providers.leetcode.sync_service import (
    LeetCodeSyncErrorCode,
    LeetCodeSyncService,
)

User = get_user_model()


def configured_provider() -> Mock:
    provider = Mock()
    provider.get_profile.return_value = LeetCodeProfileData(
        handle="tourist-lc",
        profile_url="https://leetcode.com/u/tourist-lc/",
        display_name="Example User",
        avatar_url="https://assets.leetcode.com/avatar.png",
        country="Bangladesh",
        organization="Example Org",
        school="Example University",
        global_problem_ranking=321,
        reputation=42,
    )
    provider.get_problem_stats.return_value = LeetCodeProblemStatsData(
        solved_total=100,
        solved_easy=50,
        solved_medium=40,
        solved_hard=10,
        stats_complete=True,
    )
    provider.get_contest_stats.return_value = LeetCodeContestStatsData(
        current_rating=1842.75,
        attended_contest_count=12,
        global_ranking=12345,
        total_participants=700000,
        top_percentage=1.76,
    )
    provider.get_rating_history.return_value = (
        LeetCodeRatingEventData(
            contest_title="Weekly Contest 400",
            occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            rating=1842.75,
            ranking=456,
            problems_solved=3,
            total_problems=4,
            finish_time_seconds=3600,
            attended=True,
        ),
    )
    return provider


@override_settings(LEETCODE_SYNC_ENABLED=True)
class LeetCodeSyncServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="leetcode-user",
            email="leetcode@example.com",
            password="StrongPassword123!",
        )
        self.account = PlatformAccount.objects.create(
            user=self.user,
            platform=PlatformAccount.Platform.LEETCODE,
            handle="tourist-lc",
        )

    def test_success_persists_complete_state_and_snapshot(self):
        provider = configured_provider()

        result = LeetCodeSyncService(provider=provider).sync(self.account)

        self.assertEqual(result.status, LeetCodeSyncState.Status.SUCCESS)
        self.assertTrue(result.updated)
        self.assertFalse(result.using_cached_data)
        stats = LeetCodeStats.objects.get(platform_account=self.account)
        self.assertEqual(stats.solved_total, 100)
        self.assertEqual(stats.solved_hard, 10)
        self.assertEqual(stats.current_contest_rating, 1842.75)
        self.assertEqual(stats.rating_history[0]["contest_title"], "Weekly Contest 400")
        self.assertIsNotNone(stats.data_updated_at)
        state = LeetCodeSyncState.objects.get(platform_account=self.account)
        self.assertEqual(state.status, LeetCodeSyncState.Status.SUCCESS)
        self.assertEqual(state.failure_reason, "")
        self.assertIsNotNone(state.last_attempted_at)
        self.assertIsNotNone(state.last_successful_at)
        snapshot = PlatformStatsSnapshot.objects.get(
            platform_account=self.account
        )
        self.assertEqual(snapshot.rating, 1842.75)
        self.assertEqual(snapshot.solved_count, 100)
        self.assertEqual(snapshot.contest_count, 12)
        self.account.refresh_from_db()
        self.assertTrue(self.account.is_verified)
        self.assertIsNotNone(self.account.last_sync_attempted_at)
        self.assertIsNotNone(self.account.last_synced_at)

    def test_repeated_sync_updates_one_stats_row_without_duplicate_snapshot(self):
        provider = configured_provider()
        service = LeetCodeSyncService(provider=provider)

        service.sync(self.account)
        service.sync(self.account)

        self.assertEqual(LeetCodeStats.objects.count(), 1)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)
        self.assertEqual(provider.get_profile.call_count, 2)

    def test_changed_repeat_sync_updates_current_row_and_adds_snapshot(self):
        provider = configured_provider()
        service = LeetCodeSyncService(provider=provider)
        service.sync(self.account)
        provider.get_problem_stats.return_value = LeetCodeProblemStatsData(
            solved_total=101,
            solved_easy=51,
            solved_medium=40,
            solved_hard=10,
            stats_complete=True,
        )

        service.sync(self.account)

        self.assertEqual(LeetCodeStats.objects.count(), 1)
        self.assertEqual(LeetCodeStats.objects.get().solved_total, 101)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 2)

    def test_supported_provider_failures_are_normalized(self):
        cases = (
            (
                LeetCodeProviderTimeoutError("timed out"),
                LeetCodeSyncErrorCode.TIMEOUT,
            ),
            (
                LeetCodeUserNotFoundError("missing"),
                LeetCodeSyncErrorCode.INVALID_USERNAME,
            ),
            (
                LeetCodeInvalidResponseError("malformed"),
                LeetCodeSyncErrorCode.INVALID_RESPONSE,
            ),
            (
                LeetCodeProviderUnavailableError("unavailable"),
                LeetCodeSyncErrorCode.PROVIDER_UNAVAILABLE,
            ),
        )
        for error, expected_code in cases:
            with self.subTest(error=type(error).__name__):
                provider = configured_provider()
                provider.get_profile.side_effect = error

                result = LeetCodeSyncService(provider=provider).sync(self.account)

                self.assertEqual(result.status, LeetCodeSyncState.Status.FAILED)
                self.assertEqual(result.error_code, expected_code)
                self.assertFalse(result.updated)
                state = LeetCodeSyncState.objects.get(
                    platform_account=self.account
                )
                self.assertEqual(state.failure_reason, expected_code.value)
                self.assertFalse(LeetCodeStats.objects.exists())
                self.assertFalse(PlatformStatsSnapshot.objects.exists())

    def test_failed_refresh_preserves_last_valid_data_and_success_time(self):
        provider = configured_provider()
        service = LeetCodeSyncService(provider=provider)
        first = service.sync(self.account)
        original_stats = LeetCodeStats.objects.get(platform_account=self.account)
        original_updated_at = original_stats.data_updated_at
        provider.get_problem_stats.side_effect = LeetCodeProviderTimeoutError(
            "timed out"
        )

        failed = service.sync(self.account)

        original_stats.refresh_from_db()
        self.assertEqual(original_stats.solved_total, 100)
        self.assertEqual(original_stats.data_updated_at, original_updated_at)
        self.assertEqual(PlatformStatsSnapshot.objects.count(), 1)
        self.assertTrue(failed.using_cached_data)
        self.assertEqual(failed.successful_at, first.successful_at)
        self.account.refresh_from_db()
        self.assertEqual(self.account.last_synced_at, first.successful_at)

    def test_incomplete_problem_data_is_rejected_before_persistence(self):
        provider = configured_provider()
        provider.get_problem_stats.return_value = LeetCodeProblemStatsData(
            solved_total=100,
            solved_easy=50,
            solved_medium=40,
            solved_hard=10,
            stats_complete=False,
        )

        result = LeetCodeSyncService(provider=provider).sync(self.account)

        self.assertEqual(
            result.error_code,
            LeetCodeSyncErrorCode.INVALID_RESPONSE,
        )
        self.assertFalse(LeetCodeStats.objects.exists())
        self.assertFalse(PlatformStatsSnapshot.objects.exists())

    def test_non_leetcode_account_is_rejected_without_side_effects(self):
        self.account.platform = PlatformAccount.Platform.CODEFORCES
        self.account.save(update_fields=["platform"])

        with self.assertRaisesMessage(ValueError, "requires a LeetCode account"):
            LeetCodeSyncService(provider=configured_provider()).sync(self.account)

        self.assertFalse(LeetCodeSyncState.objects.exists())
