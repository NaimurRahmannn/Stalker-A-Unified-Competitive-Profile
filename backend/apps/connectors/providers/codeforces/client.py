from typing import Any

import requests

from apps.connectors.base.exceptions import ExternalServiceError, InvalidExternalAccountError


class CodeforcesApiClient:
    BASE_URL = "https://codeforces.com/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _get(self, method: str, params: dict[str, Any], timeout: int | None = None) -> Any:
        url = f"{self.BASE_URL}/{method}"
        try:
            response = requests.get(url, params=params, timeout=timeout or self.timeout)
            if response.status_code == 429:
                raise ExternalServiceError(
                    "Codeforces rate limit reached. Please try again later."
                )
            if response.status_code >= 500:
                raise ExternalServiceError(
                    "Codeforces is temporarily unavailable. Please try again later."
                )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExternalServiceError(
                "Codeforces is temporarily unavailable. Please try again later."
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Codeforces returned an invalid response.") from exc

        status = payload.get("status")
        if status != "OK":
            comment = str(payload.get("comment", "Codeforces API request failed."))
            lowered = comment.lower()
            if "not found" in lowered or "user with handle" in lowered:
                raise InvalidExternalAccountError("Codeforces handle not found.")
            raise ExternalServiceError(f"Codeforces API error: {comment}")

        if "result" not in payload:
            raise ExternalServiceError("Codeforces API response did not include a result.")

        return payload["result"]

    def get_user_info(self, handle: str) -> dict[str, Any]:
        result = self._get("user.info", {"handles": handle})
        if not result:
            raise InvalidExternalAccountError("Codeforces handle not found.")
        return result[0]

    def get_user_submissions(self, handle: str, count: int = 10000) -> list[dict[str, Any]]:
        result = self._get(
            "user.status",
            {"handle": handle, "from": 1, "count": count},
            timeout=15,
        )
        if not isinstance(result, list):
            raise ExternalServiceError("Codeforces user.status returned an unexpected result.")
        return result

    def get_user_rating(self, handle: str) -> list[dict[str, Any]]:
        result = self._get("user.rating", {"handle": handle})
        if not isinstance(result, list):
            raise ExternalServiceError("Codeforces user.rating returned an unexpected result.")
        return result
