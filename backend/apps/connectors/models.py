from django.conf import settings
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
