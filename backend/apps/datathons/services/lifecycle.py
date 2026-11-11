from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.datathons.models import KaggleCollectionRun, KaggleProfile
from apps.datathons.persistence import record_kaggle_collection_failure


def finalize_collection_failure(run, code: str, *, failed_collection: bool = True, when=None) -> None:
    """Finalize an already locked run inside the caller's transaction."""
    when = when or timezone.now()
    run.status = KaggleCollectionRun.Status.FAILED
    run.error_code = code
    run.finished_at = when
    run.lease_expires_at = None
    run.next_attempt_at = None
    run.next_dispatch_at = None
    run.dispatched_at = None
    if failed_collection:
        record_kaggle_collection_failure(run.profile, code)
    KaggleProfile.objects.filter(pk=run.profile_id).update(
        next_refresh_at=when + timedelta(seconds=max(1, settings.KAGGLE_REFRESH_INTERVAL_SECONDS))
    )
    run.save()


def cancel_unlinked_collection(run, *, when=None) -> None:
    """Cancel without changing the profile's last collection outcome."""
    run.status = KaggleCollectionRun.Status.CANCELLED
    run.error_code = "no_valid_link"
    run.finished_at = when or timezone.now()
    run.lease_expires_at = None
    run.next_attempt_at = None
    run.next_dispatch_at = None
    run.dispatched_at = None
    KaggleProfile.objects.filter(pk=run.profile_id).update(next_refresh_at=None)
    run.save()
