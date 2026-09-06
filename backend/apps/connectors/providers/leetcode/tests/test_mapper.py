from datetime import datetime, timezone

from apps.connectors.providers.leetcode.domain import (
    LeetCodeContestStatsData,
    LeetCodeProblemStatsData,
    LeetCodeProfileData,
    LeetCodeRatingEventData,
)
from apps.connectors.providers.leetcode.exceptions import LeetCodeInvalidResponseError
from apps.connectors.providers.leetcode.mapper import (
    map_alfa_contest_stats,
    map_alfa_problem_stats,
    map_alfa_profile,
    map_alfa_rating_history,
)
from apps.connectors.providers.leetcode.tests.fixtures import (
    CONTEST_STATS_PAYLOAD,
    PROBLEM_STATS_PAYLOAD,
    PROFILE_PAYLOAD,
    RATING_HISTORY_PAYLOAD,
)
from django.test import SimpleTestCase


class AlfaLeetCodeMapperTests(SimpleTestCase):
    def test_maps_profile_to_stable_domain_object(self):
        result = map_alfa_profile(PROFILE_PAYLOAD)

        self.assertEqual(
            result,
            LeetCodeProfileData(
                handle="tourist-lc",
                profile_url="https://leetcode.com/u/tourist-lc/",
                display_name="Example User",
                avatar_url="https://assets.leetcode.com/users/example/avatar.png",
                country="Bangladesh",
                organization="Example Org",
                school="Example University",
                global_problem_ranking=321,
                reputation=42,
            ),
        )

    def test_maps_problem_stats_to_stable_domain_object(self):
        self.assertEqual(
            map_alfa_problem_stats(PROBLEM_STATS_PAYLOAD),
            LeetCodeProblemStatsData(
                solved_total=100,
                solved_easy=50,
                solved_medium=40,
                solved_hard=10,
                stats_complete=True,
            ),
        )

    def test_maps_nullable_contest_stats(self):
        unrated = {
            "contestAttend": 0,
            "contestRating": None,
            "contestGlobalRanking": None,
            "totalParticipants": None,
            "contestTopPercentage": None,
        }

        self.assertEqual(
            map_alfa_contest_stats(unrated),
            LeetCodeContestStatsData(
                current_rating=None,
                attended_contest_count=0,
                global_ranking=None,
                total_participants=None,
                top_percentage=None,
            ),
        )

    def test_maps_contest_stats_without_alfa_field_leakage(self):
        result = map_alfa_contest_stats(CONTEST_STATS_PAYLOAD)

        self.assertEqual(result.current_rating, 1842.75)
        self.assertEqual(result.attended_contest_count, 12)
        self.assertEqual(result.global_ranking, 12345)
        self.assertEqual(result.top_percentage, 1.76)
        self.assertFalse(hasattr(result, "contestRating"))

    def test_maps_only_attended_rating_events_and_sorts_them(self):
        result = map_alfa_rating_history(RATING_HISTORY_PAYLOAD)

        self.assertEqual(
            result,
            (
                LeetCodeRatingEventData(
                    contest_title="Weekly Contest 400",
                    occurred_at=datetime.fromtimestamp(1710000000, tz=timezone.utc),
                    rating=1725.5,
                    ranking=456,
                    problems_solved=3,
                    total_problems=4,
                    finish_time_seconds=3600,
                    attended=True,
                ),
            ),
        )

    def test_missing_required_problem_stat_is_rejected(self):
        malformed = dict(PROBLEM_STATS_PAYLOAD)
        malformed.pop("hardSolved")

        with self.assertRaisesRegex(LeetCodeInvalidResponseError, "hardSolved"):
            map_alfa_problem_stats(malformed)

    def test_malformed_history_entry_is_rejected(self):
        with self.assertRaisesRegex(LeetCodeInvalidResponseError, "entry 0"):
            map_alfa_rating_history({"contestHistory": ["invalid"]})

    def test_boolean_and_non_finite_numbers_are_rejected(self):
        invalid_count = dict(PROBLEM_STATS_PAYLOAD, solvedProblem=True)
        invalid_rating = dict(CONTEST_STATS_PAYLOAD, contestRating=float("nan"))

        with self.assertRaises(LeetCodeInvalidResponseError):
            map_alfa_problem_stats(invalid_count)
        with self.assertRaises(LeetCodeInvalidResponseError):
            map_alfa_contest_stats(invalid_rating)
