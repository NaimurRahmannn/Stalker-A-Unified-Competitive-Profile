from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PlatformAccount(models.Model):
    class Platform(models.TextChoices):
        CODEFORCES = "codeforces", "Codeforces"
        CODECHEF = "codechef", "CodeChef"
        LEETCODE = "leetcode", "LeetCode"
        ATCODER = "atcoder", "AtCoder"
        KAGGLE = "kaggle", "Kaggle"
        GITHUB = "github", "GitHub"
        CTFTIME = "ctftime", "CTFtime"
        TRYHACKME = "tryhackme", "TryHackMe"
        HACKTHEBOX = "hackthebox", "Hack The Box"
        DEVPOST = "devpost", "Devpost"
        DORAHACKS = "dorahacks", "DoraHacks"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="platform_accounts",
    )
    platform = models.CharField(max_length=50, choices=Platform.choices)
    handle = models.CharField(max_length=255)
    profile_url = models.URLField(max_length=500, blank=True)
    # `is_verified` remains the backwards-compatible handle-validity flag.
    # Ownership is deliberately represented separately and is not inferred from sync.
    is_verified = models.BooleanField(default=False)
    handle_validated_at = models.DateTimeField(null=True, blank=True)
    ownership_verified_at = models.DateTimeField(null=True, blank=True)
    last_sync_attempted_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "platform"],
                name="unique_user_platform_account",
            ),
        ]
        ordering = ["platform"]

    def __str__(self) -> str:
        return f"{self.user.username}::{self.platform}::{self.handle}"


