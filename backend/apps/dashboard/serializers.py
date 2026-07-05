from rest_framework import serializers

from apps.accounts.models import User
from apps.connectors.models import CodeforcesStats, PlatformAccount
from apps.connectors.services import can_sync_platform_account, get_sync_cooldown_seconds


class DashboardUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "avatar",
            "bio",
            "country",
            "institution",
            "github_url",
            "linkedin_url",
        )
        read_only_fields = fields


class DashboardCodeforcesStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeforcesStats
        fields = (
            "rating",
            "max_rating",
            "rank",
            "max_rank",
            "solved_count",
            "attempted_count",
            "accepted_submission_count",
            "contest_count",
            "last_online_at",
            "registered_at",
            "updated_at",
        )
        read_only_fields = fields


class DashboardPlatformSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    can_sync = serializers.SerializerMethodField()
    sync_cooldown_seconds = serializers.SerializerMethodField()

    class Meta:
        model = PlatformAccount
        fields = (
            "id",
            "platform",
            "handle",
            "profile_url",
            "is_verified",
            "last_synced_at",
            "created_at",
            "updated_at",
            "stats",
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = fields

    def get_stats(self, obj: PlatformAccount) -> dict | None:
        if obj.platform != PlatformAccount.Platform.CODEFORCES:
            return None

        try:
            stats = obj.codeforces_stats
        except CodeforcesStats.DoesNotExist:
            return None

        return DashboardCodeforcesStatsSerializer(stats).data

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_sync_cooldown_seconds(self, obj: PlatformAccount) -> int:
        return get_sync_cooldown_seconds(obj)
