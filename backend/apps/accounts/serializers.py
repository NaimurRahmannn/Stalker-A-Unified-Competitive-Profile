from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import ExternalAccount, User
from apps.dashboard.models import ProfileSnapshot


class UserSerializer(serializers.ModelSerializer):
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
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "email", "full_name", "password", "password_confirm")
        extra_kwargs = {
            "email": {"required": True},
            "full_name": {"required": True, "allow_blank": False},
        }

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username is already taken.")
        return value

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"],
        )


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "full_name",
            "avatar",
            "bio",
            "country",
            "institution",
            "github_url",
            "linkedin_url",
        )


class ProfileSnapshotSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileSnapshot
        fields = (
            "display_name",
            "headline_rank_title",
            "rating",
            "highest_rating",
            "contests_count",
            "solved_count",
            "avatar_url",
        )


class ExternalAccountSerializer(serializers.ModelSerializer):
    latest_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = ExternalAccount
        fields = (
            "id",
            "source",
            "handle_or_slug",
            "profile_url",
            "verification_status",
            "sync_status",
            "last_synced_at",
            "last_error",
            "is_active",
            "latest_snapshot",
        )

    def get_latest_snapshot(self, obj: ExternalAccount) -> dict | None:
        snapshot = obj.snapshots.first()
        if snapshot is None:
            return None
        return ProfileSnapshotSummarySerializer(snapshot).data


class ConnectExternalAccountSerializer(serializers.Serializer):
    source = serializers.ChoiceField(choices=ExternalAccount.Source.choices)
    handle_or_slug = serializers.CharField(max_length=255)
