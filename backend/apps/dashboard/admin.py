from django.contrib import admin

from apps.dashboard.models import ProfileSnapshot


@admin.register(ProfileSnapshot)
class ProfileSnapshotAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"external_account",
		"display_name",
		"rating",
		"highest_rating",
		"captured_at",
	)
	list_filter = ("external_account__source", "captured_at")
	search_fields = (
		"external_account__user__username",
		"external_account__handle_or_slug",
		"display_name",
	)
	readonly_fields = ("created_at",)
