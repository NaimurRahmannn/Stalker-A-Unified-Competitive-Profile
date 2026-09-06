from datetime import datetime
from typing import Any

from django.conf import settings

from apps.connectors.base.connector import BaseConnector, SnapshotValues
from apps.connectors.models import LeetCodeStats, PlatformAccount
from apps.connectors.providers.leetcode.adapter import LeetCodeAlfaAdapter
from apps.connectors.providers.leetcode.domain import LeetCodeSyncData
from apps.connectors.providers.leetcode.exceptions import LeetCodeInvalidResponseError
from apps.connectors.providers.leetcode.provider import LeetCodeProvider


class LeetCodeConnector(BaseConnector):
    """Persistence adapter over the provider-independent LeetCode contract."""

    source = PlatformAccount.Platform.LEETCODE
    display_name = "LeetCode"

    def __init__(self, provider: LeetCodeProvider | None = None):
        self.provider = provider or LeetCodeAlfaAdapter()

    @property
    def sync_cooldown_seconds(self) -> int:
        return settings.LEETCODE_SYNC_COOLDOWN_SECONDS

    @property
    def is_enabled(self) -> bool:
        return settings.LEETCODE_SYNC_ENABLED

    @property
    def cooldown_uses_attempts(self) -> bool:
        return True

    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        profile = self.provider.get_profile(handle_or_slug)
        return {"handle": profile.handle, "profile_url": profile.profile_url}

    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        profile = self.provider.get_profile(handle_or_slug)
        problems = self.provider.get_problem_stats(profile.handle)
        contests = self.provider.get_contest_stats(profile.handle)
        history = self.provider.get_rating_history(profile.handle)
        sync_data = LeetCodeSyncData(
            profile=profile,
            problem_stats=problems,
            contest_stats=contests,
            rating_history=history,
        )
        self._validate_complete(sync_data)
        return {
            "handle": profile.handle,
            "profile_url": profile.profile_url,
            "sync_data": sync_data,
        }

    def persist_normalized_profile(
        self,
        platform_account: PlatformAccount,
        profile: dict[str, Any],
        synced_at: datetime,
    ) -> SnapshotValues:
        data: LeetCodeSyncData = profile["sync_data"]
        account_profile = data.profile
        problems = data.problem_stats
        contests = data.contest_stats
        history = [
            {
                "contest_title": event.contest_title,
                "occurred_at": event.occurred_at.isoformat(),
                "rating": event.rating,
                "ranking": event.ranking,
                "problems_solved": event.problems_solved,
                "total_problems": event.total_problems,
                "finish_time_seconds": event.finish_time_seconds,
                "attended": event.attended,
            }
            for event in data.rating_history
        ]
        stats, _ = LeetCodeStats.objects.update_or_create(
            platform_account=platform_account,
            defaults={
                "display_name": account_profile.display_name,
                "avatar_url": account_profile.avatar_url,
                "country": account_profile.country,
                "organization": account_profile.organization,
                "school": account_profile.school,
                "global_problem_ranking": account_profile.global_problem_ranking,
                "reputation": account_profile.reputation,
                "solved_total": problems.solved_total,
                "solved_easy": problems.solved_easy,
                "solved_medium": problems.solved_medium,
                "solved_hard": problems.solved_hard,
                "problem_stats_complete": problems.stats_complete,
                "current_contest_rating": contests.current_rating,
                "attended_contest_count": contests.attended_contest_count,
                "contest_global_ranking": contests.global_ranking,
                "contest_total_participants": contests.total_participants,
                "contest_top_percentage": contests.top_percentage,
                "rating_history": history,
                "data_updated_at": synced_at,
            },
        )
        return SnapshotValues(
            rating=stats.current_contest_rating,
            solved_count=stats.solved_total,
            contest_count=stats.attended_contest_count,
            metadata={
                "problem_stats_complete": stats.problem_stats_complete,
                "solved_easy": stats.solved_easy,
                "solved_medium": stats.solved_medium,
                "solved_hard": stats.solved_hard,
            },
        )

    @staticmethod
    def _validate_complete(data: LeetCodeSyncData) -> None:
        problems = data.problem_stats
        if not problems.stats_complete:
            raise LeetCodeInvalidResponseError(
                "LeetCode problem statistics are incomplete."
            )
        difficulty_total = (
            problems.solved_easy
            + problems.solved_medium
            + problems.solved_hard
        )
        if difficulty_total != problems.solved_total:
            raise LeetCodeInvalidResponseError(
                "LeetCode solved totals are internally inconsistent."
            )
