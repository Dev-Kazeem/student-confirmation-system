from django.core.validators import FileExtensionValidator
from django.db import models


# ---------------------------------------------------------------------------
# Document Type
# ---------------------------------------------------------------------------
class DocumentType(models.Model):
    """
    Configurable document categories (e.g., Admission Letter, JAMB Result).
    Administrators manage these from the admin panel.
    """

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    is_required = models.BooleanField(
        default=True, help_text="Whether every applicant must upload this document."
    )
    is_active = models.BooleanField(default=True)

    allowed_extensions = models.CharField(
        max_length=100,
        default="pdf,jpg,jpeg,png",
        help_text="Comma-separated list of allowed extensions.",
    )
    max_size_mb = models.PositiveSmallIntegerField(
        default=5, help_text="Maximum file size in megabytes."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",") if ext.strip()]


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
class Document(models.Model):
    """
    A file uploaded by a student as part of their application.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        CORRECTION_REQUIRED = "CORRECTION_REQUIRED", "Correction Required"

    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "jpg", "jpeg", "png"]
            )
        ],
    )
    original_filename = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(
        default=0, help_text="Size in bytes, set on save."
    )
    content_type = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=25, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    review_comment = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_documents",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Track replacement history
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaced_documents",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["application", "document_type"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            # At most one *active* (non-replaced) document per type per application.
            # Enforced in business logic; the unique constraint here prevents
            # duplicate uploads of the same type while the previous one is still active.
            models.UniqueConstraint(
                fields=["application", "document_type", "replaced_by"],
                name="unique_active_document_per_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.document_type.name} — {self.application.reference}"

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            try:
                self.file_size = self.file.size
            except (OSError, ValueError):
                self.file_size = 0
        if self.file and not self.original_filename:
            self.original_filename = self.file.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)