from django.contrib import admin

from .models import KaggleCollectionRun


@admin.register(KaggleCollectionRun)
class KaggleCollectionRunAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "status", "trigger", "provider_name", "attempt_count",
                    "created_at", "finished_at", "error_code")
    list_filter = ("status", "trigger", "provider_name", "created_at", "error_code")
    search_fields = ("id", "profile__normalized_username")
    readonly_fields = tuple(field.name for field in KaggleCollectionRun._meta.fields)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
