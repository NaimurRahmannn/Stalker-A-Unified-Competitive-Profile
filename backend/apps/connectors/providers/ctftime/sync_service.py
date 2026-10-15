import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.connectors.base.exceptions import (
    ConnectorError,
    ExternalServiceError,
    InvalidExternalAccountError,
    ProviderAccessDeniedError,
    ProviderRateLimitError,
    ProviderSchemaError,
    ProviderSyncDisabledError,
    ProviderTimeoutError,
)
from apps.connectors.models import CTFtimeSyncState, PlatformAccount
from apps.connectors.providers.ctftime.adapter import CTFtimeAdapter
from apps.connectors.providers.ctftime.client import CTFtimeClient
from apps.connectors.providers.ctftime.domain import CTFSyncData
from apps.connectors.providers.ctftime.exceptions import (
    CTFtimeConfigurationError,
    CTFtimeSyncAlreadyRunningError,
)
from apps.connectors.providers.ctftime.persistence import CTFtimePersistenceMapper
from apps.connectors.providers.ctftime.provider import CTFProvider

logger = logging.getLogger(__name__)
STALE_RUNNING_THRESHOLD = timedelta(minutes=5)


class CTFtimeSyncService:
    """Fetch one team payload and keep its account, data and sync state consistent."""

    def __init__(self, provider: CTFProvider | None = None):
        self.provider = provider

    @staticmethod
    def is_enabled() -> bool:
        return settings.CTFTIME_SYNC_ENABLED

    def sync(self, account: PlatformAccount) -> PlatformAccount:
        if account.pk is None or account.platform != PlatformAccount.Platform.CTFTIME:
            raise ValueError("CTFtime sync requires a saved CTFtime account.")
        if not settings.CTFTIME_SYNC_ENABLED:
            raise ProviderSyncDisabledError("CTFtime synchronization is disabled.")

        attempted_at = timezone.now()
        self._mark_running(account, attempted_at)
        try:
            provider = self.provider or CTFtimeAdapter(
                CTFtimeClient(
                    base_url=settings.CTFTIME_BASE_URL,
                    timeout=settings.CTFTIME_TIMEOUT_SECONDS,
                )
            )
            data = provider.get_sync_data(account.handle)
            if data.profile.team_id != account.handle:
                raise ProviderSchemaError("CTFtime returned a different team ID.")
            return self._mark_success(account, data, attempted_at)
        except ConnectorError as exc:
            self._mark_failed(account, attempted_at, self._failure_reason(exc))
            raise
        except Exception as exc:
            logger.exception(
                "CTFtime sync failed unexpectedly",
                extra={"platform_account_id": account.pk},
            )
            self._mark_failed(account, attempted_at, "sync_error")
            raise ExternalServiceError("CTFtime synchronization failed.") from exc

    @staticmethod
    def _mark_running(account: PlatformAccount, attempted_at) -> None:
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(pk=account.pk)
            if (
                locked_account.platform != PlatformAccount.Platform.CTFTIME
                or locked_account.handle != account.handle
            ):
                raise InvalidExternalAccountError("The CTFtime account changed during sync.")
            state, _ = CTFtimeSyncState.objects.select_for_update().get_or_create(
                platform_account=locked_account
            )
            if (
                state.status == CTFtimeSyncState.Status.RUNNING
                and state.last_attempted_at is not None
                and attempted_at - state.last_attempted_at < STALE_RUNNING_THRESHOLD
            ):
                raise CTFtimeSyncAlreadyRunningError("A CTFtime sync is already in progress.")
            locked_account.last_sync_attempted_at = attempted_at
            locked_account.save(update_fields=["last_sync_attempted_at", "updated_at"])
            state.status = CTFtimeSyncState.Status.RUNNING
            state.last_attempted_at = attempted_at
            state.failure_reason = ""
            state.save(
                update_fields=["status", "last_attempted_at", "failure_reason", "updated_at"]
            )

    @staticmethod
    def _mark_success(
        account: PlatformAccount, data: CTFSyncData, attempted_at
    ) -> PlatformAccount:
        successful_at = timezone.now()
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(pk=account.pk)
            if (
                locked_account.platform != PlatformAccount.Platform.CTFTIME
                or locked_account.handle != account.handle
            ):
                raise InvalidExternalAccountError("The CTFtime account changed during sync.")
            state = CTFtimeSyncState.objects.select_for_update().get(
                platform_account=locked_account
            )
            if (
                state.status != CTFtimeSyncState.Status.RUNNING
                or state.last_attempted_at != attempted_at
            ):
                raise CTFtimeSyncAlreadyRunningError(
                    "A newer CTFtime sync has replaced this attempt."
                )
            CTFtimePersistenceMapper.persist_sync_data(locked_account, data)
            locked_account.profile_url = f"https://ctftime.org/team/{data.profile.team_id}"
            locked_account.is_verified = True
            locked_account.handle_validated_at = successful_at
            locked_account.last_synced_at = successful_at
            locked_account.save(
                update_fields=[
                    "profile_url",
                    "is_verified",
                    "handle_validated_at",
                    "last_synced_at",
                    "updated_at",
                ]
            )
            state.status = CTFtimeSyncState.Status.SUCCESS
            state.last_successful_at = successful_at
            state.failure_reason = ""
            state.consecutive_failure_count = 0
            state.save(
                update_fields=[
                    "status",
                    "last_successful_at",
                    "failure_reason",
                    "consecutive_failure_count",
                    "updated_at",
                ]
            )
        return locked_account

    @staticmethod
    def _mark_failed(account: PlatformAccount, attempted_at, reason: str) -> None:
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(pk=account.pk)
            if (
                locked_account.platform != PlatformAccount.Platform.CTFTIME
                or locked_account.handle != account.handle
            ):
                return
            state = (
                CTFtimeSyncState.objects.select_for_update()
                .filter(platform_account=locked_account)
                .first()
            )
            if state is None or state.last_attempted_at != attempted_at:
                return
            if reason == "invalid_team_id":
                locked_account.is_verified = False
                locked_account.handle_validated_at = None
                locked_account.save(
                    update_fields=["is_verified", "handle_validated_at", "updated_at"]
                )
            state.status = CTFtimeSyncState.Status.FAILED
            state.failure_reason = reason
            state.consecutive_failure_count += 1
            state.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "consecutive_failure_count",
                    "updated_at",
                ]
            )

    @staticmethod
    def _failure_reason(error: ConnectorError) -> str:
        if isinstance(error, CTFtimeConfigurationError):
            return "configuration_error"
        if isinstance(error, InvalidExternalAccountError):
            return "invalid_team_id"
        if isinstance(error, ProviderRateLimitError):
            return "rate_limited"
        if isinstance(error, ProviderTimeoutError):
            return "timeout"
        if isinstance(error, ProviderAccessDeniedError):
            return "access_denied"
        if isinstance(error, ProviderSchemaError):
            return "invalid_response"
        return "provider_unavailable"
