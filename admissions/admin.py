from django.contrib import admin

from .models import AdmissionRecord, AdmissionSession, Department, Programme


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "department", "degree_type", "is_active")
    search_fields = ("name", "code")
    list_filter = ("department", "degree_type", "is_active")
    autocomplete_fields = ("department",)


@admin.register(AdmissionSession)
class AdmissionSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(AdmissionRecord)
class AdmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        "student_name",
        "jamb_number",
        "admission_number",
        "department",
        "programme",
        "session",
        "status",
    )
    search_fields = ("student_name", "jamb_number", "admission_number")
    list_filter = ("status", "department", "programme", "session")
    autocomplete_fields = ("department", "programme", "session")
    readonly_fields = ("created_at", "updated_at", "claimed_at")