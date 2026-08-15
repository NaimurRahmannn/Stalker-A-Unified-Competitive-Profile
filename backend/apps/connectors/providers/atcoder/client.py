import logging
import re
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings

from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderNetworkError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderServerError,
    ProviderSyncDisabledError,
    ProviderTimeoutError,
)
from apps.connectors.base.utils import normalize_handle

logger = logging.getLogger(__name__)
ATCODER_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,32}$")


def normalize_atcoder_handle(handle_or_slug: str) -> str:
    handle = normalize_handle(handle_or_slug)
    if not ATCODER_HANDLE_PATTERN.fullmatch(handle):
        raise InvalidExternalAccountError(
            "AtCoder handle must contain only letters, numbers, or underscores."
        )
    return handle


class AtCoderHistoryClient:
    BASE_URL = "https://atcoder.jp"

    def __init__(
        self,
        connect_timeout: float | None = None,
        read_timeout: float | None = None,
        user_agent: str | None = None,
    ):
        self.timeout = (
            connect_timeout or settings.ATCODER_CONNECT_TIMEOUT_SECONDS,
            read_timeout or settings.ATCODER_READ_TIMEOUT_SECONDS,
        )
        self.user_agent = user_agent or settings.STALKER_EXTERNAL_USER_AGENT

    def get_algorithm_rating_history(
        self,
        handle_or_slug: str,
    ) -> list[dict[str, Any]]:
        if not settings.ATCODER_HISTORY_SYNC_ENABLED:
            raise ProviderSyncDisabledError(
                "AtCoder rating synchronization is currently disabled."
            )

        handle = normalize_atcoder_handle(handle_or_slug)
        encoded_handle = quote(handle, safe="")
        url = f"{self.BASE_URL}/users/{encoded_handle}/history/json"

        try:
            response = requests.get(
                url,
                params={"contestType": "algo"},
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
                timeout=self.timeout,
            )
        except requests.Timeout as exc:
            self._log_failure("timeout")
            raise ProviderTimeoutError(
                "AtCoder timed out. Previously synchronized data was preserved."
            ) from exc
        except requests.RequestException as exc:
            self._log_failure("network")
            raise ProviderNetworkError(
                "AtCoder is temporarily unavailable. Previously synchronized data was preserved."
            ) from exc

        if response.status_code == 404:
            self._log_failure("invalid_handle", response.status_code)
            raise InvalidExternalAccountError("AtCoder handle not found.")
        if response.status_code == 403:
            self._log_failure("access_denied", response.status_code)
            raise ProviderAccessDeniedError(
                "AtCoder denied access to rating history. Please try again later."
            )
        if response.status_code == 429:
            self._log_failure("rate_limited", response.status_code)
            raise ProviderRateLimitError(
                "AtCoder rate limit reached. Please try again later."
            )
        if response.status_code >= 500:
            self._log_failure("server_error", response.status_code)
            raise ProviderServerError(
                "AtCoder is temporarily unavailable. Please try again later."
            )
        if response.status_code != 200:
            self._log_failure("unexpected_status", response.status_code)
            raise ExternalServiceError(
                f"AtCoder returned an unexpected HTTP {response.status_code} response."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            self._log_failure("invalid_json", response.status_code)
            raise ProviderSchemaError("AtCoder returned invalid JSON.") from exc

        if not isinstance(payload, list) or any(
            not isinstance(item, dict) for item in payload
        ):
            self._log_failure("unexpected_schema", response.status_code)
            raise ProviderSchemaError(
                "AtCoder rating history has an unexpected response schema."
            )

        return payload

    @staticmethod
    def _log_failure(error_category: str, status_code: int | None = None) -> None:
        logger.warning(
            "AtCoder provider request failed",
            extra={
                "provider": "atcoder",
                "operation": "rating_history",
                "status_code": status_code,
                "error_category": error_category,
            },
        )
