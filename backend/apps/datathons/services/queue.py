import logging
import math
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.datathons.models import ACTIVE_RUN_STATUSES, KaggleCollectionRun, KaggleProfile

from .providers import CollectionError, configured_provider


logger = logging.getLogger(__name__)
MAX_DISPATCH_ATTEMPTS = 5


class CooldownActive(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class QueueResult:
    run: KaggleCollectionRun
    deduplicated: bool


def _log(event: str, run: KaggleCollectionRun, **extra):
    logger.info("kaggle.%s", event, extra={"run_id": str(run.pk), "profile_id": run.profile_id,
                                      "provider": run.provider_name, "trigger": run.trigger, **extra})


@transaction.atomic
def request_kaggle_collection(profile: KaggleProfile, requested_by=None, trigger="manual") -> QueueResult:
    if trigger not in KaggleCollectionRun.Trigger.values:
        raise ValueError("Unsupported Kaggle collection trigger.")
    provider_name, _, policy = configured_provider()
    locked = KaggleProfile.objects.select_for_update().get(pk=profile.pk)
    try:
        locked.clean()
    except ValidationError as exc:
        raise CollectionError("invalid_identity") from exc
    active = KaggleCollectionRun.objects.filter(profile=locked, status__in=ACTIVE_RUN_STATUSES).first()
    if active:
        _log("request_deduplicated", active)
        return QueueResult(active, True)
    now = timezone.now()
    if trigger == KaggleCollectionRun.Trigger.MANUAL:
        last = KaggleCollectionRun.objects.filter(
            profile=locked, trigger=KaggleCollectionRun.Trigger.MANUAL,
        ).order_by("-queued_at").values_list("queued_at", flat=True).first()
        cooldown = max(0, settings.KAGGLE_MANUAL_SYNC_COOLDOWN_SECONDS)
        if last and last + timedelta(seconds=cooldown) > now:
            raise CooldownActive(math.ceil((last + timedelta(seconds=cooldown) - now).total_seconds()))
    run = KaggleCollectionRun.objects.create(
        profile=locked, requested_by=requested_by, trigger=trigger, provider_name=provider_name,
        max_attempts=max(1, min(settings.KAGGLE_MAX_ATTEMPTS, policy.max_attempts)),
        next_dispatch_at=now,
    )
    run.task_id = str(run.pk)
    run.save(update_fields=["task_id", "updated_at"])
    _log("run_created", run)
    transaction.on_commit(lambda run_id=run.pk: dispatch_kaggle_run(run_id))
    return QueueResult(run, False)


def dispatch_kaggle_run(run_id) -> bool:
    """Claim a durable intent before broker I/O; duplicate publishes are harmless."""
    now = timezone.now()
    with transaction.atomic():
        run = KaggleCollectionRun.objects.select_for_update().filter(pk=run_id).first()
        if not run or run.status not in (KaggleCollectionRun.Status.QUEUED, KaggleCollectionRun.Status.RETRYING):
            return False
        if run.dispatched_at or (run.next_dispatch_at and run.next_dispatch_at > now):
            return False
        if run.dispatch_attempts >= MAX_DISPATCH_ATTEMPTS:
            run.status = KaggleCollectionRun.Status.FAILED
            run.error_code = "dispatch_exhausted"
            run.finished_at = now
            run.next_dispatch_at = None
            run.save()
            KaggleProfile.objects.filter(pk=run.profile_id).update(
                next_refresh_at=now + timedelta(seconds=max(1, settings.KAGGLE_REFRESH_INTERVAL_SECONDS))
            )
            return False
        run.dispatch_attempts += 1
        run.next_dispatch_at = now + timedelta(seconds=max(30, settings.KAGGLE_STALE_RUN_GRACE_SECONDS))
        run.save(update_fields=["dispatch_attempts", "next_dispatch_at", "updated_at"])
        attempt = run.dispatch_attempts
        eta = run.next_attempt_at if run.status == KaggleCollectionRun.Status.RETRYING else None
    try:
        from apps.datathons.tasks import collect_kaggle_profile_task

        collect_kaggle_profile_task.apply_async(
            args=[str(run_id)], task_id=run.task_id, queue="kaggle", eta=eta,
            retry=False,
        )
    except Exception:
        logger.warning("kaggle.broker_dispatch_failed", extra={"run_id": str(run_id),
                       "profile_id": run.profile_id, "provider": run.provider_name,
                       "trigger": run.trigger, "attempt": attempt, "error_code": "broker_unavailable"})
        with transaction.atomic():
            current = KaggleCollectionRun.objects.select_for_update().get(pk=run_id)
            if current.status in (KaggleCollectionRun.Status.QUEUED, KaggleCollectionRun.Status.RETRYING):
                current.last_dispatch_error_code = "broker_unavailable"
                if attempt >= MAX_DISPATCH_ATTEMPTS:
                    current.status = KaggleCollectionRun.Status.FAILED
                    current.error_code = "broker_unavailable"
                    current.finished_at = timezone.now()
                    current.next_dispatch_at = None
                    KaggleProfile.objects.filter(pk=current.profile_id).update(
                        next_refresh_at=timezone.now() + timedelta(
                            seconds=max(1, settings.KAGGLE_REFRESH_INTERVAL_SECONDS)
                        )
                    )
                else:
                    delay = min(300, 2 ** attempt * 5)
                    current.next_dispatch_at = timezone.now() + timedelta(seconds=delay)
                current.save()
        return False
    KaggleCollectionRun.objects.filter(
        pk=run_id, status__in=[KaggleCollectionRun.Status.QUEUED, KaggleCollectionRun.Status.RETRYING],
    ).update(dispatched_at=timezone.now(), next_dispatch_at=None, last_dispatch_error_code="")
    _log("run_dispatched", run, attempt=attempt)
    return True
