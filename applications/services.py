"""
Application lifecycle helpers.

Keeping workflow rules here means views, admin actions, and future management
commands all enforce the same logic.
"""

from django.db import transaction
from django.utils import timezone

from auditlogs.models import AuditLog
from documents.services import missing_required_document_types
from notifications.models import Notification

from .models import Application, ApplicationReview


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------
def get_or_create_draft_for_student(student) -> Application:
    """
    Return the student's DRAFT application for their claimed admission session,
    creating it if it doesn't exist.

    Raises ValueError if the student hasn't claimed an admission record.
    """
    profile = student.student_profile
    record = profile.admission_record
    if record is None:
        raise ValueError("Student has not claimed an admission record.")

    application, _ = Application.objects.get_or_create(
        student=student,
        session=record.session,
        defaults={"admission_record": record, "status": Application.Status.DRAFT},
    )
    return application


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------
def can_submit(application) -> tuple[bool, list[str]]:
    """
    Return (allowed, reasons). Reasons is a list of human-readable strings.
    """
    reasons = []

    profile = application.student.student_profile
    profile.refresh_completion()
    if not profile.is_complete:
        reasons.append("Your profile is incomplete.")

    if application.status not in (
        Application.Status.DRAFT,
        Application.Status.CORRECTION_REQUIRED,
    ):
        reasons.append("This application cannot be submitted in its current state.")

    missing = missing_required_document_types(application)
    if missing:
        names = ", ".join(dt.name for dt in missing)
        reasons.append(f"Missing required documents: {names}.")

    return (not reasons), reasons


@transaction.atomic
def submit_application(application, *, by_user):
    """
    Transition an application to SUBMITTED (or RESUBMITTED if it was
    previously returned for correction) and record the action.
    """
    allowed, reasons = can_submit(application)
    if not allowed:
        raise ValueError("; ".join(reasons))

    was_correction = application.status == Application.Status.CORRECTION_REQUIRED

    application.status = (
        Application.Status.RESUBMITTED if was_correction else Application.Status.SUBMITTED
    )
    application.submitted_at = timezone.now()
    application.save(update_fields=["status", "submitted_at", "updated_at"])

    ApplicationReview.objects.create(
        application=application,
        reviewer=by_user,
        action=(
            ApplicationReview.Action.RESUBMITTED
            if was_correction
            else ApplicationReview.Action.SUBMITTED
        ),
        comment="Student submitted the application.",
    )

    AuditLog.record(
        user=by_user,
        action=AuditLog.Action.APPLICATION_SUBMIT,
        description=(
            f"Resubmitted application {application.reference}."
            if was_correction
            else f"Submitted application {application.reference}."
        ),
        target=application,
    )

    Notification.objects.create(
        recipient=by_user,
        title="Application submitted",
        message=(
            "Your confirmation application has been submitted successfully. "
            "You will be notified when it is reviewed."
        ),
        type=Notification.Type.APPLICATION_SUBMITTED,
        link_url="/applications/status/",
    )

    return application


# ---------------------------------------------------------------------------
# Officer actions
# ---------------------------------------------------------------------------
@transaction.atomic
def start_review(application, *, officer):
    """Move SUBMITTED or RESUBMITTED → UNDER_REVIEW."""
    if application.status not in (
        Application.Status.SUBMITTED,
        Application.Status.RESUBMITTED,
    ):
        raise ValueError("Application is not in a state that can be reviewed.")

    application.status = Application.Status.UNDER_REVIEW
    application.reviewing_officer = officer
    application.reviewed_at = timezone.now()
    application.save(update_fields=["status", "reviewing_officer", "reviewed_at", "updated_at"])

    ApplicationReview.objects.create(
        application=application,
        reviewer=officer,
        action=ApplicationReview.Action.STARTED_REVIEW,
        comment="Review started.",
    )
    AuditLog.record(
        user=officer,
        action=AuditLog.Action.APPLICATION_REVIEW,
        description=f"Started review of {application.reference}.",
        target=application,
    )
    return application


@transaction.atomic
def request_correction(application, *, officer, reason: str):
    """UNDER_REVIEW → CORRECTION_REQUIRED. Requires a reason."""
    if application.status != Application.Status.UNDER_REVIEW:
        raise ValueError("Only applications under review can be sent back for correction.")
    if not reason.strip():
        raise ValueError("A reason is required when requesting correction.")

    application.status = Application.Status.CORRECTION_REQUIRED
    application.review_comment = reason
    application.save(update_fields=["status", "review_comment", "updated_at"])

    ApplicationReview.objects.create(
        application=application,
        reviewer=officer,
        action=ApplicationReview.Action.REQUESTED_CORRECTION,
        comment=reason,
    )
    AuditLog.record(
        user=officer,
        action=AuditLog.Action.CORRECTION_REQUEST,
        description=f"Requested correction on {application.reference}.",
        target=application,
    )
    Notification.objects.create(
        recipient=application.student,
        title="Correction required",
        message=(
            "Your application needs corrections. Please review the officer's comments "
            "and resubmit."
        ),
        type=Notification.Type.CORRECTION_REQUESTED,
        link_url=f"/applications/{application.reference}/status/",
    )
    return application


@transaction.atomic
def approve_application(application, *, officer, comment: str = ""):
    """UNDER_REVIEW → APPROVED."""
    if application.status != Application.Status.UNDER_REVIEW:
        raise ValueError("Only applications under review can be approved.")

    application.status = Application.Status.APPROVED
    application.approved_at = timezone.now()
    application.reviewing_officer = officer
    if comment:
        application.review_comment = comment
    application.save(
        update_fields=["status", "approved_at", "reviewing_officer", "review_comment", "updated_at"]
    )

    ApplicationReview.objects.create(
        application=application,
        reviewer=officer,
        action=ApplicationReview.Action.APPROVED,
        comment=comment or "Application approved.",
    )
    AuditLog.record(
        user=officer,
        action=AuditLog.Action.APPLICATION_APPROVE,
        description=f"Approved application {application.reference}.",
        target=application,
    )
    Notification.objects.create(
        recipient=application.student,
        title="Application approved",
        message=(
            "Congratulations! Your confirmation application has been approved. "
            "Your confirmation slip is now available."
        ),
        type=Notification.Type.APPLICATION_APPROVED,
        link_url=f"/applications/{application.reference}/status/",
    )
    return application


@transaction.atomic
def reject_application(application, *, officer, reason: str):
    """UNDER_REVIEW → REJECTED. Requires a reason."""
    if application.status != Application.Status.UNDER_REVIEW:
        raise ValueError("Only applications under review can be rejected.")
    if not reason.strip():
        raise ValueError("A reason is required when rejecting an application.")

    application.status = Application.Status.REJECTED
    application.rejected_at = timezone.now()
    application.rejection_reason = reason
    application.reviewing_officer = officer
    application.save(
        update_fields=[
            "status",
            "rejected_at",
            "rejection_reason",
            "reviewing_officer",
            "updated_at",
        ]
    )

    ApplicationReview.objects.create(
        application=application,
        reviewer=officer,
        action=ApplicationReview.Action.REJECTED,
        comment=reason,
    )
    AuditLog.record(
        user=officer,
        action=AuditLog.Action.APPLICATION_REJECT,
        description=f"Rejected application {application.reference}.",
        target=application,
    )
    Notification.objects.create(
        recipient=application.student,
        title="Application rejected",
        message=f"Your application was rejected. Reason: {reason}",
        type=Notification.Type.APPLICATION_REJECTED,
        link_url=f"/applications/{application.reference}/status/",
    )
    return application