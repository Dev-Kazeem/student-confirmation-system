import uuid

from django.conf import settings
from django.db import models


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
class Application(models.Model):
    """
    A student's confirmation application.

    Lifecycle:
        DRAFT → SUBMITTED → UNDER_REVIEW →
            CORRECTION_REQUIRED → RESUBMITTED → UNDER_REVIEW → APPROVED
            or REJECTED
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        CORRECTION_REQUIRED = "CORRECTION_REQUIRED", "Correction Required"
        RESUBMITTED = "RESUBMITTED", "Resubmitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    # Terminal / editable statuses useful throughout the app
    EDITABLE_STATUSES = {Status.DRAFT, Status.CORRECTION_REQUIRED}
    SUBMITTED_STATUSES = {
        Status.SUBMITTED,
        Status.UNDER_REVIEW,
        Status.RESUBMITTED,
    }
    FINAL_STATUSES = {Status.APPROVED, Status.REJECTED}

    # --- identity ------------------------------------------------------------
    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Public-facing unique reference.",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    admission_record = models.ForeignKey(
        "admissions.AdmissionRecord",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    session = models.ForeignKey(
        "admissions.AdmissionSession",
        on_delete=models.PROTECT,
        related_name="applications",
    )

    # --- status --------------------------------------------------------------
    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    # --- timeline ------------------------------------------------------------
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)

    reviewing_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_applications",
    )
    review_comment = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # --- meta ----------------------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # One application per student per session
            models.UniqueConstraint(
                fields=["student", "session"], name="unique_application_per_session"
            ),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["student", "session"]),
        ]

    # --- helpers -------------------------------------------------------------
    @property
    def is_editable(self) -> bool:
        return self.status in self.EDITABLE_STATUSES

    @property
    def is_submitted(self) -> bool:
        return self.status in self.SUBMITTED_STATUSES

    @property
    def is_final(self) -> bool:
        return self.status in self.FINAL_STATUSES

    def __str__(self) -> str:
        return f"App {self.reference} — {self.student} ({self.get_status_display()})"


# ---------------------------------------------------------------------------
# Application Review
# ---------------------------------------------------------------------------
class ApplicationReview(models.Model):
    """
    An immutable record of every review action taken on an application.

    One application can have many reviews over its lifetime.
    """

    class Action(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        STARTED_REVIEW = "STARTED_REVIEW", "Started Review"
        REQUESTED_CORRECTION = "REQUESTED_CORRECTION", "Requested Correction"
        RESUBMITTED = "RESUBMITTED", "Resubmitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        COMMENT = "COMMENT", "Comment"

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="application_reviews",
    )
    action = models.CharField(max_length=25, choices=Action.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} on {self.application.reference}"