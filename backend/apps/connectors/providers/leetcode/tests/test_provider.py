from unittest.mock import Mock

from apps.connectors.providers.leetcode.adapter import LeetCodeAlfaAdapter
from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)
from apps.connectors.providers.leetcode.provider import LeetCodeProvider
from apps.connectors.providers.leetcode.tests.fixtures import (
    CONTEST_STATS_PAYLOAD,
    PROBLEM_STATS_PAYLOAD,
    PROFILE_PAYLOAD,
    RATING_HISTORY_PAYLOAD,
)
from django.test import SimpleTestCase


class LeetCodeAlfaAdapterTests(SimpleTestCase):
    def setUp(self):
        self.client = Mock()
        self.client.get_profile.return_value = PROFILE_PAYLOAD
        self.client.get_problem_stats.return_value = PROBLEM_STATS_PAYLOAD
        self.client.get_contest_stats.return_value = CONTEST_STATS_PAYLOAD
        self.client.get_rating_history.return_value = RATING_HISTORY_PAYLOAD
        self.provider = LeetCodeAlfaAdapter(client=self.client)

    def test_adapter_satisfies_provider_contract(self):
        self.assertIsInstance(self.provider, LeetCodeProvider)

    def test_adapter_returns_only_stable_stalker_objects(self):
        profile = self.provider.get_profile("user")
        problems = self.provider.get_problem_stats("user")
        contests = self.provider.get_contest_stats("user")
        history = self.provider.get_rating_history("user")

        self.assertIsInstance(profile, LeetCodeProfileData)
        self.assertIsInstance(problems, LeetCodeProblemStatsData)
        self.assertIsInstance(contests, LeetCodeContestStatsData)
        self.assertTrue(
            all(isinstance(event, LeetCodeRatingEventData) for event in history)
        )
        self.assertIsInstance(history, tuple)

        self.client.get_profile.assert_called_once_with("user")
        self.client.get_problem_stats.assert_called_once_with("user")
        self.client.get_contest_stats.assert_called_once_with("user")
        self.client.get_rating_history.assert_called_once_with("user")
