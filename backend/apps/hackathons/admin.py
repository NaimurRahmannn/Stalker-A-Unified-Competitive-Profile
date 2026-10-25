from django.contrib import admin

from apps.hackathons.models import (
    HackathonAchievement,
    HackathonEvent,
    HackathonParticipation,
    HackathonProject,
    HackathonSubmission,
)


@admin.register(HackathonEvent)
class HackathonEventAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "owner",
        "organizer",
        "format",
        "source",
        "start_date",
        "end_date",
        "created_at",
    ]
    list_filter = ["format", "source", "created_at"]
    search_fields = ["name", "organizer", "owner__username"]
    raw_id_fields = ["owner"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(HackathonProject)
class HackathonProjectAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "owner",
        "source",
        "is_public",
        "created_at",
    ]
    list_filter = ["source", "is_public", "created_at"]
    search_fields = ["title", "owner__username"]
    raw_id_fields = ["owner"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(HackathonSubmission)
class HackathonSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "event",
        "status",
        "source",
        "submitted_at",
        "created_at",
    ]
    list_filter = ["status", "source", "created_at"]
    search_fields = [
        "project__title",
        "event__name",
        "project__owner__username",
    ]
    raw_id_fields = ["project", "event"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(HackathonParticipation)
class HackathonParticipationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "event",
        "status",
        "team_name",
        "is_public",
        "created_at",
    ]
    list_filter = ["status", "is_public", "created_at"]
    search_fields = ["user__username", "event__name", "team_name"]
    raw_id_fields = ["user", "event"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(HackathonAchievement)
class HackathonAchievementAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "achievement_type",
        "rank",
        "verification_status",
        "participation",
        "created_at",
    ]
    list_filter = ["achievement_type", "verification_status", "created_at"]
    search_fields = [
        "title",
        "participation__user__username",
        "participation__event__name",
    ]
    raw_id_fields = ["participation", "submission"]
    readonly_fields = ["created_at", "updated_at"]
