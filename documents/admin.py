from django.contrib import admin

from .models import Document, DocumentType


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_required", "is_active", "max_size_mb")
    list_filter = ("is_required", "is_active")
    search_fields = ("name", "code")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "document_type",
        "status",
        "file_size",
        "uploaded_at",
        "reviewed_by",
    )
    list_filter = ("status", "document_type")
    search_fields = (
        "application__reference",
        "application__student__username",
        "original_filename",
    )
    autocomplete_fields = ("application", "document_type", "reviewed_by", "replaced_by")
    readonly_fields = ("uploaded_at", "updated_at", "file_size")