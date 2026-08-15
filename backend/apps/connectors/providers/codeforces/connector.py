from datetime import datetime
from typing import Any

from django.conf import settings

from apps.connectors.base.connector import BaseConnector, SnapshotValues
from apps.connectors.base.utils import build_codeforces_profile_url, normalize_handle
from apps.connectors.models import CodeforcesStats, PlatformAccount
from apps.connectors.providers.codeforces.client import CodeforcesApiClient
from apps.connectors.providers.codeforces.mapper import map_codeforces_profile


class CodeforcesConnector(BaseConnector):
    source = "codeforces"
    display_name = "Codeforces"

    def __init__(self, client: CodeforcesApiClient | None = None):
        self.client = client or CodeforcesApiClient()

    @property
    def sync_cooldown_seconds(self) -> int:
        return settings.CODEFORCES_SYNC_COOLDOWN_SECONDS

    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_handle(handle_or_slug)
        return self.client.get_user_info(handle)

    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_handle(handle_or_slug)
        raw_user = self.client.get_user_info(handle)
        canonical_handle = raw_user.get("handle") or handle

        submissions = self.client.get_user_submissions(canonical_handle)
        rating_history = self.client.get_user_rating(canonical_handle)

        normalized = map_codeforces_profile(
            raw_user=raw_user,
            submissions=submissions,
            rating_history=rating_history,
            handle=canonical_handle,
        )
        normalized["handle_or_slug"] = canonical_handle
        normalized["profile_url"] = build_codeforces_profile_url(canonical_handle)
        return normalized

    def persist_normalized_profile(
        self,
        platform_account: PlatformAccount,
        profile: dict[str, Any],
        synced_at: datetime,
    ) -> SnapshotValues:
        stats, _ = CodeforcesStats.objects.update_or_create(
            platform_account=platform_account,
            defaults={
                "handle": profile["handle"],
                "rating": profile["rating"],
                "max_rating": profile["max_rating"],
                "rank": profile["rank"],
                "max_rank": profile["max_rank"],
                "solved_count": profile["solved_count"],
                "attempted_count": profile["attempted_count"],
                "accepted_submission_count": profile["accepted_submission_count"],
                "contest_count": profile["contest_count"],
                "last_online_at": profile["last_online_at"],
                "registered_at": profile["registered_at"],
                "raw_user_info": profile["raw_user_info"],
                "raw_rating_history": profile["raw_rating_history"],
                "recent_activity": profile.get("recent_activity", []),
            },
        )
        return SnapshotValues(
            rating=stats.rating,
            solved_count=stats.solved_count,
            contest_count=stats.contest_count,
            metadata={
                "max_rating": stats.max_rating,
                "attempted_count": stats.attempted_count,
                "accepted_submission_count": stats.accepted_submission_count,
            },
        )
