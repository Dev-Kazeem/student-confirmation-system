from django.conf import settings
from django.db import models


class Notification(models.Model):
    """
    In-app notification delivered to a user.

    Email delivery is a separate concern handled in Phase Seven; this model
    only stores the in-app copy so that a delivery failure never breaks the
    application workflow.
    """

    class Type(models.TextChoices):
        APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED", "Application Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        CORRECTION_REQUESTED = "CORRECTION_REQUESTED", "Correction Requested"
        DOCUMENT_REJECTED = "DOCUMENT_REJECTED", "Document Rejected"
        APPLICATION_APPROVED = "APPLICATION_APPROVED", "Application Approved"
        APPLICATION_REJECTED = "APPLICATION_REJECTED", "Application Rejected"
        SLIP_GENERATED = "SLIP_GENERATED", "Confirmation Slip Generated"
        ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(
        max_length=30, choices=Type.choices, default=Type.SYSTEM, db_index=True
    )
    is_read = models.BooleanField(default=False, db_index=True)

    # Optional link to related object (kept loose to avoid circular FKs)
    link_url = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_type_display()}] → {self.recipient}"