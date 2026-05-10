from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
    is_verified = models.BooleanField(default=False)
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
