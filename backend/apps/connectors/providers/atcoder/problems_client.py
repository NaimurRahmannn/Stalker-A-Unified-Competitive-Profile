import logging
import threading
import time
from typing import Any

import requests
from django.conf import settings

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderSyncDisabledError,
)
from apps.connectors.providers.atcoder.client import normalize_atcoder_handle


logger = logging.getLogger(__name__)


class AtCoderProblemsClient:
    """Transport-only client for the AtCoderProblems user submissions API."""

    PROVIDER_PAGE_LIMIT = 500
    _request_lock = threading.Lock()
    _last_request_started_at = 0.0

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        min_request_interval: float | None = None,
        user_agent: str | None = None,
    ):
        self.base_url = (base_url or settings.ATCODER_PROBLEMS_BASE_URL).rstrip("/")
        self.timeout = (
            timeout
            if timeout is not None
            else settings.ATCODER_PROBLEMS_TIMEOUT_SECONDS
        )
        self.min_request_interval = (
            min_request_interval
            if min_request_interval is not None
            else settings.ATCODER_PROBLEMS_MIN_REQUEST_INTERVAL_SECONDS
        )
        self.user_agent = user_agent or settings.STALKER_EXTERNAL_USER_AGENT

    def get_user_submissions(
        self,
        handle_or_slug: str,
        from_second: int,
    ) -> list[dict[str, Any]]:
        if not settings.ATCODER_PROBLEMS_SYNC_ENABLED:
            raise ProviderSyncDisabledError(
                "AtCoderProblems submission synchronization is currently disabled."
            )
        if isinstance(from_second, bool) or not isinstance(from_second, int):
            raise ValueError("from_second must be an integer Unix timestamp.")
        if from_second < 0:
            raise ValueError("from_second cannot be negative.")

        handle = normalize_atcoder_handle(handle_or_slug)
        try:
            with self._request_lock:
                self._wait_for_request_slot()
                response = requests.get(
                    f"{self.base_url}/user/submissions",
                    params={"user": handle, "from_second": from_second},
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "application/json",
                    },
                    timeout=self.timeout,
                )
        except requests.Timeout as exc:
            self._log_failure("timeout")
            raise ExternalServiceError(
                "AtCoderProblems timed out. Cached submissions were preserved."
            ) from exc
        except requests.RequestException as exc:
            self._log_failure("network")
            raise ExternalServiceError(
                "AtCoderProblems is temporarily unavailable. Cached submissions were preserved."
            ) from exc

        if response.status_code == 403:
            self._log_failure("access_denied", response.status_code)
            raise ProviderAccessDeniedError(
                "AtCoderProblems denied access. Please try again later."
            )
        if response.status_code == 429:
            self._log_failure("rate_limited", response.status_code)
            raise ProviderRateLimitError(
                "AtCoderProblems rate limit reached. Please try again later."
            )
        if response.status_code >= 500:
            self._log_failure("server_error", response.status_code)
            raise ExternalServiceError(
                "AtCoderProblems is temporarily unavailable. Please try again later."
            )
        if response.status_code != 200:
            self._log_failure("unexpected_status", response.status_code)
            raise ExternalServiceError(
                f"AtCoderProblems returned an unexpected HTTP {response.status_code} response."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            self._log_failure("invalid_json", response.status_code)
            raise ProviderSchemaError("AtCoderProblems returned invalid JSON.") from exc

        if not isinstance(payload, list) or any(
            not isinstance(item, dict) for item in payload
        ):
            self._log_failure("unexpected_schema", response.status_code)
            raise ProviderSchemaError(
                "AtCoderProblems submissions have an unexpected response schema."
            )
        if len(payload) > self.PROVIDER_PAGE_LIMIT:
            self._log_failure("unexpected_page_size", response.status_code)
            raise ProviderSchemaError(
                "AtCoderProblems returned more submissions than its documented limit."
            )
        return payload

    def _wait_for_request_slot(self) -> None:
        interval = max(0.0, self.min_request_interval)
        now = time.monotonic()
        remaining = interval - (now - self._last_request_started_at)
        if remaining > 0:
            time.sleep(remaining)
        type(self)._last_request_started_at = time.monotonic()

    @staticmethod
    def _log_failure(error_category: str, status_code: int | None = None) -> None:
        logger.warning(
            "AtCoderProblems provider request failed",
            extra={
                "provider": "atcoder_problems",
                "operation": "user_submissions",
                "status_code": status_code,
                "error_category": error_category,
            },
        )
