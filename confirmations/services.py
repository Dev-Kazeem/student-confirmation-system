"""
Confirmation slip lifecycle: generation, revocation, PDF caching.
"""

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from applications.models import Application
from auditlogs.models import AuditLog
from notifications.services import notify
from notifications.models import Notification

from .models import ConfirmationSlip
from .pdf import build_slip_pdf


@transaction.atomic
def generate_slip(application: Application, *, by_user) -> ConfirmationSlip:
    """
    Create (or return) the ConfirmationSlip for an APPROVED application.

    Idempotent: if a slip already exists, it is returned unchanged.
    """
    if application.status != Application.Status.APPROVED:
        raise ValueError("Only approved applications can generate a confirmation slip.")

    slip, created = ConfirmationSlip.objects.get_or_create(
        application=application,
        defaults={"generated_by": by_user},
    )

    if created:
        # Build and store the PDF
        pdf_io = build_slip_pdf(slip=slip)
        filename = f"slip-{application.reference}.pdf"
        slip.pdf_file.save(filename, ContentFile(pdf_io.read()), save=True)

        AuditLog.record(
            user=by_user,
            action=AuditLog.Action.SLIP_GENERATE,
            description=f"Generated confirmation slip for {application.reference}.",
            target=slip,
        )

        notify(
            recipient=application.student,
            title="Confirmation slip ready",
            message=(
                "Your confirmation slip is now available for download. "
                "You can also verify it publicly using the code on the slip."
            ),
            notification_type=Notification.Type.SLIP_GENERATED,
            link_url=f"/confirmations/slip/{slip.verification_code}/",
        )

    return slip


@transaction.atomic
def regenerate_slip_pdf(slip: ConfirmationSlip, *, by_user) -> ConfirmationSlip:
    """Force PDF regeneration (e.g., after a template change)."""
    pdf_io = build_slip_pdf(slip=slip)
    filename = f"slip-{slip.application.reference}.pdf"
    slip.pdf_file.save(filename, ContentFile(pdf_io.read()), save=True)
    AuditLog.record(
        user=by_user,
        action=AuditLog.Action.SLIP_GENERATE,
        description=f"Regenerated confirmation slip PDF for {slip.application.reference}.",
        target=slip,
    )
    return slip


@transaction.atomic
def revoke_slip(slip: ConfirmationSlip, *, by_user, reason: str = "") -> ConfirmationSlip:
    """Mark the slip as revoked. Public verification will report it as revoked."""
    if slip.status == ConfirmationSlip.Status.REVOKED:
        return slip
    slip.status = ConfirmationSlip.Status.REVOKED
    slip.revoked_at = timezone.now()
    slip.revoke_reason = reason
    slip.save(update_fields=["status", "revoked_at", "revoke_reason"])

    AuditLog.record(
        user=by_user,
        action=AuditLog.Action.SLIP_REVOKE,
        description=f"Revoked confirmation slip for {slip.application.reference}.",
        target=slip,
    )
    notify(
        recipient=slip.application.student,
        title="Confirmation slip revoked",
        message=f"Your confirmation slip has been revoked. Reason: {reason or 'Not specified.'}",
        notification_type=Notification.Type.SYSTEM,
    )
    return slip