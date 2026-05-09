from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.accounts.models import ExternalAccount
from apps.connectors.base.exceptions import (
    ExternalServiceError,
    InvalidExternalAccountError,
    UnsupportedSourceError,
)
from apps.connectors.services import get_connector
from apps.dashboard.models import ProfileSnapshot


class ExternalProviderError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "External provider request failed."


def _save_snapshot(external_account: ExternalAccount, normalized_profile: dict[str, Any]) -> ProfileSnapshot:
    return ProfileSnapshot.objects.create(
        external_account=external_account,
        display_name=normalized_profile.get("display_name"),
        headline_rank_title=normalized_profile.get("headline_rank_title"),
        rating=normalized_profile.get("rating"),
        highest_rating=normalized_profile.get("highest_rating"),
        contests_count=normalized_profile.get("contests_count"),
        solved_count=normalized_profile.get("solved_count"),
        avatar_url=normalized_profile.get("avatar_url"),
        metadata_json=normalized_profile.get("metadata_json") or {},
    )


def _mark_account_failed(account: ExternalAccount, error_message: str, is_invalid: bool) -> None:
    account.sync_status = ExternalAccount.SyncStatus.FAILED
    account.last_error = error_message
    account.last_synced_at = timezone.now()
    if is_invalid:
        account.verification_status = ExternalAccount.VerificationStatus.INVALID
    account.save(
        update_fields=[
            "sync_status",
            "last_error",
            "last_synced_at",
            "verification_status",
            "updated_at",
        ],
    )


@transaction.atomic
def connect_external_account(user, source: str, handle_or_slug: str) -> tuple[ExternalAccount, ProfileSnapshot]:
    existing_account = ExternalAccount.objects.filter(user=user, source=source).first()

    try:
        connector = get_connector(source)
    except UnsupportedSourceError as exc:
        raise ValidationError({"source": [str(exc)]}) from exc

    try:
        normalized_profile = connector.fetch_normalized_profile(handle_or_slug)
    except InvalidExternalAccountError as exc:
        if existing_account is not None:
            _mark_account_failed(existing_account, str(exc), is_invalid=True)
        raise ValidationError({"handle_or_slug": [str(exc)]}) from exc
    except ExternalServiceError as exc:
        if existing_account is not None:
            _mark_account_failed(existing_account, str(exc), is_invalid=False)
        raise ExternalProviderError(detail=str(exc)) from exc

    account_defaults = {
        "handle_or_slug": normalized_profile["handle_or_slug"],
        "profile_url": normalized_profile.get("profile_url", ""),
        "verification_status": ExternalAccount.VerificationStatus.VERIFIED,
        "sync_status": ExternalAccount.SyncStatus.SUCCESS,
        "last_synced_at": timezone.now(),
        "last_error": "",
        "is_active": True,
    }

    external_account, _ = ExternalAccount.objects.update_or_create(
        user=user,
        source=source,
        defaults=account_defaults,
    )
    snapshot = _save_snapshot(external_account, normalized_profile)
    return external_account, snapshot


@transaction.atomic
def sync_external_account(external_account: ExternalAccount) -> ProfileSnapshot:
    try:
        connector = get_connector(external_account.source)
        normalized_profile = connector.fetch_normalized_profile(external_account.handle_or_slug)
    except UnsupportedSourceError as exc:
        raise ValidationError({"source": [str(exc)]}) from exc
    except InvalidExternalAccountError as exc:
        _mark_account_failed(external_account, str(exc), is_invalid=True)
        raise ValidationError({"handle_or_slug": [str(exc)]}) from exc
    except ExternalServiceError as exc:
        _mark_account_failed(external_account, str(exc), is_invalid=False)
        raise ExternalProviderError(detail=str(exc)) from exc

    external_account.handle_or_slug = normalized_profile["handle_or_slug"]
    external_account.profile_url = normalized_profile.get("profile_url", "")
    external_account.verification_status = ExternalAccount.VerificationStatus.VERIFIED
    external_account.sync_status = ExternalAccount.SyncStatus.SUCCESS
    external_account.last_synced_at = timezone.now()
    external_account.last_error = ""
    external_account.save(
        update_fields=[
            "handle_or_slug",
            "profile_url",
            "verification_status",
            "sync_status",
            "last_synced_at",
            "last_error",
            "updated_at",
        ],
    )

    return _save_snapshot(external_account, normalized_profile)
