import logging
from datetime import timedelta

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.datathons.models import KaggleCollectionRun, KaggleProfile
from apps.datathons.services.collection import collect_kaggle_profile
from apps.datathons.services.lifecycle import cancel_unlinked_collection, finalize_collection_failure
from apps.datathons.services.links import has_valid_profile_link
from apps.datathons.services.providers import CollectionError, configured_provider
from apps.datathons.services.scheduling import (
    cleanup_old_runs, dispatch_pending_runs, recover_stale_runs, retry_delay, schedule_due_profiles,
)
from apps.datathons.services.throttle import provider_slot


logger = logging.getLogger(__name__)


def process_collection_run(run_id):
    now = timezone.now()
    with transaction.atomic():
        run = KaggleCollectionRun.objects.select_for_update().select_related("profile").filter(pk=run_id).first()
        if run is None or run.status in ("succeeded", "failed", "cancelled"):
            return "terminal"
        if run.status == "running" and run.lease_expires_at and run.lease_expires_at > now:
            return "leased"
        profile = KaggleProfile.objects.select_for_update().get(pk=run.profile_id)
        if not has_valid_profile_link(profile):
            cancel_unlinked_collection(run, when=now)
            return "cancelled"
        if run.status == "retrying" and run.next_attempt_at and run.next_attempt_at > now:
            return "waiting"
        if run.attempt_count >= run.max_attempts:
            finalize_collection_failure(run, "attempts_exhausted", when=now)
            return "failed"
        run.status = KaggleCollectionRun.Status.RUNNING
        run.attempt_count += 1
        attempt = run.attempt_count
        run.started_at = now
        run.lease_expires_at = now + timedelta(seconds=max(1, settings.KAGGLE_RUN_LEASE_SECONDS))
        run.next_attempt_at = None
        run.last_dispatch_error_code = ""
        run.save()
        KaggleProfile.objects.filter(pk=run.profile_id).update(last_attempted_at=now)
    logger.info("kaggle.run_started", extra={"run_id": str(run_id), "profile_id": profile.pk,
                "provider": run.provider_name, "trigger": run.trigger, "attempt": attempt})
    unexpected = None
    try:
        provider_name, provider, policy = configured_provider()
        if provider_name != run.provider_name:
            raise CollectionError("provider_disabled")
        with provider_slot(provider_name, policy):
            collect_kaggle_profile(profile, provider=provider, policy=policy)
        error = None
    except CollectionError as exc:
        error = exc
    except SoftTimeLimitExceeded:
        error = CollectionError("provider_timeout", retryable=True)
    except Exception as exc:
        logger.exception("kaggle.unexpected_collection_error", extra={"run_id": str(run_id),
                         "profile_id": profile.pk, "provider": run.provider_name,
                         "trigger": run.trigger, "attempt": attempt})
        error = CollectionError("internal_error")
        unexpected = exc

    with transaction.atomic():
        current = KaggleCollectionRun.objects.select_for_update().get(pk=run_id)
        if current.status != KaggleCollectionRun.Status.RUNNING or current.attempt_count != attempt:
            return "superseded"
        finished = timezone.now()
        current.lease_expires_at = None
        if error is None:
            current.status = KaggleCollectionRun.Status.SUCCEEDED
            current.finished_at = finished
            current.next_attempt_at = None
            current.error_code = ""
            current.safe_error_message = ""
            KaggleProfile.objects.filter(pk=profile.pk).update(
                next_refresh_at=finished + timedelta(seconds=max(1, settings.KAGGLE_REFRESH_INTERVAL_SECONDS))
            )
            outcome = "succeeded"
        elif error.retryable and attempt < current.max_attempts:
            current.status = KaggleCollectionRun.Status.RETRYING
            current.next_attempt_at = finished + timedelta(seconds=retry_delay(attempt))
            current.next_dispatch_at = current.next_attempt_at
            current.dispatched_at = None
            current.error_code = error.code
            outcome = "retrying"
        elif error.code == "no_valid_link":
            cancel_unlinked_collection(current, when=finished)
            outcome = "cancelled"
        else:
            finalize_collection_failure(
                current, error.code, failed_collection=error.code != "provider_disabled", when=finished,
            )
            outcome = "failed"
        if outcome in ("succeeded", "retrying"):
            current.save()
    logger.info("kaggle.run_%s", outcome, extra={"run_id": str(run_id), "profile_id": profile.pk,
                "provider": run.provider_name, "trigger": run.trigger, "attempt": attempt,
                "duration_seconds": (timezone.now() - now).total_seconds(),
                "error_code": error.code if error else ""})
    if unexpected is not None:
        raise unexpected
    return outcome


@shared_task(name="apps.datathons.tasks.collect_kaggle_profile_task", ignore_result=True)
def collect_kaggle_profile_task(run_id):
    return process_collection_run(run_id)


@shared_task(name="apps.datathons.tasks.schedule_due_kaggle_profiles", ignore_result=True)
def schedule_due_kaggle_profiles():
    return schedule_due_profiles()


@shared_task(name="apps.datathons.tasks.dispatch_pending_kaggle_runs", ignore_result=True)
def dispatch_pending_kaggle_runs():
    return dispatch_pending_runs()


@shared_task(name="apps.datathons.tasks.recover_stale_kaggle_runs", ignore_result=True)
def recover_stale_kaggle_runs():
    return recover_stale_runs()


@shared_task(name="apps.datathons.tasks.cleanup_old_kaggle_collection_runs", ignore_result=True)
def cleanup_old_kaggle_collection_runs():
    return cleanup_old_runs()
