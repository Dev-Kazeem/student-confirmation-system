import uuid

from django.conf import settings
from django.db import models


class ConfirmationSlip(models.Model):
    """
    A digital confirmation slip generated after an application is approved.

    - One slip per approved application.
    - The slip exposes a public verification reference (`verification_code`)
      used by the public verification page and the QR code.
    - No sensitive student data is embedded in the QR code itself; only the
      verification URL.
    """

    class Status(models.TextChoices):
        VALID = "VALID", "Valid"
        REVOKED = "REVOKED", "Revoked"

    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="confirmation_slip",
    )
    verification_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Public verification code embedded in the QR code.",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.VALID, db_index=True
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_slips",
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoke_reason = models.TextField(blank=True)

    # Cached PDF path (regeneration writes a new file)
    pdf_file = models.FileField(
        upload_to="confirmation_slips/%Y/%m/", null=True, blank=True
    )

    class Meta:
        ordering = ["-generated_at"]
        indexes = [
            models.Index(fields=["verification_code"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Slip for {self.application.reference}"

    @property
    def is_valid(self) -> bool:
        return self.status == self.Status.VALID