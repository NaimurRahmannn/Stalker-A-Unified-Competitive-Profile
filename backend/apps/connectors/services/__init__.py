import math

from django.conf import settings
from django.utils import timezone

from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.models import AtCoderSyncState, PlatformAccount
from apps.connectors.providers.atcoder.connector import AtCoderConnector
from apps.connectors.providers.codeforces.connector import CodeforcesConnector

CONNECTOR_REGISTRY: dict[str, BaseConnector] = {
    PlatformAccount.Platform.CODEFORCES: CodeforcesConnector(),
    PlatformAccount.Platform.ATCODER: AtCoderConnector(),
}


def get_connector(source: str) -> BaseConnector:
    connector = CONNECTOR_REGISTRY.get(source)
    if connector is None:
        raise UnsupportedSourceError(f"Unsupported source: {source}")
    return connector


def get_sync_cooldown_seconds(platform_account: PlatformAccount) -> int:
    if platform_account.platform == PlatformAccount.Platform.ATCODER:
        return get_atcoder_sync_cooldown_seconds(platform_account)
    connector = CONNECTOR_REGISTRY.get(platform_account.platform)
    if connector is None:
        return 0

    cooldown_reference = (
        platform_account.last_sync_attempted_at or platform_account.last_synced_at
        if connector.cooldown_uses_attempts
        else platform_account.last_synced_at
    )
    if cooldown_reference is None:
        return 0

    elapsed_seconds = (
        timezone.now() - cooldown_reference
    ).total_seconds()
    remaining_seconds = connector.sync_cooldown_seconds - elapsed_seconds

    if remaining_seconds <= 0:
        return 0

    return math.ceil(remaining_seconds)


def can_sync_platform_account(platform_account: PlatformAccount) -> bool:
    if platform_account.platform == PlatformAccount.Platform.ATCODER:
        if not (
            settings.ATCODER_HISTORY_SYNC_ENABLED
            or settings.ATCODER_PROBLEMS_SYNC_ENABLED
        ):
            return False
        return get_atcoder_sync_cooldown_seconds(platform_account) == 0
    connector = CONNECTOR_REGISTRY.get(platform_account.platform)
    return (
        connector is not None
        and connector.is_enabled
        and get_sync_cooldown_seconds(platform_account) == 0
    )


def get_atcoder_sync_cooldown_seconds(
    platform_account: PlatformAccount,
) -> int:
    state = AtCoderSyncState.objects.filter(
        platform_account=platform_account
    ).first()
    if state is None:
        return 0

    source_policies = []
    if settings.ATCODER_HISTORY_SYNC_ENABLED:
        source_policies.append(
            (
                state.rating_sync_attempted_at,
                settings.ATCODER_HISTORY_SYNC_COOLDOWN_SECONDS,
            )
        )
    if settings.ATCODER_PROBLEMS_SYNC_ENABLED:
        source_policies.append(
            (
                state.submission_sync_attempted_at,
                settings.ATCODER_PROBLEMS_SYNC_COOLDOWN_SECONDS,
            )
        )
    if not source_policies:
        return 0

    now = timezone.now()
    remaining = []
    for attempted_at, cooldown in source_policies:
        if attempted_at is None:
            return 0
        seconds = cooldown - (now - attempted_at).total_seconds()
        if seconds <= 0:
            return 0
        remaining.append(math.ceil(seconds))
    return min(remaining)
