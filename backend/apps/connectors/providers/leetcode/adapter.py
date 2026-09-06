from apps.connectors.providers.leetcode.client import AlfaLeetCodeClient
from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)
from apps.connectors.providers.leetcode.mapper import (
    map_alfa_contest_stats,
    map_alfa_problem_stats,
    map_alfa_profile,
    map_alfa_rating_history,
)


class LeetCodeAlfaAdapter:
    """Adapts alfa transport payloads to the stable LeetCode provider contract."""

    def __init__(self, client: AlfaLeetCodeClient | None = None):
        self.client = client or AlfaLeetCodeClient()

    def get_profile(self, handle: str) -> LeetCodeProfileData:
        return map_alfa_profile(self.client.get_profile(handle))

    def get_problem_stats(self, handle: str) -> LeetCodeProblemStatsData:
        return map_alfa_problem_stats(self.client.get_problem_stats(handle))

    def get_contest_stats(self, handle: str) -> LeetCodeContestStatsData:
        return map_alfa_contest_stats(self.client.get_contest_stats(handle))

    def get_rating_history(
        self,
        handle: str,
    ) -> tuple[LeetCodeRatingEventData, ...]:
        return map_alfa_rating_history(self.client.get_rating_history(handle))
