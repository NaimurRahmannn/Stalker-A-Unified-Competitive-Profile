import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.connectors.models import PlatformAccount

COLLECTION_STATUSES = ("not_collected", "success", "failed")
KAGGLE_TRACKS = ("competitions", "code", "datasets")
RANK_STATUSES = ("unknown", "ranked", "unranked")
ACTIVE_RUN_STATUSES = ("queued", "running", "retrying")
RUN_STATUSES = ACTIVE_RUN_STATUSES + ("succeeded", "failed", "cancelled")


class KaggleProfile(models.Model):
    class CollectionStatus(models.TextChoices):
        NOT_COLLECTED = "not_collected", "Not collected"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    username = models.CharField(max_length=50)
    normalized_username = models.CharField(max_length=50, unique=True)
    profile_url = models.URLField(max_length=200)
    collection_status = models.CharField(
        max_length=20, choices=CollectionStatus.choices, default=CollectionStatus.NOT_COLLECTED
    )
    last_attempted_at = models.DateTimeField(null=True, blank=True)
    last_successful_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=64, blank=True)
    next_refresh_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(username=""), name="kaggle_profile_username_nonempty"),
            models.CheckConstraint(condition=~Q(normalized_username=""), name="kaggle_profile_key_nonempty"),
            models.CheckConstraint(condition=~Q(profile_url=""), name="kaggle_profile_url_nonempty"),
            models.CheckConstraint(
                condition=Q(collection_status__in=COLLECTION_STATUSES),
                name="kaggle_profile_collection_status_valid",
            ),
        ]

    def clean(self):
        from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity

        try:
            identity = normalize_kaggle_identity(self.username)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if self.normalized_username != identity.lookup_key or self.profile_url != identity.profile_url:
            raise ValidationError("Kaggle profile identity must match its username and canonical URL.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class KaggleProfileLink(models.Model):
    platform_account = models.OneToOneField(
        PlatformAccount, on_delete=models.CASCADE, related_name="kaggle_profile_link"
    )
    kaggle_profile = models.ForeignKey(
        KaggleProfile, on_delete=models.PROTECT, related_name="account_links"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.platform_account_id and self.platform_account.platform != PlatformAccount.Platform.KAGGLE:
            raise ValidationError("Only Kaggle accounts may link a Kaggle profile.")
        if self.platform_account_id and self.kaggle_profile_id:
            from apps.connectors.providers.kaggle.identity import normalize_kaggle_identity

            try:
                identity = normalize_kaggle_identity(self.platform_account.handle)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc
            if identity.lookup_key != self.kaggle_profile.normalized_username:
                raise ValidationError("Kaggle account and profile usernames must match.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)


class KaggleTrackStats(models.Model):
    class Track(models.TextChoices):
        COMPETITIONS = "competitions", "Competitions"
        CODE = "code", "Code"
        DATASETS = "datasets", "Datasets"

    class RankStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        RANKED = "ranked", "Ranked"
        UNRANKED = "unranked", "Unranked"

    profile = models.ForeignKey(KaggleProfile, on_delete=models.CASCADE, related_name="track_stats")
    track = models.CharField(max_length=16, choices=Track.choices)
    rank_status = models.CharField(max_length=10, choices=RankStatus.choices, default=RankStatus.UNKNOWN)
    tier = models.CharField(max_length=16, null=True, blank=True)
    global_rank = models.PositiveIntegerField(null=True, blank=True)
    highest_rank = models.PositiveIntegerField(null=True, blank=True)
    points = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    gold_medals = models.PositiveIntegerField(null=True, blank=True)
    silver_medals = models.PositiveIntegerField(null=True, blank=True)
    bronze_medals = models.PositiveIntegerField(null=True, blank=True)
    source = models.CharField(max_length=40)
    data_collected_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["profile", "track"], name="unique_kaggle_profile_track"),
            models.CheckConstraint(condition=Q(track__in=KAGGLE_TRACKS), name="kaggle_stats_track_valid"),
            models.CheckConstraint(condition=Q(rank_status__in=RANK_STATUSES), name="kaggle_stats_status_valid"),
            models.CheckConstraint(
                condition=Q(highest_rank__isnull=True) | Q(highest_rank__gt=0),
                name="kaggle_stats_highest_rank_positive",
            ),
            models.CheckConstraint(
                condition=Q(points__isnull=True) | (Q(points__gte=0) & Q(points__lt=10000000000)),
                name="kaggle_stats_points_valid",
            ),
            models.CheckConstraint(
                condition=(Q(rank_status="ranked") & Q(global_rank__isnull=False) & Q(global_rank__gt=0))
                | (Q(rank_status__in=["unknown", "unranked"]) & Q(global_rank__isnull=True)),
                name="kaggle_stats_status_rank_consistent",
            ),
            models.CheckConstraint(
                condition=~Q(rank_status="unranked") | (Q(tier__isnull=True) & Q(points__isnull=True)),
                name="kaggle_stats_unranked_values_empty",
            ),
        ]


class KaggleManualTrackStats(models.Model):
    """Self-reported values owned by one linked STALKER account."""

    platform_account = models.ForeignKey(
        PlatformAccount, on_delete=models.CASCADE, related_name="kaggle_manual_stats",
    )
    track = models.CharField(max_length=16, choices=KaggleTrackStats.Track.choices)
    rank_status = models.CharField(max_length=10, choices=KaggleTrackStats.RankStatus.choices)
    global_rank = models.PositiveIntegerField(null=True, blank=True)
    highest_rank = models.PositiveIntegerField(null=True, blank=True)
    tier = models.CharField(max_length=16, null=True, blank=True)
    points = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    gold_medals = models.PositiveIntegerField(null=True, blank=True)
    silver_medals = models.PositiveIntegerField(null=True, blank=True)
    bronze_medals = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform_account", "track"], name="unique_kaggle_manual_account_track",
            ),
            models.CheckConstraint(condition=Q(track__in=KAGGLE_TRACKS), name="kaggle_manual_track_valid"),
            models.CheckConstraint(condition=Q(rank_status__in=RANK_STATUSES), name="kaggle_manual_status_valid"),
            models.CheckConstraint(
                condition=Q(highest_rank__isnull=True) | Q(highest_rank__gt=0),
                name="kaggle_manual_highest_rank_positive",
            ),
            models.CheckConstraint(
                condition=Q(points__isnull=True) | (Q(points__gte=0) & Q(points__lt=10000000000)),
                name="kaggle_manual_points_valid",
            ),
            models.CheckConstraint(
                condition=(Q(rank_status="ranked") & Q(global_rank__isnull=False) & Q(global_rank__gt=0))
                | (Q(rank_status__in=["unknown", "unranked"]) & Q(global_rank__isnull=True)),
                name="kaggle_manual_status_rank_consistent",
            ),
            models.CheckConstraint(
                condition=~Q(rank_status="unranked") | (Q(tier__isnull=True) & Q(points__isnull=True)),
                name="kaggle_manual_unranked_values_empty",
            ),
        ]


