from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

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
from apps.connectors.models import LeetCodeStats, LeetCodeSyncState, PlatformAccount
from apps.connectors.providers.leetcode.connector import LeetCodeConnector
from apps.connectors.providers.leetcode.exceptions import LeetCodeConfigurationError
from apps.connectors.providers.leetcode.provider import LeetCodeProvider


class LeetCodeSyncErrorCode(StrEnum):
    INVALID_USERNAME = "invalid_username"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    RATE_LIMITED = "rate_limited"
    ACCESS_DENIED = "access_denied"
    CONFIGURATION_ERROR = "configuration_error"
    PROVIDER_DISABLED = "provider_disabled"
    PROVIDER_ERROR = "provider_error"


@dataclass(frozen=True)
class LeetCodeSyncResult:
    status: str
    attempted_at: datetime
    successful_at: datetime | None
    updated: bool
    using_cached_data: bool
    error_code: LeetCodeSyncErrorCode | None = None


class LeetCodeSyncService:
    """Synchronous boundary that can later be invoked by a background worker."""

    def __init__(
        self,
        provider: LeetCodeProvider | None = None,
        connector: LeetCodeConnector | None = None,
    ):
        if provider is not None and connector is not None:
            raise ValueError("Pass either provider or connector, not both.")
        self.connector = connector or LeetCodeConnector(provider=provider)

    def sync(self, platform_account: PlatformAccount) -> LeetCodeSyncResult:
        self._validate_account(platform_account)
        attempted_at = timezone.now()
        self._mark_running(platform_account, attempted_at)

        try:
            if not self.connector.is_enabled:
                raise ProviderSyncDisabledError(
                    "LeetCode synchronization is currently disabled."
                )
            profile = self.connector.fetch_normalized_profile(
                platform_account.handle
            )
        except ConnectorError as exc:
            return self._mark_failed(platform_account, attempted_at, exc)

        successful_at = timezone.now()
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
            )
            state = LeetCodeSyncState.objects.select_for_update().get(
                platform_account=locked_account
            )
            snapshot = self.connector.persist_normalized_profile(
                locked_account,
                profile,
                successful_at,
            )
            locked_account.handle = profile["handle"]
            locked_account.profile_url = profile["profile_url"]
            locked_account.is_verified = True
            locked_account.handle_validated_at = successful_at
            locked_account.last_sync_attempted_at = attempted_at
            locked_account.last_synced_at = successful_at
            locked_account.save(
                update_fields=[
                    "handle",
                    "profile_url",
                    "is_verified",
                    "handle_validated_at",
                    "last_sync_attempted_at",
                    "last_synced_at",
                    "updated_at",
                ]
            )
            self.connector.record_snapshot(locked_account, snapshot)
            state.status = LeetCodeSyncState.Status.SUCCESS
            state.last_attempted_at = attempted_at
            state.last_successful_at = successful_at
            state.failure_reason = ""
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "last_successful_at",
                    "failure_reason",
                    "updated_at",
                ]
            )

        return LeetCodeSyncResult(
            status=LeetCodeSyncState.Status.SUCCESS,
            attempted_at=attempted_at,
            successful_at=successful_at,
            updated=True,
            using_cached_data=False,
        )

    @staticmethod
    def _validate_account(platform_account: PlatformAccount) -> None:
        if platform_account.pk is None:
            raise ValueError("LeetCode synchronization requires a saved account.")
        if platform_account.platform != PlatformAccount.Platform.LEETCODE:
            raise ValueError("LeetCode synchronization requires a LeetCode account.")

    @staticmethod
    def _mark_running(
        platform_account: PlatformAccount,
        attempted_at: datetime,
    ) -> None:
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
            )
            state, _ = LeetCodeSyncState.objects.select_for_update().get_or_create(
                platform_account=locked_account
            )
            locked_account.last_sync_attempted_at = attempted_at
            locked_account.save(
                update_fields=["last_sync_attempted_at", "updated_at"]
            )
            state.status = LeetCodeSyncState.Status.RUNNING
            state.last_attempted_at = attempted_at
            state.failure_reason = ""
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "failure_reason",
                    "updated_at",
                ]
            )

    def _mark_failed(
        self,
        platform_account: PlatformAccount,
        attempted_at: datetime,
        error: ConnectorError,
    ) -> LeetCodeSyncResult:
        error_code = self._error_code(error)
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
            )
            state = LeetCodeSyncState.objects.select_for_update().get(
                platform_account=locked_account
            )
            if error_code == LeetCodeSyncErrorCode.INVALID_USERNAME:
                locked_account.is_verified = False
                locked_account.handle_validated_at = None
                locked_account.save(
                    update_fields=[
                        "is_verified",
                        "handle_validated_at",
                        "updated_at",
                    ]
                )
            state.status = LeetCodeSyncState.Status.FAILED
            state.last_attempted_at = attempted_at
            state.failure_reason = error_code.value
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "failure_reason",
                    "updated_at",
                ]
            )
            using_cached_data = LeetCodeStats.objects.filter(
                platform_account=locked_account
            ).exists()

        return LeetCodeSyncResult(
            status=LeetCodeSyncState.Status.FAILED,
            attempted_at=attempted_at,
            successful_at=state.last_successful_at,
            updated=False,
            using_cached_data=using_cached_data,
            error_code=error_code,
        )

    @staticmethod
    def _error_code(error: ConnectorError) -> LeetCodeSyncErrorCode:
        if isinstance(error, InvalidExternalAccountError):
            return LeetCodeSyncErrorCode.INVALID_USERNAME
        if isinstance(error, ProviderTimeoutError):
            return LeetCodeSyncErrorCode.TIMEOUT
        if isinstance(error, ProviderSchemaError):
            return LeetCodeSyncErrorCode.INVALID_RESPONSE
        if isinstance(error, ProviderRateLimitError):
            return LeetCodeSyncErrorCode.RATE_LIMITED
        if isinstance(error, ProviderAccessDeniedError):
            return LeetCodeSyncErrorCode.ACCESS_DENIED
        if isinstance(error, LeetCodeConfigurationError):
            return LeetCodeSyncErrorCode.CONFIGURATION_ERROR
        if isinstance(error, ProviderSyncDisabledError):
            return LeetCodeSyncErrorCode.PROVIDER_DISABLED
        if isinstance(error, ExternalServiceError):
            return LeetCodeSyncErrorCode.PROVIDER_UNAVAILABLE
        return LeetCodeSyncErrorCode.PROVIDER_ERROR
