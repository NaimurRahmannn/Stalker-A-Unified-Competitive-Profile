from django.core.exceptions import ValidationError
from django.db import models

from apps.connectors.models import PlatformAccount


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        ]
        indexes = [models.Index(fields=["profile", "track"], name="kaggle_stats_profile_track_idx")]


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
        ]
        indexes = [
            models.Index(fields=["profile", "track", "-captured_at"], name="kaggle_rank_history_idx")
        ]
