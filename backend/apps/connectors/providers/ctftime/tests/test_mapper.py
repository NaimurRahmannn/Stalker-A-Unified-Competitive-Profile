import json
from pathlib import Path

from django.test import SimpleTestCase

from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.exceptions import CTFtimeInvalidResponseError
from apps.connectors.providers.ctftime.mapper import CTFtimeMapper


class CTFtimeMapperTests(SimpleTestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "team_profile.json"
        with open(fixture_path, "r") as f:
            self.valid_payload = json.load(f)

    def test_map_profile_returns_valid_dto(self):
        profile = CTFtimeMapper.map_profile(self.valid_payload)
        self.assertIsInstance(profile, CTFProfileData)
        self.assertEqual(profile.team_id, "1005")
        self.assertEqual(profile.name, "More Smoked Leet Chicken")
        self.assertEqual(profile.country, "RU")
        self.assertEqual(
            profile.logo_url, "https://ctftime.org//media/team/mslc_150x150_ctftime.png"
        )

    def test_map_profile_requires_id_and_name(self):
        invalid_payload = {"academic": False}
        with self.assertRaises(CTFtimeInvalidResponseError):
            CTFtimeMapper.map_profile(invalid_payload)

    def test_map_rankings_extracts_and_sorts_yearly_data(self):
        rankings = CTFtimeMapper.map_rankings(self.valid_payload)

        self.assertEqual(len(rankings), 3)
        self.assertIsInstance(rankings[0], CTFYearlyRankingData)

        # Newest year first
        self.assertEqual(rankings[0].year, 2025)
        self.assertEqual(rankings[0].global_rank, 41)
        self.assertEqual(rankings[0].country_rank, 3)
        self.assertAlmostEqual(rankings[0].rating_points, 530.243981957)
        self.assertEqual(rankings[0].organizer_points, 0)

        self.assertEqual(rankings[1].year, 2024)
        self.assertEqual(rankings[2].year, 2023)

    def test_map_rankings_handles_missing_fields_gracefully(self):
        payload = {
            "rating": {
                "2023": {
                    "rating_place": None,
                    "rating_points": None,
                }
            }
        }
        rankings = CTFtimeMapper.map_rankings(payload)
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0].year, 2023)
        self.assertIsNone(rankings[0].global_rank)
        self.assertIsNone(rankings[0].country_rank)
        self.assertEqual(rankings[0].rating_points, 0.0)
        self.assertEqual(rankings[0].organizer_points, 0.0)

    def test_map_rankings_ignores_invalid_years(self):
        payload = {
            "rating": {
                "not_a_year": {"rating_place": 1},
                "2023": {"rating_place": 10},
            }
        }
        rankings = CTFtimeMapper.map_rankings(payload)
        self.assertEqual(len(rankings), 1)
        self.assertEqual(rankings[0].year, 2023)
