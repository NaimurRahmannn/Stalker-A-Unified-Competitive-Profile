from django.contrib import admin

from apps.connectors.models import PlatformAccount


@admin.register(PlatformAccount)
class PlatformAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "platform",
        "handle",
        "is_verified",
        "last_synced_at",
        "created_at",
    )
    list_filter = ("platform", "is_verified")
    search_fields = ("user__username", "user__email", "handle")
    readonly_fields = ("created_at", "updated_at")
