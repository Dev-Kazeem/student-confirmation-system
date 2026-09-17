"""
QR code generation for confirmation slips.

The QR encodes only a URL containing the public verification code — no
student data is embedded in the QR itself.
"""

import io

import qrcode
from django.conf import settings


def verification_url(verification_code) -> str:
    base = getattr(settings, "SITE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    path = getattr(settings, "CONFIRMATION_VERIFY_PATH", "/confirmations/verify/")
    return f"{base}{path}?code={verification_code}"


def generate_qr_png(verification_code) -> io.BytesIO:
    """Return an in-memory PNG of the QR code."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(verification_url(verification_code))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer