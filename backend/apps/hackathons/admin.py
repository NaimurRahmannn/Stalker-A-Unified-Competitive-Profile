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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append("owner")
        return readonly


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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append("owner")
        return readonly


@admin.register(HackathonSubmission)
class HackathonSubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "event",
        "owner",
        "status",
        "source",
        "submitted_at",
        "created_at",
    ]
    list_filter = ["status", "source", "created_at"]
    search_fields = [
        "project__title",
        "event__name",
        "owner__username",
    ]
    raw_id_fields = ["owner", "project", "event"]
    readonly_fields = ["created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.extend(["owner", "project", "event"])
        return readonly


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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.extend(["user", "event"])
        return readonly


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

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:
            readonly.append("participation")
        return readonly
