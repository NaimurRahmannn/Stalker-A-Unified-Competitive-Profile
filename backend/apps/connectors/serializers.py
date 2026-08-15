from django.db import transaction
from django.utils.dateparse import parse_datetime
from rest_framework import serializers

from apps.connectors.base.exceptions import InvalidExternalAccountError
from apps.connectors.base.utils import build_atcoder_profile_url
from apps.connectors.models import (
    AtCoderStats,
    AtCoderSubmission,
    AtCoderSubmissionSyncState,
    AtCoderSyncState,
    CodeforcesStats,
    PlatformAccount,
    PlatformRatingEvent,
    PlatformStatsSnapshot,
)
from apps.connectors.providers.atcoder.client import normalize_atcoder_handle
from apps.connectors.providers.atcoder.mapper import get_atcoder_rating_color
from apps.connectors.providers.codeforces.mapper import normalize_rating_history
from apps.connectors.services import (
    can_sync_platform_account,
    get_sync_cooldown_seconds,
)


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


class AtCoderStatsSerializer(serializers.ModelSerializer):
    rating_color = serializers.SerializerMethodField()

    class Meta:
        model = AtCoderStats
        fields = (
            "discipline",
            "current_rating",
            "max_rating",
            "rating_color",
            "rated_contest_count",
            "last_rated_at",
            "last_performance",
            "rating_data_updated_at",
            "solved_count",
            "attempted_count",
            "accepted_submission_count",
            "indexed_submission_count",
            "submission_data_updated_at",
            "submission_backfill_complete",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_rating_color(self, obj: AtCoderStats) -> str | None:
        return get_atcoder_rating_color(obj.current_rating)


class AtCoderSubmissionSyncStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtCoderSubmissionSyncState
        fields = (
            "last_submission_epoch",
            "last_submission_id",
            "backfill_complete",
            "progress_status",
            "blocked_reason",
            "submission_data_updated_at",
        )
        read_only_fields = fields


class AtCoderSyncStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtCoderSyncState
        fields = (
            "overall_status",
            "rating_status",
            "rating_error_code",
            "rating_sync_attempted_at",
            "submission_status",
            "submission_error_code",
            "submission_sync_attempted_at",
        )
        read_only_fields = fields


class AtCoderRecentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AtCoderSubmission
        fields = (
            "external_submission_id",
            "external_contest_id",
            "external_problem_id",
            "verdict",
            "language",
            "submitted_at",
            "execution_time_ms",
            "code_size_bytes",
        )
        read_only_fields = fields


class AtCoderAnalyticsAccountSerializer(serializers.ModelSerializer):
    profile_url = serializers.SerializerMethodField()
    handle_validated = serializers.SerializerMethodField()
    ownership_verified = serializers.SerializerMethodField()
    can_sync = serializers.SerializerMethodField()
    sync_cooldown_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = PlatformAccount
        fields = (
            "id",
            "handle",
            "profile_url",
            "handle_validated",
            "handle_validated_at",
            "ownership_verified",
            "ownership_verified_at",
            "last_sync_attempted_at",
            "last_synced_at",
            "can_sync",
            "sync_cooldown_remaining_seconds",
        )
        read_only_fields = fields

    def get_profile_url(self, obj: PlatformAccount) -> str:
        return obj.profile_url or build_atcoder_profile_url(obj.handle)

    def get_handle_validated(self, obj: PlatformAccount) -> bool:
        return obj.handle_validated_at is not None or obj.is_verified

    def get_ownership_verified(self, obj: PlatformAccount) -> bool:
        return obj.ownership_verified_at is not None

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_sync_cooldown_remaining_seconds(
        self,
        obj: PlatformAccount,
    ) -> int:
        return get_sync_cooldown_seconds(obj)


class AtCoderAnalyticsStatsSerializer(serializers.ModelSerializer):
    rating_color = serializers.SerializerMethodField()
    submission_stats_complete = serializers.BooleanField(
        source="submission_backfill_complete"
    )

    class Meta:
        model = AtCoderStats
        fields = (
            "discipline",
            "current_rating",
            "max_rating",
            "rating_color",
            "rated_contest_count",
            "last_rated_at",
            "last_performance",
            "solved_count",
            "attempted_count",
            "accepted_submission_count",
            "indexed_submission_count",
            "submission_stats_complete",
        )
        read_only_fields = fields

    def get_rating_color(self, obj: AtCoderStats) -> str | None:
        return get_atcoder_rating_color(obj.current_rating)


class AtCoderAnalyticsRatingEventSerializer(serializers.ModelSerializer):
    contest_id = serializers.CharField(source="external_contest_id")
    rated = serializers.BooleanField(source="is_rated")

    class Meta:
        model = PlatformRatingEvent
        fields = (
            "contest_id",
            "contest_name",
            "rank",
            "performance",
            "inner_performance",
            "old_rating",
            "new_rating",
            "rating_change",
            "rated",
            "occurred_at",
        )
        read_only_fields = fields


class AtCoderAnalyticsActivitySerializer(serializers.ModelSerializer):
    submission_id = serializers.IntegerField(source="external_submission_id")
    contest_id = serializers.CharField(source="external_contest_id")
    problem_id = serializers.CharField(source="external_problem_id")
    accepted = serializers.SerializerMethodField()

    class Meta:
        model = AtCoderSubmission
        fields = (
            "submission_id",
            "contest_id",
            "problem_id",
            "verdict",
            "accepted",
            "language",
            "submitted_at",
            "execution_time_ms",
            "code_size_bytes",
        )
        read_only_fields = fields

    def get_accepted(self, obj: AtCoderSubmission) -> bool:
        return obj.verdict == "AC"


class AtCoderAnalyticsSnapshotSerializer(serializers.ModelSerializer):
    rated_contest_count = serializers.IntegerField(source="contest_count")
    submission_stats_complete = serializers.SerializerMethodField()

    class Meta:
        model = PlatformStatsSnapshot
        fields = (
            "captured_at",
            "rating",
            "solved_count",
            "rated_contest_count",
            "submission_stats_complete",
        )
        read_only_fields = fields

    def get_submission_stats_complete(
        self,
        obj: PlatformStatsSnapshot,
    ) -> bool:
        if "submission_stats_complete" in obj.metadata:
            return bool(obj.metadata["submission_stats_complete"])
        return obj.solved_count is not None


class AtCoderAnalyticsProgressSerializer(serializers.Serializer):
    status = serializers.CharField()
    stats_complete = serializers.BooleanField()
    error_code = serializers.CharField(allow_null=True)


class AtCoderAnalyticsSourceSyncSerializer(serializers.Serializer):
    status = serializers.CharField()
    updated_at = serializers.DateTimeField(allow_null=True)
    attempted_at = serializers.DateTimeField(allow_null=True)
    using_cached_data = serializers.BooleanField()
    error_code = serializers.CharField(allow_null=True)


class AtCoderAnalyticsSubmissionSyncSerializer(
    AtCoderAnalyticsSourceSyncSerializer
):
    progress = AtCoderAnalyticsProgressSerializer()


class AtCoderAnalyticsSyncSerializer(serializers.Serializer):
    status = serializers.CharField()
    rating = AtCoderAnalyticsSourceSyncSerializer()
    submissions = AtCoderAnalyticsSubmissionSyncSerializer()


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
            "last_sync_attempted_at",
            "last_synced_at",
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = fields

    def get_can_sync(self, obj: PlatformAccount) -> bool:
        return can_sync_platform_account(obj)

    def get_handle_validated(self, obj: PlatformAccount) -> bool:
        return obj.handle_validated_at is not None or obj.is_verified

    def get_ownership_verified(self, obj: PlatformAccount) -> bool:
        return obj.ownership_verified_at is not None

    def get_sync_cooldown_seconds(self, obj: PlatformAccount) -> int:
        return get_sync_cooldown_seconds(obj)


class PlatformAccountSerializer(serializers.ModelSerializer):
    codeforces_stats = CodeforcesStatsSerializer(read_only=True)
    atcoder_stats = AtCoderStatsSerializer(read_only=True)
    atcoder_sync_state = AtCoderSyncStateSerializer(read_only=True)
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
            "last_sync_attempted_at",
            "last_synced_at",
            "created_at",
            "updated_at",
            "codeforces_stats",
            "atcoder_stats",
            "atcoder_sync_state",
            "can_sync",
            "sync_cooldown_seconds",
        )
        read_only_fields = (
            "id",
            "is_verified",
            "handle_validated",
            "handle_validated_at",
            "ownership_verified",
            "ownership_verified_at",
            "last_sync_attempted_at",
            "last_synced_at",
            "created_at",
            "updated_at",
            "codeforces_stats",
            "atcoder_stats",
            "atcoder_sync_state",
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

    def get_handle_validated(self, obj: PlatformAccount) -> bool:
        return obj.handle_validated_at is not None or obj.is_verified

    def get_ownership_verified(self, obj: PlatformAccount) -> bool:
        return obj.ownership_verified_at is not None

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

        if platform == PlatformAccount.Platform.ATCODER and "handle" in attrs:
            try:
                attrs["handle"] = normalize_atcoder_handle(attrs["handle"])
            except InvalidExternalAccountError as exc:
                raise serializers.ValidationError({"handle": str(exc)}) from exc

        return attrs

    def update(
        self,
        instance: PlatformAccount,
        validated_data: dict,
    ) -> PlatformAccount:
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
                instance.handle_validated_at = None
                instance.ownership_verified_at = None
                instance.last_sync_attempted_at = None
                instance.last_synced_at = None
                instance.save(
                    update_fields=[
                        "profile_url",
                        "is_verified",
                        "handle_validated_at",
                        "ownership_verified_at",
                        "last_sync_attempted_at",
                        "last_synced_at",
                        "updated_at",
                    ]
                )
                CodeforcesStats.objects.filter(platform_account=instance).delete()
                AtCoderStats.objects.filter(platform_account=instance).delete()
                AtCoderSyncState.objects.filter(platform_account=instance).delete()
                AtCoderSubmissionSyncState.objects.filter(
                    platform_account=instance
                ).delete()
                AtCoderSubmission.objects.filter(platform_account=instance).delete()
                PlatformRatingEvent.objects.filter(platform_account=instance).delete()
                PlatformStatsSnapshot.objects.filter(platform_account=instance).delete()
                instance._state.fields_cache.pop("codeforces_stats", None)
                instance._state.fields_cache.pop("atcoder_stats", None)
                instance._state.fields_cache.pop(
                    "atcoder_submission_sync_state", None
                )
                instance._state.fields_cache.pop("atcoder_sync_state", None)
                getattr(instance, "_prefetched_objects_cache", {}).pop(
                    "rating_events", None
                )

        return instance


def serialize_atcoder_submission_overview(
    platform_account: PlatformAccount,
    recent_limit: int = 20,
) -> dict:
    stats = AtCoderStats.objects.filter(platform_account=platform_account).first()
    state = AtCoderSubmissionSyncState.objects.filter(
        platform_account=platform_account
    ).first()
    recent = AtCoderSubmission.objects.filter(
        platform_account=platform_account
    ).order_by("-submitted_at", "-external_submission_id")[:recent_limit]
    return {
        "platform": PlatformAccount.Platform.ATCODER,
        "handle": platform_account.handle,
        "stats": AtCoderStatsSerializer(stats).data if stats else None,
        "sync_state": (
            AtCoderSubmissionSyncStateSerializer(state).data if state else None
        ),
        "recent_submissions": AtCoderRecentSubmissionSerializer(
            recent,
            many=True,
        ).data,
    }


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
