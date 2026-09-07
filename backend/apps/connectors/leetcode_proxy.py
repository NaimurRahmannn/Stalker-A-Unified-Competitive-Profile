import hashlib
import json
import logging
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = getattr(settings, "LEETCODE_GRAPHQL_CACHE_TTL", 3600)  # 1 hour cache by default


class LeetCodeGraphQLProxy:
    """High-performance proxy and caching service for LeetCode GraphQL API."""

    LEETCODE_URL = "https://leetcode.com/graphql"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "Accept": "application/json",
    }

    def execute_query(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
        bypass_cache: bool = False,
    ) -> tuple[dict[str, Any], bool]:
        """Execute GraphQL query with caching.

        Returns (response_data, is_cached_hit)
        """
        variables = variables or {}
        username = variables.get("username", "").strip()

        # Build unique cache key
        cache_key = self._build_cache_key(query, variables)

        if not bypass_cache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"LeetCode GraphQL Cache HIT for user: '{username}'")
                return cached_data, True

        logger.info(f"LeetCode GraphQL Cache MISS for user: '{username}'. Fetching upstream...")
        data = self._fetch_upstream(query, variables)

        # Cache valid responses
        if data and "errors" not in data:
            cache.set(cache_key, data, timeout=CACHE_TTL_SECONDS)

        return data, False

    def _fetch_upstream(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        session = requests.Session()
        try:
            resp = session.post(
                self.LEETCODE_URL,
                json={"query": query, "variables": variables},
                headers=self.HEADERS,
                timeout=(3.05, 10.0),
            )
            if resp.status_code != 200:
                logger.warning(f"LeetCode upstream returned status {resp.status_code}")
                return {"errors": [{"message": f"Upstream LeetCode error HTTP {resp.status_code}"}]}
            return resp.json()
        except requests.RequestException as exc:
            logger.error(f"LeetCode upstream fetch failed: {exc}")
            return {"errors": [{"message": "Failed to connect to LeetCode upstream service."}]}

    @staticmethod
    def _build_cache_key(query: str, variables: dict[str, Any]) -> str:
        username = variables.get("username", "").lower().strip()
        query_hash = hashlib.md5(query.encode("utf-8")).hexdigest()[:12]
        if username:
            return f"leetcode:gql:{username}:{query_hash}"
        return f"leetcode:gql:raw:{hashlib.md5(json.dumps({'q': query, 'v': variables}, sort_keys=True).encode()).hexdigest()[:16]}"
