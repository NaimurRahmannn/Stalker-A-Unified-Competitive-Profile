from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderSyncDisabledError,
)
from apps.connectors.providers.atcoder.client import AtCoderHistoryClient


class AtCoderHistoryClientTests(SimpleTestCase):
    def setUp(self):
        self.client = AtCoderHistoryClient(
            connect_timeout=2.0,
            read_timeout=7.0,
            user_agent="STALKER/tests",
        )

    @staticmethod
    def response(status_code=200, payload=None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = [] if payload is None else payload
        return response

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_constructs_algorithm_history_request_and_normalizes_handle(self, mocked_get):
        payload = [{"ContestScreenName": "abc100.contest.atcoder.jp"}]
        mocked_get.return_value = self.response(payload=payload)

        result = self.client.get_algorithm_rating_history("  user_name  ")

        self.assertEqual(result, payload)
        mocked_get.assert_called_once_with(
            "https://atcoder.jp/users/user_name/history/json",
            params={"contestType": "algo"},
            headers={"User-Agent": "STALKER/tests", "Accept": "application/json"},
            timeout=(2.0, 7.0),
        )

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_empty_history_is_a_valid_response(self, mocked_get):
        mocked_get.return_value = self.response(payload=[])

        self.assertEqual(self.client.get_algorithm_rating_history("new_user"), [])

    def test_rejects_unsafe_handle_before_request(self):
        with patch("apps.connectors.providers.atcoder.client.requests.get") as mocked_get:
            with self.assertRaises(InvalidExternalAccountError):
                self.client.get_algorithm_rating_history("user/name")
            mocked_get.assert_not_called()

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_malformed_json_raises_schema_error(self, mocked_get):
        response = self.response()
        response.json.side_effect = ValueError("bad json")
        mocked_get.return_value = response

        with self.assertRaisesRegex(ProviderSchemaError, "invalid JSON"):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_unexpected_top_level_schema_raises_schema_error(self, mocked_get):
        mocked_get.return_value = self.response(payload={"history": []})

        with self.assertRaisesRegex(ProviderSchemaError, "unexpected response schema"):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_unexpected_entry_schema_raises_schema_error(self, mocked_get):
        mocked_get.return_value = self.response(payload=["not-an-object"])

        with self.assertRaises(ProviderSchemaError):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_404_maps_to_invalid_handle(self, mocked_get):
        mocked_get.return_value = self.response(status_code=404)

        with self.assertRaisesRegex(InvalidExternalAccountError, "not found"):
            self.client.get_algorithm_rating_history("missing")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_403_maps_to_access_denied(self, mocked_get):
        mocked_get.return_value = self.response(status_code=403)

        with self.assertRaises(ProviderAccessDeniedError):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_429_maps_to_rate_limit(self, mocked_get):
        mocked_get.return_value = self.response(status_code=429)

        with self.assertRaises(ProviderRateLimitError):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_5xx_maps_to_temporary_failure(self, mocked_get):
        mocked_get.return_value = self.response(status_code=503)

        with self.assertRaisesRegex(ExternalServiceError, "temporarily unavailable"):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_timeout_maps_to_temporary_failure(self, mocked_get):
        mocked_get.side_effect = requests.Timeout("slow")

        with self.assertRaisesRegex(ExternalServiceError, "timed out"):
            self.client.get_algorithm_rating_history("user")

    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_network_failure_maps_to_temporary_failure(self, mocked_get):
        mocked_get.side_effect = requests.ConnectionError("offline")

        with self.assertRaisesRegex(ExternalServiceError, "temporarily unavailable"):
            self.client.get_algorithm_rating_history("user")

    @override_settings(ATCODER_HISTORY_SYNC_ENABLED=False)
    @patch("apps.connectors.providers.atcoder.client.requests.get")
    def test_kill_switch_prevents_external_request(self, mocked_get):
        with self.assertRaises(ProviderSyncDisabledError):
            self.client.get_algorithm_rating_history("user")
        mocked_get.assert_not_called()
