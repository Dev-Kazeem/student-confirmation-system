"""
Notification helpers.

`notify()` is the single entry point for creating in-app notifications and
(optionally) sending a matching email. Email failures NEVER propagate —
they are logged and swallowed so that a broken SMTP server cannot block
application state transitions.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

from .models import Notification

logger = logging.getLogger(__name__)


def notify(
    *,
    recipient,
    title: str,
    message: str,
    notification_type: str = Notification.Type.SYSTEM,
    link_url: str = "",
    send_email: bool = True,
) -> Notification:
    """
    Create an in-app notification and optionally email the recipient.

    Always returns the Notification row, even if the email step fails.
    """
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message,
        type=notification_type,
        link_url=link_url,
    )

    if send_email and getattr(settings, "NOTIFICATIONS_EMAIL_ENABLED", True) and recipient.email:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
        except Exception as exc:  # noqa: BLE001 — we deliberately catch everything
            logger.warning(
                "Email delivery failed for notification %s to %s: %s",
                notification.pk,
                recipient.email,
                exc,
            )
    return notification