class CodeforcesStats(models.Model):
    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="codeforces_stats",
    )
    handle = models.CharField(max_length=100)

    rating = models.IntegerField(blank=True, null=True)
    max_rating = models.IntegerField(blank=True, null=True)
    rank = models.CharField(max_length=100, blank=True, null=True)
    max_rank = models.CharField(max_length=100, blank=True, null=True)

    solved_count = models.PositiveIntegerField(default=0)
    attempted_count = models.PositiveIntegerField(default=0)
    accepted_submission_count = models.PositiveIntegerField(default=0)
    contest_count = models.PositiveIntegerField(default=0)

    last_online_at = models.DateTimeField(blank=True, null=True)
    registered_at = models.DateTimeField(blank=True, null=True)

    raw_user_info = models.JSONField(default=dict, blank=True)
    raw_rating_history = models.JSONField(default=list, blank=True)
    recent_activity = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.CODEFORCES
        ):
            raise ValidationError(
                "Codeforces stats can only be attached to Codeforces platform accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Codeforces stats for {self.handle}"


class AtCoderStats(models.Model):
    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="atcoder_stats",
    )
    discipline = models.CharField(max_length=32, default="algorithm")
    current_rating = models.IntegerField(blank=True, null=True)
    max_rating = models.IntegerField(blank=True, null=True)
    rated_contest_count = models.PositiveIntegerField(default=0)
    last_rated_at = models.DateTimeField(blank=True, null=True)
    last_performance = models.IntegerField(blank=True, null=True)
    rating_data_updated_at = models.DateTimeField(blank=True, null=True)
    solved_count = models.PositiveIntegerField(default=0)
    attempted_count = models.PositiveIntegerField(default=0)
    accepted_submission_count = models.PositiveIntegerField(default=0)
    indexed_submission_count = models.PositiveIntegerField(default=0)
    submission_data_updated_at = models.DateTimeField(blank=True, null=True)
    submission_backfill_complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.ATCODER
        ):
            raise ValidationError(
                "AtCoder stats can only be attached to AtCoder platform accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"AtCoder stats for {self.platform_account.handle}"


class LeetCodeStats(models.Model):
    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="leetcode_stats",
    )
    display_name = models.CharField(max_length=255, blank=True, null=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    school = models.CharField(max_length=255, blank=True, null=True)
    global_problem_ranking = models.PositiveIntegerField(blank=True, null=True)
    reputation = models.PositiveIntegerField(blank=True, null=True)

    solved_total = models.PositiveIntegerField(default=0)
    solved_easy = models.PositiveIntegerField(default=0)
    solved_medium = models.PositiveIntegerField(default=0)
    solved_hard = models.PositiveIntegerField(default=0)
    problem_stats_complete = models.BooleanField(default=False)

    current_contest_rating = models.FloatField(blank=True, null=True)
    attended_contest_count = models.PositiveIntegerField(default=0)
    contest_global_ranking = models.PositiveIntegerField(blank=True, null=True)
    contest_total_participants = models.PositiveIntegerField(blank=True, null=True)
    contest_top_percentage = models.FloatField(blank=True, null=True)
    rating_history = models.JSONField(default=list, blank=True)

    data_updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.LEETCODE
        ):
            raise ValidationError(
                "LeetCode stats can only be attached to LeetCode accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"LeetCode stats for {self.platform_account.handle}"


class LeetCodeSyncState(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="leetcode_sync_state",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    last_attempted_at = models.DateTimeField(blank=True, null=True)
    last_successful_at = models.DateTimeField(blank=True, null=True)
    failure_reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.LEETCODE
        ):
            raise ValidationError(
                "LeetCode sync state can only be attached to LeetCode accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"LeetCode sync state for {self.platform_account.handle}"


class AtCoderSyncState(models.Model):
    class OverallStatus(models.TextChoices):
        NEVER = "never", "Never synchronized"
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    class SourceStatus(models.TextChoices):
        NEVER = "never", "Never synchronized"
        SUCCESS = "success", "Success"
        SKIPPED_FRESH = "skipped_fresh", "Skipped (fresh)"
        FAILED = "failed", "Failed"
        BLOCKED = "blocked", "Blocked"
        DISABLED = "disabled", "Disabled"

    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="atcoder_sync_state",
    )
    overall_status = models.CharField(
        max_length=16,
        choices=OverallStatus.choices,
        default=OverallStatus.NEVER,
    )
    rating_status = models.CharField(
        max_length=20,
        choices=SourceStatus.choices,
        default=SourceStatus.NEVER,
    )
    rating_error_code = models.CharField(max_length=64, blank=True)
    rating_sync_attempted_at = models.DateTimeField(null=True, blank=True)
    submission_status = models.CharField(
        max_length=20,
        choices=SourceStatus.choices,
        default=SourceStatus.NEVER,
    )
    submission_error_code = models.CharField(max_length=64, blank=True)
    submission_sync_attempted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.ATCODER
        ):
            raise ValidationError(
                "AtCoder sync state can only be attached to AtCoder accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"AtCoder sync state for {self.platform_account.handle}"


class AtCoderSubmissionSyncState(models.Model):
    class ProgressStatus(models.TextChoices):
        BACKFILLING = "backfilling", "Backfilling"
        CAUGHT_UP = "caught_up", "Caught up"
        BLOCKED = "blocked", "Blocked"

    platform_account = models.OneToOneField(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="atcoder_submission_sync_state",
    )
    last_submission_epoch = models.BigIntegerField(default=0)
    last_submission_id = models.BigIntegerField(default=0)
    backfill_complete = models.BooleanField(default=False)
    progress_status = models.CharField(
        max_length=16,
        choices=ProgressStatus.choices,
        default=ProgressStatus.BACKFILLING,
    )
    blocked_reason = models.CharField(max_length=64, blank=True)
    submission_data_updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.ATCODER
        ):
            raise ValidationError(
                "AtCoder submission state can only be attached to AtCoder accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"AtCoder submission state for {self.platform_account.handle}"


class AtCoderSubmission(models.Model):
    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="atcoder_submissions",
    )
    external_submission_id = models.BigIntegerField()
    external_contest_id = models.CharField(max_length=255)
    external_problem_id = models.CharField(max_length=255)
    verdict = models.CharField(max_length=64)
    language = models.CharField(max_length=255, blank=True, null=True)
    submitted_at = models.DateTimeField()
    provider_epoch_second = models.BigIntegerField()
    execution_time_ms = models.IntegerField(blank=True, null=True)
    code_size_bytes = models.PositiveIntegerField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at", "-external_submission_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["platform_account", "external_submission_id"],
                name="unique_atcoder_submission",
            )
        ]
        indexes = [
            models.Index(
                fields=["platform_account", "-submitted_at"],
                name="atcoder_submission_time_idx",
            ),
            models.Index(
                fields=["platform_account", "external_problem_id"],
                name="atcoder_submission_problem_idx",
            ),
            models.Index(
                fields=["platform_account", "verdict", "external_problem_id"],
                name="atcoder_submission_result_idx",
            ),
        ]

    def clean(self):
        if (
            self.platform_account_id
            and self.platform_account.platform != PlatformAccount.Platform.ATCODER
        ):
            raise ValidationError(
                "AtCoder submissions can only be attached to AtCoder accounts."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"AtCoder submission {self.external_submission_id}"


class PlatformRatingEvent(models.Model):
    class Discipline(models.TextChoices):
        ALGORITHM = "algorithm", "Algorithm"

    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="rating_events",
    )
    discipline = models.CharField(max_length=32, choices=Discipline.choices)
    external_contest_id = models.CharField(max_length=255)
    contest_name = models.CharField(max_length=500, blank=True, null=True)
    rank = models.IntegerField(blank=True, null=True)
    performance = models.IntegerField(blank=True, null=True)
    inner_performance = models.IntegerField(blank=True, null=True)
    old_rating = models.IntegerField(blank=True, null=True)
    new_rating = models.IntegerField(blank=True, null=True)
    rating_change = models.IntegerField(blank=True, null=True)
    is_rated = models.BooleanField()
    occurred_at = models.DateTimeField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["occurred_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "platform_account",
                    "discipline",
                    "external_contest_id",
                ],
                name="unique_platform_rating_event",
            )
        ]
        indexes = [
            models.Index(
                fields=["platform_account", "discipline", "-occurred_at"],
                name="platform_rating_event_idx",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.platform_account} {self.discipline} "
            f"rating event {self.external_contest_id}"
        )


class PlatformStatsSnapshot(models.Model):
    platform_account = models.ForeignKey(
        PlatformAccount,
        on_delete=models.CASCADE,
        related_name="stats_snapshots",
    )
    captured_at = models.DateTimeField(default=timezone.now)
    rating = models.FloatField(blank=True, null=True)
    solved_count = models.PositiveIntegerField(blank=True, null=True)
    contest_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-captured_at", "-id"]
        indexes = [
            models.Index(
                fields=["platform_account", "-captured_at"],
                name="platform_snapshot_time_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.platform_account} snapshot at {self.captured_at.isoformat()}"