class KaggleRankingSnapshot(models.Model):
    profile = models.ForeignKey(KaggleProfile, on_delete=models.CASCADE, related_name="ranking_snapshots")
    track = models.CharField(max_length=16, choices=KaggleTrackStats.Track.choices)
    rank_status = models.CharField(max_length=10, choices=KaggleTrackStats.RankStatus.choices)
    global_rank = models.PositiveIntegerField(null=True, blank=True)
    tier = models.CharField(max_length=16, null=True, blank=True)
    points = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    captured_on = models.DateField()
    captured_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "track", "captured_on"], name="unique_kaggle_daily_ranking"
            ),
            models.CheckConstraint(condition=Q(track__in=KaggleTrackStats.Track.values), name="kaggle_snapshot_track_valid"),
            models.CheckConstraint(
                condition=Q(rank_status__in=KaggleTrackStats.RankStatus.values),
                name="kaggle_snapshot_status_valid",
            ),
            models.CheckConstraint(
                condition=Q(points__isnull=True) | (Q(points__gte=0) & Q(points__lt=10000000000)),
                name="kaggle_snapshot_points_valid",
            ),
            models.CheckConstraint(
                condition=(Q(rank_status=KaggleTrackStats.RankStatus.RANKED)
                           & Q(global_rank__isnull=False) & Q(global_rank__gt=0))
                | (Q(rank_status__in=[KaggleTrackStats.RankStatus.UNKNOWN, KaggleTrackStats.RankStatus.UNRANKED])
                   & Q(global_rank__isnull=True)),
                name="kaggle_snapshot_status_rank_consistent",
            ),
            models.CheckConstraint(
                condition=~Q(rank_status=KaggleTrackStats.RankStatus.UNRANKED)
                | (Q(tier__isnull=True) & Q(points__isnull=True)),
                name="kaggle_snapshot_unranked_values_empty",
            ),
        ]
        indexes = [
            models.Index(fields=["profile", "track", "-captured_at"], name="kaggle_rank_history_idx")
        ]


class KaggleCollectionRun(models.Model):
    class Trigger(models.TextChoices):
        MANUAL = "manual", "Manual"
        SCHEDULED = "scheduled", "Scheduled"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        RETRYING = "retrying", "Retrying"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(KaggleProfile, on_delete=models.CASCADE, related_name="collection_runs")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="kaggle_collection_requests",
    )
    trigger = models.CharField(max_length=12, choices=Trigger.choices)
    provider_name = models.CharField(max_length=64)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.QUEUED)
    task_id = models.CharField(max_length=64, null=True, blank=True, unique=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    queued_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    dispatch_attempts = models.PositiveSmallIntegerField(default=0)
    next_dispatch_at = models.DateTimeField(null=True, blank=True)
    last_dispatch_error_code = models.CharField(max_length=64, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    safe_error_message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(trigger__in=("manual", "scheduled")), name="kaggle_run_trigger_valid"),
            models.CheckConstraint(condition=Q(status__in=RUN_STATUSES), name="kaggle_run_status_valid"),
            models.CheckConstraint(condition=Q(max_attempts__gt=0), name="kaggle_run_max_attempts_positive"),
            models.CheckConstraint(condition=Q(attempt_count__lte=models.F("max_attempts")), name="kaggle_run_attempts_bounded"),
            models.UniqueConstraint(fields=["profile"], condition=Q(status__in=ACTIVE_RUN_STATUSES),
                                    name="unique_active_kaggle_run_per_profile"),
        ]
        indexes = [
            models.Index(fields=["profile", "status", "-created_at"], name="kaggle_run_profile_status_idx"),
            models.Index(fields=["-created_at"], name="kaggle_run_created_idx"),
            models.Index(fields=["status", "next_dispatch_at"], name="kaggle_run_dispatch_idx"),
            models.Index(fields=["status", "lease_expires_at"], name="kaggle_run_lease_idx"),
        ]
