from rest_framework import serializers

from apps.accounts.models import ExternalAccount
from apps.accounts.serializers import ProfileSnapshotSummarySerializer, UserSerializer


class DashboardAccountSerializer(serializers.ModelSerializer):
    latest_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = ExternalAccount
        fields = (
            "source",
            "handle_or_slug",
            "verification_status",
            "sync_status",
            "last_synced_at",
            "latest_snapshot",
        )

    def get_latest_snapshot(self, obj: ExternalAccount) -> dict | None:
        snapshot = obj.snapshots.first()
        if snapshot is None:
            return None
        return ProfileSnapshotSummarySerializer(snapshot).data


class DashboardMeSerializer(serializers.Serializer):
    user = UserSerializer()
    accounts = DashboardAccountSerializer(many=True)
