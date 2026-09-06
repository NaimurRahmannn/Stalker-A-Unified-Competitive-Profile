from rest_framework import serializers

from apps.accounts.models import User
from apps.connectors.models import (
    AtCoderStats,
    CodeforcesStats,
    LeetCodeStats,
    PlatformAccount,
)
from apps.connectors.providers.atcoder.mapper import get_atcoder_rating_color
from apps.connectors.services import (
    can_sync_platform_account,
    get_sync_cooldown_seconds,
)


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


class DashboardAtCoderStatsSerializer(serializers.ModelSerializer):
    rating_color = serializers.SerializerMethodField()
    submission_stats_complete = serializers.BooleanField(
        source="submission_backfill_complete"
    )

    class Meta:
        model = AtCoderStats
        fields = (
            "current_rating",
            "max_rating",
            "rating_color",
            "rated_contest_count",
            "solved_count",
            "attempted_count",
            "accepted_submission_count",
            "indexed_submission_count",
            "submission_stats_complete",
            "rating_data_updated_at",
            "submission_data_updated_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_rating_color(self, obj: AtCoderStats) -> str | None:
        return get_atcoder_rating_color(obj.current_rating)


class DashboardLeetCodeStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeetCodeStats
        fields = (
            "current_contest_rating",
            "attended_contest_count",
            "contest_global_ranking",
            "contest_top_percentage",
            "solved_total",
            "solved_easy",
            "solved_medium",
            "solved_hard",
            "problem_stats_complete",
            "data_updated_at",
            "updated_at",
        )
        read_only_fields = fields


class DashboardPlatformSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    handle_validated = serializers.SerializerMethodField()
    ownership_verified = serializers.SerializerMethodField()
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
            "handle_validated",
            "handle_validated_at",
            "ownership_verified",
            "ownership_verified_at",
            "last_synced_at",
            "created_at",
            "updated_at",
            "stats",
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = fields

    def get_stats(self, obj: PlatformAccount) -> dict | None:
        if obj.platform == PlatformAccount.Platform.CODEFORCES:
            try:
                stats = obj.codeforces_stats
            except CodeforcesStats.DoesNotExist:
                return None
            return DashboardCodeforcesStatsSerializer(stats).data
        if obj.platform == PlatformAccount.Platform.ATCODER:
            try:
                stats = obj.atcoder_stats
            except AtCoderStats.DoesNotExist:
                return None
            return DashboardAtCoderStatsSerializer(stats).data
        if obj.platform == PlatformAccount.Platform.LEETCODE:
            try:
                stats = obj.leetcode_stats
            except LeetCodeStats.DoesNotExist:
                return None
            return DashboardLeetCodeStatsSerializer(stats).data
        return None

    def get_handle_validated(self, obj: PlatformAccount) -> bool:
        return obj.handle_validated_at is not None or obj.is_verified

    def get_ownership_verified(self, obj: PlatformAccount) -> bool:
        return obj.ownership_verified_at is not None

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_sync_cooldown_seconds(self, obj: PlatformAccount) -> int:
        return get_sync_cooldown_seconds(obj)
