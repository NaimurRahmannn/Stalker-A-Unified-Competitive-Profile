import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
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

logger = logging.getLogger(__name__)

# A RUNNING state older than this is considered stale and will not block a
# new sync.  Generous enough for cold-start alfa wake-ups (~50 s).
STALE_RUNNING_THRESHOLD = timedelta(minutes=5)


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
    SYNC_ALREADY_RUNNING = "sync_already_running"


@dataclass(frozen=True)
class LeetCodeSyncResult:
    status: str
    attempted_at: datetime
    successful_at: datetime | None
    updated: bool
    using_cached_data: bool
    error_code: LeetCodeSyncErrorCode | None = None
    duration_seconds: float | None = None
    consecutive_failure_count: int = 0


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
        wall_start = time.monotonic()

        # Concurrency guard — prevent overlapping syncs for the same account.
        blocked = self._check_already_running(platform_account, attempted_at)
        if blocked is not None:
            return blocked

        self._mark_running(platform_account, attempted_at)

        logger.info(
            "LeetCode sync started",
            extra={
                "provider": "leetcode",
                "platform_account_id": platform_account.pk,
                "handle": platform_account.handle,
            },
        )

        try:
            if not self.connector.is_enabled:
                raise ProviderSyncDisabledError(
                    "LeetCode synchronization is currently disabled."
                )
            profile = self.connector.fetch_normalized_profile(
                platform_account.handle
            )
        except ConnectorError as exc:
            duration = time.monotonic() - wall_start
            result = self._mark_failed(platform_account, attempted_at, exc)
            logger.warning(
                "LeetCode sync failed",
                extra={
                    "provider": "leetcode",
                    "platform_account_id": platform_account.pk,
                    "handle": platform_account.handle,
                    "error_code": (
                        result.error_code.value if result.error_code else None
                    ),
                    "duration_seconds": round(duration, 3),
                    "using_cached_data": result.using_cached_data,
                    "consecutive_failure_count": result.consecutive_failure_count,
                },
            )
            return result
        except Exception:
            # Catch-all: unexpected exceptions must not leave the sync stuck
            # in RUNNING state.
            duration = time.monotonic() - wall_start
            logger.exception(
                "LeetCode sync encountered unexpected error",
                extra={
                    "provider": "leetcode",
                    "platform_account_id": platform_account.pk,
                    "handle": platform_account.handle,
                    "duration_seconds": round(duration, 3),
                },
            )
            return self._mark_failed_unexpected(
                platform_account, attempted_at
            )

        duration = time.monotonic() - wall_start
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
            state.consecutive_failure_count = 0
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "last_successful_at",
                    "failure_reason",
                    "consecutive_failure_count",
                    "updated_at",
                ]
            )

        logger.info(
            "LeetCode sync completed",
            extra={
                "provider": "leetcode",
                "platform_account_id": platform_account.pk,
                "handle": platform_account.handle,
                "status": "success",
                "duration_seconds": round(duration, 3),
                "updated": True,
            },
        )

        return LeetCodeSyncResult(
            status=LeetCodeSyncState.Status.SUCCESS,
            attempted_at=attempted_at,
            successful_at=successful_at,
            updated=True,
            using_cached_data=False,
            duration_seconds=round(duration, 3),
            consecutive_failure_count=0,
        )

    @staticmethod
    def _validate_account(platform_account: PlatformAccount) -> None:
        if platform_account.pk is None:
            raise ValueError("LeetCode synchronization requires a saved account.")
        if platform_account.platform != PlatformAccount.Platform.LEETCODE:
            raise ValueError("LeetCode synchronization requires a LeetCode account.")

    def _check_already_running(
        self,
        platform_account: PlatformAccount,
        now: datetime,
    ) -> LeetCodeSyncResult | None:
        """Return an early result if another sync is actively running."""
        try:
            state = LeetCodeSyncState.objects.get(
                platform_account=platform_account
            )
        except LeetCodeSyncState.DoesNotExist:
            return None

        if state.status != LeetCodeSyncState.Status.RUNNING:
            return None

        # Allow recovery from truly stale RUNNING states (e.g. crash).
        if (
            state.last_attempted_at is not None
            and (now - state.last_attempted_at) > STALE_RUNNING_THRESHOLD
        ):
            logger.warning(
                "LeetCode sync recovering stale RUNNING state",
                extra={
                    "provider": "leetcode",
                    "platform_account_id": platform_account.pk,
                    "stale_since": state.last_attempted_at.isoformat(),
                },
            )
            return None

        logger.info(
            "LeetCode sync skipped — already running",
            extra={
                "provider": "leetcode",
                "platform_account_id": platform_account.pk,
            },
        )
        using_cached = LeetCodeStats.objects.filter(
            platform_account=platform_account
        ).exists()
        return LeetCodeSyncResult(
            status=LeetCodeSyncState.Status.RUNNING,
            attempted_at=now,
            successful_at=state.last_successful_at,
            updated=False,
            using_cached_data=using_cached,
            error_code=LeetCodeSyncErrorCode.SYNC_ALREADY_RUNNING,
            consecutive_failure_count=state.consecutive_failure_count,
        )

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
            state.consecutive_failure_count += 1
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "failure_reason",
                    "consecutive_failure_count",
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
            consecutive_failure_count=state.consecutive_failure_count,
        )

    def _mark_failed_unexpected(
        self,
        platform_account: PlatformAccount,
        attempted_at: datetime,
    ) -> LeetCodeSyncResult:
        """Mark failed from an unexpected non-ConnectorError exception."""
        with transaction.atomic():
            locked_account = PlatformAccount.objects.select_for_update().get(
                pk=platform_account.pk,
                user_id=platform_account.user_id,
            )
            state = LeetCodeSyncState.objects.select_for_update().get(
                platform_account=locked_account
            )
            state.status = LeetCodeSyncState.Status.FAILED
            state.last_attempted_at = attempted_at
            state.failure_reason = LeetCodeSyncErrorCode.PROVIDER_ERROR.value
            state.consecutive_failure_count += 1
            state.save(
                update_fields=[
                    "status",
                    "last_attempted_at",
                    "failure_reason",
                    "consecutive_failure_count",
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
            error_code=LeetCodeSyncErrorCode.PROVIDER_ERROR,
            consecutive_failure_count=state.consecutive_failure_count,
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

