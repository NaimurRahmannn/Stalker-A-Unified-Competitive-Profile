import logging
import math
from typing import Any
from urllib.parse import quote, urlparse

import requests
from apps.connectors.providers.leetcode.exceptions import (
    LeetCodeConfigurationError,
    LeetCodeInvalidResponseError,
    LeetCodeProviderAccessError,
    LeetCodeProviderRateLimitError,
    LeetCodeProviderTimeoutError,
    LeetCodeProviderUnavailableError,
    LeetCodeUserNotFoundError,
)
from django.conf import settings

logger = logging.getLogger(__name__)


class AlfaLeetCodeClient:
    """HTTP transport for alfa-leetcode-api.

    Raw alfa payloads intentionally stop at the adapter/mapper boundary.
    """

    def __init__(
        self,
        base_url: str | None = None,
        connect_timeout: float | None = None,
        read_timeout: float | None = None,
        user_agent: str | None = None,
        session: requests.Session | None = None,
    ):
        configured_base_url = (
            settings.LEETCODE_ALFA_BASE_URL if base_url is None else base_url
        )
        self.base_url = self._normalize_base_url(configured_base_url)
        self.timeout = (
            self._normalize_timeout(
                connect_timeout
                if connect_timeout is not None
                else settings.LEETCODE_ALFA_CONNECT_TIMEOUT_SECONDS,
                "LEETCODE_ALFA_CONNECT_TIMEOUT_SECONDS",
            ),
            self._normalize_timeout(
                read_timeout
                if read_timeout is not None
                else settings.LEETCODE_ALFA_READ_TIMEOUT_SECONDS,
                "LEETCODE_ALFA_READ_TIMEOUT_SECONDS",
            ),
        )
        configured_user_agent = user_agent or settings.STALKER_EXTERNAL_USER_AGENT
        if (
            not isinstance(configured_user_agent, str)
            or not configured_user_agent.strip()
        ):
            raise LeetCodeConfigurationError(
                "STALKER_EXTERNAL_USER_AGENT must be configured before using LeetCode."
            )
        self.user_agent = configured_user_agent.strip()
        self.session = session if session is not None else requests.Session()

    def get_profile(self, handle: str) -> dict[str, Any]:
        return self._get(handle, "profile")

    def get_problem_stats(self, handle: str) -> dict[str, Any]:
        return self._get(handle, "problem_stats", "solved")

    def get_contest_stats(self, handle: str) -> dict[str, Any]:
        return self._get(handle, "contest_stats", "contest")

    def get_rating_history(self, handle: str) -> dict[str, Any]:
        return self._get(handle, "rating_history", "contest", "history")

    def _get(
        self,
        handle: str,
        operation: str,
        *suffix: str,
    ) -> dict[str, Any]:
        normalized_handle = self._normalize_handle(handle)
        path_parts = [quote(normalized_handle, safe="")]
        path_parts.extend(quote(part, safe="") for part in suffix)
        path = "/".join(path_parts)
        url = f"{self.base_url}/{path}"

        try:
            response = self.session.get(
                url,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json",
                },
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            self._log_failure(operation, "timeout")
            raise LeetCodeProviderTimeoutError(
                "The LeetCode provider timed out."
            ) from exc
        except requests.RequestException as exc:
            self._log_failure(operation, "network")
            raise LeetCodeProviderUnavailableError(
                "The LeetCode provider is temporarily unavailable."
            ) from exc

        if response.status_code == 404:
            self._log_failure(operation, "user_not_found", response.status_code)
            raise LeetCodeUserNotFoundError("LeetCode user not found.")
        if response.status_code in (401, 403):
            self._log_failure(operation, "access_denied", response.status_code)
            raise LeetCodeProviderAccessError(
                "The LeetCode provider rejected access. Check provider configuration."
            )
        if response.status_code == 429:
            self._log_failure(operation, "rate_limited", response.status_code)
            raise LeetCodeProviderRateLimitError(
                "The LeetCode provider rate limit was reached."
            )
        if response.status_code >= 500:
            self._log_failure(operation, "server_error", response.status_code)
            raise LeetCodeProviderUnavailableError(
                "The LeetCode provider is temporarily unavailable."
            )
        if response.status_code != 200:
            self._log_failure(operation, "unexpected_status", response.status_code)
            raise LeetCodeProviderUnavailableError(
                f"The LeetCode provider returned HTTP {response.status_code}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            self._log_failure(operation, "invalid_json", response.status_code)
            raise LeetCodeInvalidResponseError(
                "The LeetCode provider returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            self._log_failure(operation, "unexpected_schema", response.status_code)
            raise LeetCodeInvalidResponseError(
                "The LeetCode provider returned an unexpected response schema."
            )

        provider_errors = payload.get("errors")
        if provider_errors:
            self._raise_provider_payload_error(operation, provider_errors)
        if payload.get("error"):
            self._raise_provider_payload_error(operation, payload["error"])

        return payload

    @staticmethod
    def _normalize_base_url(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise LeetCodeConfigurationError(
                "LEETCODE_ALFA_BASE_URL must be configured before using LeetCode."
            )
        normalized = value.strip().rstrip("/")
        parsed = urlparse(normalized)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.query
            or parsed.fragment
        ):
            raise LeetCodeConfigurationError(
                "LEETCODE_ALFA_BASE_URL must be a valid HTTP(S) base URL."
            )
        return normalized

    @staticmethod
    def _normalize_handle(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise LeetCodeUserNotFoundError("A LeetCode handle is required.")
        return value.strip()

    @staticmethod
    def _normalize_timeout(value: Any, setting_name: str) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or value <= 0
        ):
            raise LeetCodeConfigurationError(
                f"{setting_name} must be a positive finite number."
            )
        return float(value)

    def _raise_provider_payload_error(self, operation: str, error: Any) -> None:
        message = self._error_text(error)
        lowered = message.lower()
        if any(
            marker in lowered
            for marker in ("not found", "does not exist", "doesn't exist", "no user")
        ):
            self._log_failure(operation, "user_not_found")
            raise LeetCodeUserNotFoundError("LeetCode user not found.")
        self._log_failure(operation, "provider_error_payload")
        raise LeetCodeProviderUnavailableError(
            "The LeetCode provider could not complete the request."
        )

    @staticmethod
    def _error_text(error: Any) -> str:
        if isinstance(error, str):
            return error
        if isinstance(error, dict):
            return str(error.get("message", ""))
        if isinstance(error, list):
            return " ".join(AlfaLeetCodeClient._error_text(item) for item in error)
        return ""

    @staticmethod
    def _log_failure(
        operation: str,
        error_category: str,
        status_code: int | None = None,
    ) -> None:
        logger.warning(
            "LeetCode provider request failed",
            extra={
                "provider": "leetcode",
                "adapter": "alfa",
                "operation": operation,
                "status_code": status_code,
                "error_category": error_category,
            },
        )
