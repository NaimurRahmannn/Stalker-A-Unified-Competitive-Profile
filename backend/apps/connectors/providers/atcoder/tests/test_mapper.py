from datetime import datetime

from django.test import SimpleTestCase

from apps.connectors.base.exceptions import ProviderSchemaError
from apps.connectors.providers.atcoder.mapper import (
    derive_algorithm_stats,
    get_atcoder_rating_color,
    normalize_algorithm_rating_history,
)


def history_entry(
    contest_id: str,
    end_time: str,
    *,
    is_rated: bool = True,
    old_rating: int | None = 1000,
    new_rating: int | None = 1100,
    place: int | None = 123,
    performance: int | None = 1200,
) -> dict:
    return {
        "IsRated": is_rated,
        "Place": place,
        "OldRating": old_rating,
        "NewRating": new_rating,
        "Performance": performance,
        "InnerPerformance": 1215 if performance is not None else None,
        "ContestScreenName": f"{contest_id}.contest.atcoder.jp",
        "ContestName": f"Contest {contest_id}",
        "ContestNameEn": f"Contest {contest_id} EN",
        "EndTime": end_time,
    }


class AtCoderRatingHistoryMapperTests(SimpleTestCase):
    def test_normalizes_and_sorts_algorithm_events_chronologically(self):
        raw = [
            history_entry(
                "abc200",
                "2024-02-10T21:00:00+09:00",
                old_rating=1300,
                new_rating=1420,
                place=42,
                performance=1600,
            ),
            history_entry(
                "abc100",
                "2024-01-10T21:00:00+09:00",
                old_rating=1200,
                new_rating=1300,
            ),
        ]

        events = normalize_algorithm_rating_history(raw)

        self.assertEqual([event["external_contest_id"] for event in events], ["abc100", "abc200"])
        latest = events[-1]
        self.assertEqual(latest["discipline"], "algorithm")
        self.assertEqual(latest["contest_name"], "Contest abc200")
        self.assertEqual(latest["rank"], 42)
        self.assertEqual(latest["performance"], 1600)
        self.assertEqual(latest["inner_performance"], 1215)
        self.assertEqual(latest["old_rating"], 1300)
        self.assertEqual(latest["new_rating"], 1420)
        self.assertEqual(latest["rating_change"], 120)
        self.assertEqual(
            latest["occurred_at"],
            datetime.fromisoformat("2024-02-10T21:00:00+09:00"),
        )

    def test_unrated_event_keeps_nullable_values_and_is_excluded_from_stats(self):
        events = normalize_algorithm_rating_history(
            [
                history_entry(
                    "practice",
                    "2024-03-10T21:00:00+09:00",
                    is_rated=False,
                    old_rating=None,
                    new_rating=None,
                    place=None,
                    performance=None,
                )
            ]
        )

        self.assertFalse(events[0]["is_rated"])
        self.assertIsNone(events[0]["new_rating"])
        self.assertEqual(
            derive_algorithm_stats(events),
            {
                "current_rating": None,
                "max_rating": None,
                "rated_contest_count": 0,
                "last_rated_at": None,
                "last_performance": None,
            },
        )

    def test_missing_optional_fields_are_preserved_as_null(self):
        entry = history_entry("abc100", "2024-01-01T00:00:00+09:00")
        for field in ("Place", "Performance", "InnerPerformance", "ContestName"):
            entry.pop(field)

        event = normalize_algorithm_rating_history([entry])[0]

        self.assertIsNone(event["rank"])
        self.assertIsNone(event["performance"])
        self.assertIsNone(event["inner_performance"])
        self.assertIsNone(event["contest_name"])

    def test_derives_current_max_count_and_latest_performance_from_rated_events(self):
        events = normalize_algorithm_rating_history(
            [
                history_entry("one", "2024-01-01T00:00:00+09:00", old_rating=0, new_rating=800, performance=900),
                history_entry("unrated", "2024-02-01T00:00:00+09:00", is_rated=False, old_rating=800, new_rating=800),
                history_entry("two", "2024-03-01T00:00:00+09:00", old_rating=800, new_rating=750, performance=700),
            ]
        )

        stats = derive_algorithm_stats(events)

        self.assertEqual(stats["current_rating"], 750)
        self.assertEqual(stats["max_rating"], 800)
        self.assertEqual(stats["rated_contest_count"], 2)
        self.assertEqual(stats["last_performance"], 700)

    def test_missing_required_structure_fails_instead_of_creating_zero_stats(self):
        for field in ("IsRated", "ContestScreenName", "EndTime", "OldRating", "NewRating"):
            with self.subTest(field=field):
                entry = history_entry("abc100", "2024-01-01T00:00:00+09:00")
                entry.pop(field)
                with self.assertRaises(ProviderSchemaError):
                    normalize_algorithm_rating_history([entry])

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaisesRegex(ProviderSchemaError, "EndTime"):
            normalize_algorithm_rating_history(
                [history_entry("abc100", "2024-01-01T00:00:00")]
            )

    def test_rating_color_bands_are_derived_locally(self):
        cases = {
            None: None,
            0: "gray",
            399: "gray",
            400: "brown",
            800: "green",
            1200: "cyan",
            1600: "blue",
            2000: "yellow",
            2400: "orange",
            2800: "red",
        }
        for rating, expected in cases.items():
            with self.subTest(rating=rating):
                self.assertEqual(get_atcoder_rating_color(rating), expected)
