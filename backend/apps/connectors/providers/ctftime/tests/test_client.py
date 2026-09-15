import json
from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from apps.connectors.providers.ctftime.client import CTFtimeClient
from apps.connectors.providers.ctftime.exceptions import (
    CTFtimeConfigurationError,
    CTFtimeInvalidResponseError,
    CTFtimeProviderAccessError,
    CTFtimeProviderRateLimitError,
    CTFtimeProviderTimeoutError,
    CTFtimeProviderUnavailableError,
    CTFtimeTeamNotFoundError,
)


class CTFtimeClientTests(SimpleTestCase):
    def setUp(self):
        self.client = CTFtimeClient(base_url="https://ctftime.org/api/v1/", timeout=2.0)

    def test_init_validates_configuration(self):
        with self.assertRaises(CTFtimeConfigurationError):
            CTFtimeClient(base_url="")

        with self.assertRaises(CTFtimeConfigurationError):
            CTFtimeClient(base_url="https://ctftime.org", timeout=-1)

    def test_init_sets_user_agent(self):
        self.assertIn("STALKER/", self.client.session.headers["User-Agent"])

    def test_get_team_info_validates_team_id(self):
        with self.assertRaises(CTFtimeTeamNotFoundError):
            self.client.get_team_info("not_a_number")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_successful_request_returns_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1005, "name": "Team"}
        mock_get.return_value = mock_response

        data = self.client.get_team_info("1005")
        self.assertEqual(data["id"], 1005)

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_404_maps_to_team_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeTeamNotFoundError):
            self.client.get_team_info("999999")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_429_maps_to_rate_limit_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeProviderRateLimitError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_timeout_maps_to_provider_timeout_error(self, mock_get):
        mock_get.side_effect = requests.Timeout("Connection timed out")

        with self.assertRaises(CTFtimeProviderTimeoutError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_network_failure_maps_to_provider_unavailable(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        with self.assertRaises(CTFtimeProviderUnavailableError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_403_maps_to_access_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeProviderAccessError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_500_maps_to_unavailable(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 502
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeProviderUnavailableError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_malformed_json_raises_invalid_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeInvalidResponseError):
            self.client.get_team_info("1005")

    @patch("apps.connectors.providers.ctftime.client.requests.Session.get")
    def test_array_json_raises_invalid_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1005}]
        mock_get.return_value = mock_response

        with self.assertRaises(CTFtimeInvalidResponseError):
            self.client.get_team_info("1005")
