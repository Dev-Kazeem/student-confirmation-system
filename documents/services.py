"""
Document helper functions — required-document detection and upload validation.
"""

from .models import Document, DocumentType


def missing_required_document_types(application) -> list[DocumentType]:
    """
    Return the list of active DocumentTypes marked as required that do NOT
    have a currently-active document (replaced_by IS NULL) on this application.
    """
    required = DocumentType.objects.filter(is_required=True, is_active=True)
    uploaded_type_ids = set(
        Document.objects.filter(
            application=application,
            replaced_by__isnull=True,
        ).values_list("document_type_id", flat=True)
    )
    return [dt for dt in required if dt.pk not in uploaded_type_ids]


def validate_upload(*, document_type: DocumentType, uploaded_file) -> tuple[bool, str]:
    """
    Server-side validation of a file against a DocumentType's rules.

    Returns (ok, error_message).
    """
    if uploaded_file is None:
        return False, "No file was provided."

    name = (uploaded_file.name or "").lower()
    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    allowed = document_type.allowed_extensions_list()
    if ext not in allowed:
        return False, f"Only {', '.join(allowed)} files are allowed for {document_type.name}."

    max_bytes = document_type.max_size_mb * 1024 * 1024
    if uploaded_file.size > max_bytes:
        return False, f"{document_type.name} must be at most {document_type.max_size_mb} MB."

    if uploaded_file.size <= 0:
        return False, "The uploaded file is empty."

    return True, ""