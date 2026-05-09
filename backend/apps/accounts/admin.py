from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import ExternalAccount, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "full_name",
        "country",
        "institution",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "country")
    search_fields = ("username", "email", "full_name", "institution")
    ordering = ("username",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": (
                    "full_name",
                    "avatar",
                    "bio",
                    "country",
                    "institution",
                    "github_url",
                    "linkedin_url",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(ExternalAccount)
class ExternalAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "source",
        "handle_or_slug",
        "verification_status",
        "sync_status",
        "last_synced_at",
        "is_active",
    )
    list_filter = ("source", "verification_status", "sync_status", "is_active")
    search_fields = ("user__username", "user__email", "handle_or_slug")
    readonly_fields = ("created_at", "updated_at")
