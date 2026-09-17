"""
Document helper functions — required-document detection and upload validation.
"""
import django.utils.timezone as tz  # noqa: E402

from auditlogs.models import AuditLog  # noqa: E402
from notifications.models import Notification  # noqa: E402
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




def review_document(document, *, officer, status: str, comment: str = ""):
    """
    Set a document's review status and record the action.

    status must be one of Document.Status.{ACCEPTED, REJECTED, CORRECTION_REQUIRED}.

    Sending a document back for correction also flips its parent application
    into CORRECTION_REQUIRED if that application is currently UNDER_REVIEW.
    """
    from applications.models import Application  # avoid circular import

    if status not in (
        Document.Status.ACCEPTED,
        Document.Status.REJECTED,
        Document.Status.CORRECTION_REQUIRED,
    ):
        raise ValueError("Invalid document status.")
    if status in (Document.Status.REJECTED, Document.Status.CORRECTION_REQUIRED) and not comment.strip():
        raise ValueError("A comment is required for rejection or correction.")

    document.status = status
    document.review_comment = comment
    document.reviewed_by = officer
    document.reviewed_at = tz.now()
    document.save(update_fields=["status", "review_comment", "reviewed_by", "reviewed_at", "updated_at"])

    AuditLog.record(
        user=officer,
        action=AuditLog.Action.DOCUMENT_REVIEW,
        description=f"Marked document '{document.document_type.name}' as {status}.",
        target=document,
    )

    if status in (Document.Status.REJECTED, Document.Status.CORRECTION_REQUIRED):
        Notification.objects.create(
            recipient=document.application.student,
            title=f"Document {document.get_status_display().lower()}",
            message=(
                f"Your document '{document.document_type.name}' requires attention: "
                f"{comment}"
            ),
            type=Notification.Type.DOCUMENT_REJECTED,
            link_url=f"/documents/{document.application.reference}/manage/",
        )
        # Send the whole application back for correction
        if document.application.status == Application.Status.UNDER_REVIEW:
            document.application.status = Application.Status.CORRECTION_REQUIRED
            document.application.review_comment = (
                f"Document '{document.document_type.name}' requires correction: {comment}"
            )
            document.application.save(update_fields=["status", "review_comment", "updated_at"])

    return document