from rest_framework import serializers

from apps.connectors.models import PlatformAccount


class ConnectorHealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class PlatformAccountSerializer(serializers.ModelSerializer):
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
        )
        read_only_fields = (
            "id",
            "is_verified",
            "last_synced_at",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "profile_url": {"required": False, "allow_blank": True},
        }

    def validate_handle(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Handle cannot be empty.")
        return value

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
