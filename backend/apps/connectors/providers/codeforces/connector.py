from typing import Any

from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.utils import build_codeforces_profile_url, normalize_handle
from apps.connectors.providers.codeforces.client import CodeforcesApiClient
from apps.connectors.providers.codeforces.mapper import map_codeforces_user_to_snapshot


class CodeforcesConnector(BaseConnector):
    source = "codeforces"

    def __init__(self, client: CodeforcesApiClient | None = None):
        self.client = client or CodeforcesApiClient()

    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_handle(handle_or_slug)
        return self.client.get_user_info(handle)

    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_handle(handle_or_slug)
        raw_user = self.verify_handle(handle)
        normalized = map_codeforces_user_to_snapshot(raw_user)
        normalized["profile_url"] = build_codeforces_profile_url(handle)
        normalized["handle_or_slug"] = handle
        return normalized
