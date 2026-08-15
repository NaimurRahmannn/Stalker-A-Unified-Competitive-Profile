from datetime import datetime
from typing import Any

from django.conf import settings

from apps.connectors.base.connector import BaseConnector, SnapshotValues
from apps.connectors.base.utils import build_atcoder_profile_url
from apps.connectors.models import AtCoderStats, PlatformAccount, PlatformRatingEvent
from apps.connectors.providers.atcoder.client import (
    AtCoderHistoryClient,
    normalize_atcoder_handle,
)
from apps.connectors.providers.atcoder.mapper import (
    derive_algorithm_stats,
    normalize_algorithm_rating_history,
)


class AtCoderConnector(BaseConnector):
    source = "atcoder"
    display_name = "AtCoder"

    def __init__(self, client: AtCoderHistoryClient | None = None):
        self.client = client or AtCoderHistoryClient()

    @property
    def sync_cooldown_seconds(self) -> int:
        return settings.ATCODER_SYNC_COOLDOWN_SECONDS

    @property
    def is_enabled(self) -> bool:
        return settings.ATCODER_HISTORY_SYNC_ENABLED

    @property
    def cooldown_uses_attempts(self) -> bool:
        return True

    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_atcoder_handle(handle_or_slug)
        self.client.get_algorithm_rating_history(handle)
        return {"handle": handle}

    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        handle = normalize_atcoder_handle(handle_or_slug)
        raw_history = self.client.get_algorithm_rating_history(handle)
        events = normalize_algorithm_rating_history(raw_history)
        stats = derive_algorithm_stats(events)
        return {
            "handle": handle,
            "profile_url": build_atcoder_profile_url(handle),
            "discipline": PlatformRatingEvent.Discipline.ALGORITHM,
            "rating_events": events,
            **stats,
        }

    def persist_normalized_profile(
        self,
        platform_account: PlatformAccount,
        profile: dict[str, Any],
        synced_at: datetime,
    ) -> SnapshotValues:
        discipline = profile["discipline"]
        for event in profile["rating_events"]:
            PlatformRatingEvent.objects.update_or_create(
                platform_account=platform_account,
                discipline=discipline,
                external_contest_id=event["external_contest_id"],
                defaults={
                    "contest_name": event["contest_name"],
                    "rank": event["rank"],
                    "performance": event["performance"],
                    "inner_performance": event["inner_performance"],
                    "old_rating": event["old_rating"],
                    "new_rating": event["new_rating"],
                    "rating_change": event["rating_change"],
                    "is_rated": event["is_rated"],
                    "occurred_at": event["occurred_at"],
                    "metadata": event["metadata"],
                },
            )

        stats, _ = AtCoderStats.objects.update_or_create(
            platform_account=platform_account,
            defaults={
                "discipline": discipline,
                "current_rating": profile["current_rating"],
                "max_rating": profile["max_rating"],
                "rated_contest_count": profile["rated_contest_count"],
                "last_rated_at": profile["last_rated_at"],
                "last_performance": profile["last_performance"],
                "rating_data_updated_at": synced_at,
            },
        )
        return SnapshotValues(
            rating=stats.current_rating,
            contest_count=stats.rated_contest_count,
            metadata={
                "discipline": discipline,
                "max_rating": stats.max_rating,
                "last_performance": stats.last_performance,
            },
        )
