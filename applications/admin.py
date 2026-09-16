from django.contrib import admin

from .models import Application, ApplicationReview


class ApplicationReviewInline(admin.TabularInline):
    model = ApplicationReview
    extra = 0
    readonly_fields = ("reviewer", "action", "comment", "created_at")
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "student",
        "session",
        "status",
        "submitted_at",
        "reviewing_officer",
    )
    list_filter = ("status", "session")
    search_fields = (
        "reference",
        "student__username",
        "student__first_name",
        "student__last_name",
        "admission_record__jamb_number",
        "admission_record__admission_number",
    )
    autocomplete_fields = ("student", "admission_record", "session", "reviewing_officer")
    readonly_fields = ("reference", "created_at", "updated_at")
    inlines = [ApplicationReviewInline]


@admin.register(ApplicationReview)
class ApplicationReviewAdmin(admin.ModelAdmin):
    list_display = ("application", "reviewer", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("application__reference", "reviewer__username")
    readonly_fields = ("application", "reviewer", "action", "comment", "created_at")