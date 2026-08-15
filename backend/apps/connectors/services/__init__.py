import math

from django.utils import timezone

from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.models import CodeforcesStats, PlatformAccount, PlatformStatsSnapshot
from apps.connectors.providers.codeforces.connector import CodeforcesConnector


SYNC_COOLDOWN_SECONDS = 60

CONNECTOR_REGISTRY: dict[str, BaseConnector] = {
    PlatformAccount.Platform.CODEFORCES: CodeforcesConnector(),
}


def get_connector(source: str) -> BaseConnector:
    connector = CONNECTOR_REGISTRY.get(source)
    if connector is None:
        raise UnsupportedSourceError(f"Unsupported source: {source}")
    return connector


def get_sync_cooldown_seconds(platform_account: PlatformAccount) -> int:
    if platform_account.last_synced_at is None:
        return 0

    elapsed_seconds = (
        timezone.now() - platform_account.last_synced_at
    ).total_seconds()
    remaining_seconds = SYNC_COOLDOWN_SECONDS - elapsed_seconds

    if remaining_seconds <= 0:
        return 0

    return math.ceil(remaining_seconds)


def can_sync_platform_account(platform_account: PlatformAccount) -> bool:
    return get_sync_cooldown_seconds(platform_account) == 0


def record_platform_stats_snapshot(
    platform_account: PlatformAccount,
    stats: CodeforcesStats,
) -> PlatformStatsSnapshot:
    latest = platform_account.stats_snapshots.first()
    if (
        latest is not None
        and latest.rating == stats.rating
        and latest.solved_count == stats.solved_count
        and latest.contest_count == stats.contest_count
    ):
        return latest

    return PlatformStatsSnapshot.objects.create(
        platform_account=platform_account,
        rating=stats.rating,
        solved_count=stats.solved_count,
        contest_count=stats.contest_count,
        metadata={
            "max_rating": stats.max_rating,
            "attempted_count": stats.attempted_count,
            "accepted_submission_count": stats.accepted_submission_count,
        },
    )
