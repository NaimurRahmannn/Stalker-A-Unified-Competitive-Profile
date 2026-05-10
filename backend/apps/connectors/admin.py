from django.contrib import admin

from apps.connectors.models import CodeforcesStats, PlatformAccount


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


@admin.register(CodeforcesStats)
class CodeforcesStatsAdmin(admin.ModelAdmin):
    list_display = (
        "platform_account",
        "handle",
        "rating",
        "max_rating",
        "rank",
        "max_rank",
        "solved_count",
        "attempted_count",
        "accepted_submission_count",
        "contest_count",
        "updated_at",
    )
    list_filter = ("rank", "max_rank")
    search_fields = (
        "handle",
        "platform_account__user__username",
        "platform_account__user__email",
    )
    readonly_fields = ("created_at", "updated_at")
