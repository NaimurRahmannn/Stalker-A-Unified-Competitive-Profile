from typing import Any

import requests

from apps.connectors.base.exceptions import ExternalServiceError, InvalidExternalAccountError


class CodeforcesApiClient:
    BASE_URL = "https://codeforces.com/api"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_user_info(self, handle: str) -> dict[str, Any]:
        url = f"{self.BASE_URL}/user.info"
        try:
            response = requests.get(url, params={"handles": handle}, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExternalServiceError("Unable to reach Codeforces API right now.") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceError("Codeforces returned an invalid response.") from exc

        status = payload.get("status")
        if status != "OK":
            comment = str(payload.get("comment", "Codeforces API request failed."))
            lowered = comment.lower()
            if "not found" in lowered or "user with handle" in lowered:
                raise InvalidExternalAccountError("Codeforces handle was not found.")
            raise ExternalServiceError(f"Codeforces API error: {comment}")

        result = payload.get("result") or []
        if not result:
            raise InvalidExternalAccountError("Codeforces handle was not found.")

        return result[0]
