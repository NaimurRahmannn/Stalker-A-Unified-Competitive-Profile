from unittest.mock import Mock

import requests
from apps.connectors.providers.leetcode.client import AlfaLeetCodeClient
from apps.connectors.providers.leetcode.exceptions import (
    LeetCodeConfigurationError,
    LeetCodeInvalidResponseError,
    LeetCodeProviderAccessError,
    LeetCodeProviderRateLimitError,
    LeetCodeProviderTimeoutError,
    LeetCodeProviderUnavailableError,
    LeetCodeUserNotFoundError,
)
from django.test import SimpleTestCase, override_settings


class AlfaLeetCodeClientTests(SimpleTestCase):
    def setUp(self):
        self.session = Mock()
        self.client = AlfaLeetCodeClient(
            base_url="https://alfa.internal.test/",
            connect_timeout=2.0,
            read_timeout=7.0,
            user_agent="STALKER/tests",
            session=self.session,
        )

    @staticmethod
    def response(status_code=200, payload=None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = {} if payload is None else payload
        return response

    def test_constructs_only_alfa_aware_endpoint_paths(self):
        self.session.get.return_value = self.response(payload={"contestHistory": []})

        result = self.client.get_rating_history(" user/name ")

        self.assertEqual(result, {"contestHistory": []})
        self.session.get.assert_called_once_with(
            "https://alfa.internal.test/user%2Fname/contest/history",
            headers={"User-Agent": "STALKER/tests", "Accept": "application/json"},
            timeout=(2.0, 7.0),
        )

    def test_404_maps_to_user_not_found(self):
        self.session.get.return_value = self.response(status_code=404)

        with self.assertRaisesRegex(LeetCodeUserNotFoundError, "not found"):
            self.client.get_profile("missing")

    def test_graphql_error_body_maps_missing_user_without_leaking_payload(self):
        self.session.get.return_value = self.response(
            payload={"errors": [{"message": "That user does not exist"}]}
        )

        with self.assertRaisesRegex(LeetCodeUserNotFoundError, "not found"):
            self.client.get_profile("missing")

    def test_malformed_json_maps_to_invalid_response(self):
        response = self.response()
        response.json.side_effect = ValueError("bad json")
        self.session.get.return_value = response

        with self.assertRaisesRegex(LeetCodeInvalidResponseError, "invalid JSON"):
            self.client.get_profile("user")

    def test_non_object_payload_maps_to_invalid_response(self):
        self.session.get.return_value = self.response(payload=[])

        with self.assertRaisesRegex(
            LeetCodeInvalidResponseError, "unexpected response schema"
        ):
            self.client.get_profile("user")

    def test_provider_failure_maps_to_unavailable(self):
        self.session.get.return_value = self.response(status_code=503)

        with self.assertRaises(LeetCodeProviderUnavailableError):
            self.client.get_profile("user")

    def test_rate_limit_maps_to_normalized_error(self):
        self.session.get.return_value = self.response(status_code=429)

        with self.assertRaises(LeetCodeProviderRateLimitError):
            self.client.get_profile("user")

    def test_timeout_maps_to_normalized_timeout(self):
        self.session.get.side_effect = requests.Timeout("slow")

        with self.assertRaises(LeetCodeProviderTimeoutError):
            self.client.get_profile("user")

    def test_access_failure_maps_to_configuration_aware_error(self):
        self.session.get.return_value = self.response(status_code=401)

        with self.assertRaisesRegex(LeetCodeProviderAccessError, "configuration"):
            self.client.get_profile("user")

    @override_settings(LEETCODE_ALFA_BASE_URL="")
    def test_missing_base_url_fails_before_any_request(self):
        with self.assertRaisesRegex(
            LeetCodeConfigurationError, "LEETCODE_ALFA_BASE_URL"
        ):
            AlfaLeetCodeClient(session=self.session)
        self.session.get.assert_not_called()

    def test_invalid_base_url_fails_before_any_request(self):
        with self.assertRaises(LeetCodeConfigurationError):
            AlfaLeetCodeClient(base_url="not-a-url", session=self.session)
        self.session.get.assert_not_called()

    def test_invalid_timeout_fails_before_any_request(self):
        with self.assertRaisesRegex(
            LeetCodeConfigurationError, "LEETCODE_ALFA_READ_TIMEOUT_SECONDS"
        ):
            AlfaLeetCodeClient(
                base_url="https://alfa.internal.test",
                read_timeout=0,
                session=self.session,
            )
        self.session.get.assert_not_called()
