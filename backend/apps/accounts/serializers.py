from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User


def uploaded_image_url(image, request) -> str | None:
    if not image:
        return None
    return request.build_absolute_uri(image.url) if request else image.url


def validate_profile_image(image):
    if image.size > 8 * 1024 * 1024:
        raise serializers.ValidationError("Image must be smaller than 8 MB.")
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise serializers.ValidationError("Upload a JPG, PNG, or WebP image.")
    return image


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    cover_photo = serializers.SerializerMethodField()

    def get_avatar(self, user: User) -> str | None:
        return uploaded_image_url(user.avatar_image, self.context.get("request")) or user.avatar or None

    def get_cover_photo(self, user: User) -> str | None:
        return uploaded_image_url(user.cover_image, self.context.get("request"))

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "avatar",
            "cover_photo",
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
    def validate_avatar_image(self, image):
        return validate_profile_image(image)

    def validate_cover_image(self, image):
        return validate_profile_image(image)

    class Meta:
        model = User
        fields = (
            "full_name",
            "avatar",
            "avatar_image",
            "cover_image",
            "bio",
            "country",
            "institution",
            "github_url",
            "linkedin_url",
        )
