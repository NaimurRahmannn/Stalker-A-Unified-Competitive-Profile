import json
from pathlib import Path
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.connectors.providers.ctftime.adapter import CTFtimeAdapter
from apps.connectors.providers.ctftime.domain import (
    CTFProfileData,
    CTFYearlyRankingData,
)
from apps.connectors.providers.ctftime.provider import CTFProvider


class CTFtimeAdapterTests(SimpleTestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "team_profile.json"
        with open(fixture_path, "r") as f:
            self.valid_payload = json.load(f)

        self.mock_client = MagicMock()
        self.mock_client.get_team_info.return_value = self.valid_payload

        self.adapter = CTFtimeAdapter(client=self.mock_client)

    def test_adapter_satisfies_provider_protocol(self):
        self.assertIsInstance(self.adapter, CTFProvider)

    def test_get_profile_returns_domain_object(self):
        profile = self.adapter.get_profile("1005")

        self.mock_client.get_team_info.assert_called_once_with("1005")
        self.assertIsInstance(profile, CTFProfileData)
        self.assertEqual(profile.team_id, "1005")
        self.assertEqual(profile.name, "More Smoked Leet Chicken")

    def test_get_yearly_rankings_returns_tuple_of_domain_objects(self):
        rankings = self.adapter.get_yearly_rankings("1005")

        self.mock_client.get_team_info.assert_called_once_with("1005")
        self.assertIsInstance(rankings, tuple)
        self.assertTrue(len(rankings) > 0)
        self.assertIsInstance(rankings[0], CTFYearlyRankingData)
        self.assertEqual(rankings[0].year, 2025)
