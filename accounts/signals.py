from django.contrib.auth import get_user_model
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
)
from django.db.models.signals import post_save
from django.dispatch import receiver

from auditlogs.models import AuditLog
from auditlogs.utils import get_client_ip

from .models import StudentProfile

User = get_user_model()


# ---------------------------------------------------------------------------
# Auto-create a StudentProfile when a student user is created
# ---------------------------------------------------------------------------
@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    """
    Every student gets a StudentProfile.

    If a phone number was stashed on the instance during registration
    (`_pending_phone_number`), prefill it on the profile.
    """
    if not created or instance.role != User.Role.STUDENT:
        return
    profile, _ = StudentProfile.objects.get_or_create(
        user=instance,
        defaults={
            "full_name": instance.get_full_name(),
            "phone_number": getattr(instance, "_pending_phone_number", "") or "",
        },
    )


# ---------------------------------------------------------------------------
# Audit log on login / logout
# ---------------------------------------------------------------------------
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.record(
        user=user,
        action=AuditLog.Action.LOGIN,
        description=f"User {user.username} logged in.",
        ip_address=get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else "")[:255],
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user is None:
        return
    AuditLog.record(
        user=user,
        action=AuditLog.Action.LOGOUT,
        description=f"User {user.username} logged out.",
        ip_address=get_client_ip(request),
        user_agent=(request.META.get("HTTP_USER_AGENT", "") if request else "")[:255],
    )