from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.connectors.base.exceptions import ProviderSyncDisabledError
from apps.connectors.models import PlatformAccount


@dataclass(frozen=True)
class SnapshotValues:
    rating: int | None
    solved_count: int | None = None
    contest_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    source: str
    display_name: str

    @property
    @abstractmethod
    def sync_cooldown_seconds(self) -> int:
        raise NotImplementedError

    @property
    def is_enabled(self) -> bool:
        return True

    @property
    def cooldown_uses_attempts(self) -> bool:
        return False

    @abstractmethod
    def verify_handle(self, handle_or_slug: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def fetch_normalized_profile(self, handle_or_slug: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def persist_normalized_profile(
        self,
        platform_account: PlatformAccount,
        profile: dict[str, Any],
        synced_at: datetime,
    ) -> SnapshotValues | None:
        raise NotImplementedError

    def sync(
        self,
        platform_account: PlatformAccount,
        *,
        update_account_sync_metadata: bool = True,
    ) -> PlatformAccount:
        """Fetch outside a transaction, then atomically persist validated data."""
        if not self.is_enabled:
            raise ProviderSyncDisabledError(
                f"{self.display_name} synchronization is currently disabled."
            )
        profile = self.fetch_normalized_profile(platform_account.handle)
        synced_at = timezone.now()

        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
            )
            snapshot = self.persist_normalized_profile(
                locked_account,
                profile,
                synced_at,
            )
            locked_account.handle = profile["handle"]
            locked_account.profile_url = profile.get("profile_url", "")
            # Backwards compatibility: this legacy flag means handle validated,
            # never external-account ownership verified.
            locked_account.is_verified = True
            locked_account.handle_validated_at = synced_at
            update_fields = [
                "handle",
                "profile_url",
                "is_verified",
                "handle_validated_at",
                "updated_at",
            ]
            if update_account_sync_metadata:
                locked_account.last_sync_attempted_at = synced_at
                locked_account.last_synced_at = synced_at
                update_fields.extend(
                    ["last_sync_attempted_at", "last_synced_at"]
                )
            locked_account.save(update_fields=update_fields)

            if snapshot is not None:
                self._record_snapshot(locked_account, snapshot)

        return locked_account

    @staticmethod
    def _record_snapshot(
        platform_account: PlatformAccount,
        values: SnapshotValues,
    ) -> None:
        from apps.connectors.models import PlatformStatsSnapshot

        latest = platform_account.stats_snapshots.first()
        if (
            latest is not None
            and latest.rating == values.rating
            and latest.solved_count == values.solved_count
            and latest.contest_count == values.contest_count
        ):
            return

        PlatformStatsSnapshot.objects.create(
            platform_account=platform_account,
            rating=values.rating,
            solved_count=values.solved_count,
            contest_count=values.contest_count,
            metadata=values.metadata,
        )
