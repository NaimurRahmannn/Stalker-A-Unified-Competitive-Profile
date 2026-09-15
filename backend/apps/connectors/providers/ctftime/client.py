import logging
from typing import Any
from urllib.parse import urljoin

import requests

from apps.connectors.providers.ctftime.exceptions import (
    CTFtimeConfigurationError,
    CTFtimeInvalidResponseError,
    CTFtimeProviderAccessError,
    CTFtimeProviderRateLimitError,
    CTFtimeProviderTimeoutError,
    CTFtimeProviderUnavailableError,
    CTFtimeTeamNotFoundError,
)

logger = logging.getLogger(__name__)


class CTFtimeClient:
    """
    Direct HTTP client for the CTFtime API.
    Does not interpret domain meaning; only fetches JSON and maps HTTP errors.
    """

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        if not base_url:
            raise CTFtimeConfigurationError("CTFtime base URL cannot be empty")
        if timeout <= 0:
            raise CTFtimeConfigurationError("CTFtime timeout must be strictly positive")

        self.base_url = base_url if base_url.endswith("/") else f"{base_url}/"
        self.timeout = timeout

        # User-Agent is important for public APIs to identify STALKER traffic
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "STALKER/1.0"})

    def get_team_info(self, team_id: str) -> dict[str, Any]:
        """
        Fetch the complete team profile and ratings payload.
        """
        # Ensure team_id is valid for URL construction
        if not team_id or not str(team_id).isdigit():
            raise CTFtimeTeamNotFoundError(f"Invalid team ID format: {team_id}")

        url = urljoin(self.base_url, f"teams/{team_id}/")

        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.Timeout as e:
            raise CTFtimeProviderTimeoutError(
                f"Request to {url} timed out after {self.timeout}s"
            ) from e
        except requests.RequestException as e:
            raise CTFtimeProviderUnavailableError(
                f"Network error accessing {url}"
            ) from e

        if response.status_code == 404:
            raise CTFtimeTeamNotFoundError(f"Team {team_id} not found on CTFtime")
        if response.status_code == 401 or response.status_code == 403:
            raise CTFtimeProviderAccessError(
                f"Access denied to {url} (HTTP {response.status_code})"
            )
        if response.status_code == 429:
            raise CTFtimeProviderRateLimitError(
                f"Rate limited by CTFtime (HTTP 429) for team {team_id}"
            )
        if response.status_code >= 500:
            raise CTFtimeProviderUnavailableError(
                f"CTFtime is currently unavailable (HTTP {response.status_code})"
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise CTFtimeProviderUnavailableError(
                f"Unexpected HTTP {response.status_code} from CTFtime"
            ) from e

        try:
            data = response.json()
        except ValueError as e:
            raise CTFtimeInvalidResponseError("CTFtime returned malformed JSON") from e

        if not isinstance(data, dict):
            raise CTFtimeInvalidResponseError("CTFtime response root must be an object")

        return data
