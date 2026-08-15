from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from apps.connectors.models import (
    CodeforcesStats,
    PlatformAccount,
    PlatformStatsSnapshot,
)
from apps.connectors.providers.codeforces.mapper import normalize_rating_history
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


class CodeforcesRatingHistorySerializer(serializers.Serializer):
    contest_id = serializers.IntegerField(allow_null=True)
    contest_name = serializers.CharField(allow_null=True)
    rank = serializers.IntegerField(allow_null=True)
    old_rating = serializers.IntegerField(allow_null=True)
    new_rating = serializers.IntegerField()
    rating_change = serializers.IntegerField(allow_null=True)
    timestamp = serializers.DateTimeField()


class CodeforcesRecentActivitySerializer(serializers.Serializer):
    submission_id = serializers.IntegerField(allow_null=True)
    contest_id = serializers.IntegerField(allow_null=True)
    problem_index = serializers.CharField(allow_null=True)
    problem_name = serializers.CharField()
    problem_rating = serializers.IntegerField(allow_null=True)
    verdict = serializers.CharField()
    language = serializers.CharField(allow_null=True)
    submitted_at = serializers.DateTimeField()


class PlatformStatsSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformStatsSnapshot
        fields = (
            "captured_at",
            "rating",
            "solved_count",
            "contest_count",
        )
        read_only_fields = fields


class CodeforcesAnalyticsAccountSerializer(serializers.ModelSerializer):
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
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = fields

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_sync_cooldown_seconds(self, obj: PlatformAccount) -> int:
        return get_sync_cooldown_seconds(obj)


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

    def update(self, instance: PlatformAccount, validated_data: dict) -> PlatformAccount:
        handle_changed = (
            "handle" in validated_data
            and validated_data["handle"] != instance.handle
        )
        platform_changed = (
            "platform" in validated_data
            and validated_data["platform"] != instance.platform
        )

        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if handle_changed or platform_changed:
                instance.profile_url = ""
                instance.is_verified = False
                instance.last_synced_at = None
                instance.save(
                    update_fields=[
                        "profile_url",
                        "is_verified",
                        "last_synced_at",
                        "updated_at",
                    ]
                )
                CodeforcesStats.objects.filter(platform_account=instance).delete()
                PlatformStatsSnapshot.objects.filter(platform_account=instance).delete()

        return instance


def serialize_codeforces_rating_history(stats: CodeforcesStats) -> list[dict]:
    normalized = normalize_rating_history(stats.raw_rating_history)
    return CodeforcesRatingHistorySerializer(normalized, many=True).data


def serialize_codeforces_recent_activity(stats: CodeforcesStats) -> list[dict]:
    activity = stats.recent_activity if isinstance(stats.recent_activity, list) else []
    normalized = []
    for item in activity:
        if not isinstance(item, dict):
            continue
        problem_name = item.get("problem_name")
        verdict = item.get("verdict")
        submitted_at = item.get("submitted_at")
        if (
            not isinstance(problem_name, str)
            or not problem_name.strip()
            or not isinstance(verdict, str)
            or not verdict.strip()
            or not isinstance(submitted_at, str)
            or parse_datetime(submitted_at) is None
        ):
            continue
        normalized.append(
            {
                "submission_id": item.get("submission_id"),
                "contest_id": item.get("contest_id"),
                "problem_index": item.get("problem_index"),
                "problem_name": problem_name,
                "problem_rating": item.get("problem_rating"),
                "verdict": verdict,
                "language": item.get("language"),
                "submitted_at": submitted_at,
            }
        )
    return CodeforcesRecentActivitySerializer(normalized, many=True).data
