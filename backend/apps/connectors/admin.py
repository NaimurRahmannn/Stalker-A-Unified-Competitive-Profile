from django.contrib import admin

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
        "solved_count",
        "attempted_count",
        "indexed_submission_count",
        "submission_backfill_complete",
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


@admin.register(AtCoderSubmissionSyncState)
class AtCoderSubmissionSyncStateAdmin(admin.ModelAdmin):
    list_display = (
        "platform_account",
        "last_submission_epoch",
        "last_submission_id",
        "backfill_complete",
        "progress_status",
        "blocked_reason",
        "submission_data_updated_at",
    )
    list_filter = ("backfill_complete", "progress_status")
    search_fields = ("platform_account__handle",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AtCoderSyncState)
class AtCoderSyncStateAdmin(admin.ModelAdmin):
    list_display = (
        "platform_account",
        "overall_status",
        "rating_status",
        "submission_status",
        "rating_sync_attempted_at",
        "submission_sync_attempted_at",
    )
    list_filter = ("overall_status", "rating_status", "submission_status")
    search_fields = ("platform_account__handle",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AtCoderSubmission)
class AtCoderSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "external_submission_id",
        "platform_account",
        "external_problem_id",
        "verdict",
        "language",
        "submitted_at",
    )
    list_filter = ("verdict",)
    search_fields = (
        "platform_account__handle",
        "external_problem_id",
        "external_contest_id",
    )
    readonly_fields = ("created_at", "updated_at")


admin.site.register(PlatformStatsSnapshot)
