from rest_framework import serializers

from apps.connectors.models import CodeforcesStats, PlatformAccount
from apps.connectors.services import can_sync_platform_account, get_sync_cooldown_seconds


class ConnectorHealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class CodeforcesStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeforcesStats
        fields = (
            "handle",
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
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PlatformAccountSerializer(serializers.ModelSerializer):
    codeforces_stats = CodeforcesStatsSerializer(read_only=True)
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
            "codeforces_stats",
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = (
            "id",
            "is_verified",
            "last_synced_at",
            "created_at",
            "updated_at",
            "codeforces_stats",
            "can_sync",
            "sync_cooldown_seconds",
        )
        extra_kwargs = {
            "profile_url": {"required": False, "allow_blank": True},
        }

    def validate_handle(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Handle cannot be empty.")
        return value

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_sync_cooldown_seconds(self, obj: PlatformAccount) -> int:
        return get_sync_cooldown_seconds(obj)

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        platform = attrs.get("platform")

        if platform is None and self.instance is not None:
            platform = self.instance.platform

        if user is not None and user.is_authenticated and platform is not None:
            queryset = PlatformAccount.objects.filter(user=user, platform=platform)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    {"platform": "You already have an account for this platform."}
                )

        return attrs
