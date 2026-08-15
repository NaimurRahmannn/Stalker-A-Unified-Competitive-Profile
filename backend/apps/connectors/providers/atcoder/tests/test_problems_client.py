from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase, override_settings

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderSyncDisabledError,
)
from apps.connectors.providers.atcoder.problems_client import AtCoderProblemsClient


class AtCoderProblemsClientTests(SimpleTestCase):
    def setUp(self):
        AtCoderProblemsClient._last_request_started_at = 0.0
        self.client = AtCoderProblemsClient(
            base_url="https://example.test/api/v3/",
            timeout=8.0,
            min_request_interval=0,
            user_agent="STALKER/tests",
        )

    @staticmethod
    def response(status_code=200, payload=None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = [] if payload is None else payload
        return response

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_constructs_user_submissions_request_with_cursor(self, mocked_get):
        payload = [{"id": 123}]
        mocked_get.return_value = self.response(payload=payload)

        result = self.client.get_user_submissions("  user_name  ", 1700000000)

        self.assertEqual(result, payload)
        mocked_get.assert_called_once_with(
            "https://example.test/api/v3/user/submissions",
            params={"user": "user_name", "from_second": 1700000000},
            headers={"User-Agent": "STALKER/tests", "Accept": "application/json"},
            timeout=8.0,
        )

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_empty_json_is_valid(self, mocked_get):
        mocked_get.return_value = self.response(payload=[])

        self.assertEqual(self.client.get_user_submissions("user", 0), [])

    @override_settings(ATCODER_PROBLEMS_SYNC_ENABLED=False)
    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_provider_kill_switch_prevents_request(self, mocked_get):
        with self.assertRaises(ProviderSyncDisabledError):
            self.client.get_user_submissions("user", 0)
        mocked_get.assert_not_called()

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_malformed_json_raises_schema_error(self, mocked_get):
        response = self.response()
        response.json.side_effect = ValueError("invalid")
        mocked_get.return_value = response

        with self.assertRaisesRegex(ProviderSchemaError, "invalid JSON"):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_unexpected_top_level_schema_raises_schema_error(self, mocked_get):
        mocked_get.return_value = self.response(payload={"submissions": []})

        with self.assertRaises(ProviderSchemaError):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_unexpected_item_schema_raises_schema_error(self, mocked_get):
        mocked_get.return_value = self.response(payload=["invalid"])

        with self.assertRaises(ProviderSchemaError):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_oversized_page_raises_schema_error(self, mocked_get):
        mocked_get.return_value = self.response(payload=[{}] * 501)

        with self.assertRaisesRegex(ProviderSchemaError, "documented limit"):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_403_maps_to_access_denied(self, mocked_get):
        mocked_get.return_value = self.response(status_code=403)

        with self.assertRaises(ProviderAccessDeniedError):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_429_maps_to_rate_limit(self, mocked_get):
        mocked_get.return_value = self.response(status_code=429)

        with self.assertRaises(ProviderRateLimitError):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_5xx_maps_to_temporary_failure(self, mocked_get):
        mocked_get.return_value = self.response(status_code=503)

        with self.assertRaisesRegex(ExternalServiceError, "temporarily unavailable"):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_timeout_maps_to_temporary_failure(self, mocked_get):
        mocked_get.side_effect = requests.Timeout("slow")

        with self.assertRaisesRegex(ExternalServiceError, "timed out"):
            self.client.get_user_submissions("user", 0)

    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_network_failure_maps_to_temporary_failure(self, mocked_get):
        mocked_get.side_effect = requests.ConnectionError("offline")

        with self.assertRaisesRegex(ExternalServiceError, "temporarily unavailable"):
            self.client.get_user_submissions("user", 0)

    def test_invalid_cursor_is_rejected_before_request(self):
        with patch(
            "apps.connectors.providers.atcoder.problems_client.requests.get"
        ) as mocked_get:
            with self.assertRaises(ValueError):
                self.client.get_user_submissions("user", -1)
            mocked_get.assert_not_called()

    @patch("apps.connectors.providers.atcoder.problems_client.time.sleep")
    @patch("apps.connectors.providers.atcoder.problems_client.time.monotonic")
    @patch("apps.connectors.providers.atcoder.problems_client.requests.get")
    def test_request_spacing_is_provider_wide_in_process(
        self,
        mocked_get,
        mocked_monotonic,
        mocked_sleep,
    ):
        mocked_get.return_value = self.response(payload=[])
        mocked_monotonic.side_effect = [10.0, 10.0, 10.5, 11.1]
        client = AtCoderProblemsClient(
            base_url="https://example.test",
            min_request_interval=1.1,
        )
        second_client = AtCoderProblemsClient(
            base_url="https://example.test",
            min_request_interval=1.1,
        )

        client.get_user_submissions("user", 0)
        second_client.get_user_submissions("user", 0)

        mocked_sleep.assert_called_once()
        self.assertAlmostEqual(mocked_sleep.call_args.args[0], 0.6)
        self.assertEqual(mocked_get.call_count, 2)
