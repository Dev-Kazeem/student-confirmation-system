from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit log entry.

    Rows in this table are never modified or deleted via the application.
    `target_type` + `target_id` point to the affected object without a hard
    FK, so unrelated apps can log against each other without coupling.
    """

    class Action(models.TextChoices):
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        REGISTER = "REGISTER", "Registration"
        PROFILE_UPDATE = "PROFILE_UPDATE", "Profile Update"
        DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD", "Document Upload"
        DOCUMENT_REPLACE = "DOCUMENT_REPLACE", "Document Replacement"
        DOCUMENT_REVIEW = "DOCUMENT_REVIEW", "Document Review"
        APPLICATION_SUBMIT = "APPLICATION_SUBMIT", "Application Submission"
        APPLICATION_REVIEW = "APPLICATION_REVIEW", "Application Review"
        CORRECTION_REQUEST = "CORRECTION_REQUEST", "Correction Request"
        APPLICATION_APPROVE = "APPLICATION_APPROVE", "Application Approval"
        APPLICATION_REJECT = "APPLICATION_REJECT", "Application Rejection"
        SLIP_GENERATE = "SLIP_GENERATE", "Confirmation Slip Generation"
        SLIP_REVOKE = "SLIP_REVOKE", "Confirmation Slip Revocation"
        ROLE_CHANGE = "ROLE_CHANGE", "User Role Modification"
        ACCOUNT_DEACTIVATE = "ACCOUNT_DEACTIVATE", "Account Deactivation"
        ACCOUNT_REACTIVATE = "ACCOUNT_REACTIVATE", "Account Reactivation"
        ADMISSION_IMPORT = "ADMISSION_IMPORT", "Admission Record Import"
        OTHER = "OTHER", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    description = models.TextField(blank=True)

    # Generic target reference (no hard FK to avoid coupling)
    target_type = models.CharField(max_length=60, blank=True)
    target_id = models.CharField(max_length=60, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        who = self.user or "anonymous"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} — {self.get_action_display()}"

    # ------------------------------------------------------------------
    # Convenience constructor — MUST be present for signals to work
    # ------------------------------------------------------------------
    @classmethod
    def record(
        cls,
        *,
        user=None,
        action,
        description="",
        target=None,
        ip_address=None,
        user_agent="",
    ):
        """
        Create an audit log entry.

        Usage:
            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.LOGIN,
                description="Signed in",
                ip_address=get_client_ip(request),
            )
        """
        target_type = ""
        target_id = ""
        if target is not None:
            target_type = target.__class__.__name__
            target_id = str(getattr(target, "pk", "") or "")

        # Only store the user if they're actually authenticated.
        safe_user = user if getattr(user, "is_authenticated", False) else None

        return cls.objects.create(
            user=safe_user,
            action=action,
            description=description,
            target_type=target_type,
            target_id=target_id,
            ip_address=ip_address,
            user_agent=(user_agent or "")[:255],
        )