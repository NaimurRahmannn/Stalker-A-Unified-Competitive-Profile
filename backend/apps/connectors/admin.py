from django.contrib import admin

from apps.connectors.models import (
    AtCoderStats,
    CodeforcesStats,
    PlatformAccount,
    PlatformRatingEvent,
    PlatformStatsSnapshot,
)


@admin.register(PlatformAccount)
class PlatformAccountAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "platform",
        "handle",
        "is_verified",
        "handle_validated_at",
        "ownership_verified_at",
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


@admin.register(AtCoderStats)
class AtCoderStatsAdmin(admin.ModelAdmin):
    list_display = (
        "platform_account",
        "discipline",
        "current_rating",
        "max_rating",
        "rated_contest_count",
        "last_rated_at",
        "updated_at",
    )
    list_filter = ("discipline",)
    search_fields = (
        "platform_account__handle",
        "platform_account__user__username",
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlatformRatingEvent)
class PlatformRatingEventAdmin(admin.ModelAdmin):
    list_display = (
        "platform_account",
        "discipline",
        "external_contest_id",
        "new_rating",
        "is_rated",
        "occurred_at",
    )
    list_filter = ("discipline", "is_rated")
    search_fields = (
        "external_contest_id",
        "contest_name",
        "platform_account__handle",
    )
    readonly_fields = ("created_at", "updated_at")


admin.site.register(PlatformStatsSnapshot)
