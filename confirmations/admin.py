from django.contrib import admin

from .models import ConfirmationSlip


@admin.register(ConfirmationSlip)
class ConfirmationSlipAdmin(admin.ModelAdmin):
    list_display = ("application", "verification_code", "status", "generated_at")
    list_filter = ("status",)
    search_fields = (
        "application__reference",
        "verification_code",
        "application__student__username",
    )
    readonly_fields = ("verification_code", "generated_at")
    autocomplete_fields = ("application", "generated_by")