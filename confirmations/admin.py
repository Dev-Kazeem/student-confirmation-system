from django.contrib import admin, messages

from .models import ConfirmationSlip
from .services import revoke_slip


@admin.register(ConfirmationSlip)
class ConfirmationSlipAdmin(admin.ModelAdmin):
    list_display = ("application", "verification_code", "status", "generated_at", "generated_by")
    list_filter = ("status", "generated_at")
    search_fields = (
        "application__reference",
        "verification_code",
        "application__student__username",
        "application__student__first_name",
        "application__student__last_name",
    )
    readonly_fields = ("verification_code", "generated_at", "revoked_at")
    autocomplete_fields = ("application", "generated_by")
    actions = ["action_revoke"]

    @admin.action(description="Revoke selected confirmation slips")
    def action_revoke(self, request, queryset):
        count = 0
        for slip in queryset:
            if slip.status != ConfirmationSlip.Status.REVOKED:
                revoke_slip(slip, by_user=request.user, reason="Revoked from admin.")
                count += 1
        self.message_user(request, f"Revoked {count} slip(s).", messages.SUCCESS)