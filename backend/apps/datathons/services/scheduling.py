import logging
import random
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apps.datathons.models import ACTIVE_RUN_STATUSES, KaggleCollectionRun, KaggleProfile, KaggleProfileLink
from apps.datathons.persistence import record_kaggle_collection_failure

from .providers import CollectionError, configured_provider
from .queue import dispatch_kaggle_run, request_kaggle_collection


logger = logging.getLogger(__name__)


def batch_size():
    return max(1, min(settings.KAGGLE_SCHEDULER_BATCH_SIZE, 1000))


def retry_delay(attempt: int) -> int:
    base = max(1, settings.KAGGLE_RETRY_BASE_DELAY_SECONDS)
    cap = max(base, settings.KAGGLE_RETRY_MAX_DELAY_SECONDS)
    exponential = min(cap, base * 2 ** max(0, attempt - 1))
    return min(cap, exponential + random.randint(0, max(1, exponential // 4)))


def schedule_due_profiles() -> int:
    if not settings.KAGGLE_SCHEDULED_SYNC_ENABLED:
        return 0
    try:
        configured_provider()
    except CollectionError:
        return 0
    now = timezone.now()
    linked = KaggleProfileLink.objects.filter(kaggle_profile_id=OuterRef("pk"))
    active = KaggleCollectionRun.objects.filter(profile_id=OuterRef("pk"), status__in=ACTIVE_RUN_STATUSES)
    ids = list(KaggleProfile.objects.annotate(
        has_link=Exists(linked), has_active=Exists(active),
    ).filter(has_link=True, has_active=False).filter(
        Q(next_refresh_at__lte=now) | Q(next_refresh_at__isnull=True)
    ).order_by("next_refresh_at", "pk").values_list("pk", flat=True)[:batch_size()])
    created = 0
    for profile_id in ids:
        try:
            result = request_kaggle_collection(
                KaggleProfile(pk=profile_id), trigger=KaggleCollectionRun.Trigger.SCHEDULED,
            )
            created += not result.deduplicated
        except CollectionError:
            break
    logger.info("kaggle.scheduler_batch", extra={"selected": len(ids), "created": created})
    return created


def dispatch_pending_runs() -> int:
    now = timezone.now()
    grace = timedelta(seconds=max(30, settings.KAGGLE_STALE_RUN_GRACE_SECONDS))
    candidates = list(KaggleCollectionRun.objects.filter(status__in=[
        KaggleCollectionRun.Status.QUEUED, KaggleCollectionRun.Status.RETRYING,
    ]).filter(
        Q(dispatched_at__isnull=True, next_dispatch_at__lte=now)
        | Q(status=KaggleCollectionRun.Status.QUEUED, dispatched_at__lt=now - grace)
        | Q(status=KaggleCollectionRun.Status.RETRYING, dispatched_at__lt=now - grace,
            next_attempt_at__lte=now)
    ).order_by("queued_at", "pk").values_list("pk", flat=True)[:batch_size()])
    dispatched = 0
    for run_id in candidates:
        with transaction.atomic():
            run = KaggleCollectionRun.objects.select_for_update().get(pk=run_id)
            if run.dispatched_at and run.dispatched_at < now - grace and (
                run.status == KaggleCollectionRun.Status.QUEUED or
                (run.status == KaggleCollectionRun.Status.RETRYING and run.next_attempt_at
                 and run.next_attempt_at <= now)
            ):
                run.dispatched_at = None
                run.next_dispatch_at = now
                run.save(update_fields=["dispatched_at", "next_dispatch_at", "updated_at"])
        dispatched += dispatch_kaggle_run(run_id)
    return dispatched


def recover_stale_runs() -> int:
    now = timezone.now()
    ids = list(KaggleCollectionRun.objects.filter(
        status=KaggleCollectionRun.Status.RUNNING, lease_expires_at__lt=now,
    ).order_by("lease_expires_at", "pk").values_list("pk", flat=True)[:batch_size()])
    recovered = 0
    for run_id in ids:
        with transaction.atomic():
            run = KaggleCollectionRun.objects.select_for_update().select_related("profile").get(pk=run_id)
            if run.status != KaggleCollectionRun.Status.RUNNING or not run.lease_expires_at or run.lease_expires_at >= timezone.now():
                continue
            run.lease_expires_at = None
            run.dispatched_at = None
            if run.attempt_count >= run.max_attempts:
                run.status = KaggleCollectionRun.Status.FAILED
                run.finished_at = timezone.now()
                run.next_attempt_at = None
                run.next_dispatch_at = None
                run.error_code = "worker_lost"
                record_kaggle_collection_failure(run.profile, "worker_lost")
                KaggleProfile.objects.filter(pk=run.profile_id).update(
                    next_refresh_at=timezone.now() + timedelta(seconds=max(1, settings.KAGGLE_REFRESH_INTERVAL_SECONDS))
                )
            else:
                run.status = KaggleCollectionRun.Status.RETRYING
                run.next_attempt_at = timezone.now() + timedelta(seconds=retry_delay(run.attempt_count))
                run.next_dispatch_at = timezone.now()
                run.error_code = "worker_lost"
                transaction.on_commit(lambda pk=run.pk: dispatch_kaggle_run(pk))
            run.save()
            recovered += 1
            logger.warning("kaggle.stale_run_recovered", extra={"run_id": str(run.pk),
                           "profile_id": run.profile_id, "provider": run.provider_name,
                           "trigger": run.trigger, "attempt": run.attempt_count,
                           "error_code": run.error_code})
    return recovered


def cleanup_old_runs() -> int:
    cutoff = timezone.now() - timedelta(days=max(1, settings.KAGGLE_COLLECTION_RUN_RETENTION_DAYS))
    ids = list(KaggleCollectionRun.objects.filter(
        status__in=[KaggleCollectionRun.Status.SUCCEEDED, KaggleCollectionRun.Status.FAILED,
                    KaggleCollectionRun.Status.CANCELLED], finished_at__lt=cutoff,
    ).order_by("finished_at", "pk").values_list("pk", flat=True)[:batch_size()])
    if ids:
        KaggleCollectionRun.objects.filter(pk__in=ids).delete()
    return len(ids)
