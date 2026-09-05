from typing import Protocol, runtime_checkable

from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)


@runtime_checkable
class LeetCodeProvider(Protocol):
    """Stable STALKER contract for any future LeetCode data source."""

    def get_profile(self, handle: str) -> LeetCodeProfileData: ...

    def get_problem_stats(self, handle: str) -> LeetCodeProblemStatsData: ...

    def get_contest_stats(self, handle: str) -> LeetCodeContestStatsData: ...

    def get_rating_history(
        self,
        handle: str,
    ) -> tuple[LeetCodeRatingEventData, ...]: ...
