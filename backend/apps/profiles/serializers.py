from rest_framework import serializers

from apps.accounts.models import User
from apps.connectors.models import CodeforcesStats, PlatformAccount


class PublicProfileUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "avatar",
            "bio",
            "country",
            "institution",
            "github_url",
            "linkedin_url",
        )
        read_only_fields = fields

    def to_representation(self, instance: User) -> dict:
        data = super().to_representation(instance)

        for field in (
            "avatar",
            "bio",
            "country",
            "institution",
            "github_url",
            "linkedin_url",
        ):
            if data.get(field) == "":
                data[field] = None

        return data


class PublicProfileCodeforcesStatsSerializer(serializers.ModelSerializer):
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


class PublicProfilePlatformSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    handle_validated = serializers.SerializerMethodField()
    ownership_verified = serializers.SerializerMethodField()

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
        )
        read_only_fields = fields

    def get_stats(self, obj: PlatformAccount) -> dict | None:
        if obj.platform != PlatformAccount.Platform.CODEFORCES:
            return None

        try:
            stats = obj.codeforces_stats
        except CodeforcesStats.DoesNotExist:
            return None

        return PublicProfileCodeforcesStatsSerializer(stats).data

    def get_handle_validated(self, obj: PlatformAccount) -> bool:
        return obj.handle_validated_at is not None or obj.is_verified

    def get_ownership_verified(self, obj: PlatformAccount) -> bool:
        return obj.ownership_verified_at is not None
