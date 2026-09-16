from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "action", "target_type", "ip_address")
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "description", "target_id")
    readonly_fields = (
        "user",
        "action",
        "description",
        "target_type",
        "target_id",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False