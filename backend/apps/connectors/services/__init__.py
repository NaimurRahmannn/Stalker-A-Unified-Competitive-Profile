import math

from django.utils import timezone

from apps.connectors.base.connector import BaseConnector
from apps.connectors.base.exceptions import UnsupportedSourceError
from apps.connectors.models import PlatformAccount
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
    connector = CONNECTOR_REGISTRY.get(platform_account.platform)
    return (
        connector is not None
        and connector.is_enabled
        and get_sync_cooldown_seconds(platform_account) == 0
    )
