from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import student_required
from applications.models import Application
from auditlogs.models import AuditLog

from .models import ConfirmationSlip
from .services import generate_slip

from .qr import generate_qr_png



# ---------------------------------------------------------------------------
# Download / print (owner or staff)
# ---------------------------------------------------------------------------
@login_required
def slip_detail(request, verification_code):
    slip = get_object_or_404(
        ConfirmationSlip.objects.select_related(
            "application__student",
            "application__admission_record__department",
            "application__admission_record__programme",
            "application__session",
        ),
        verification_code=verification_code,
    )

    user = request.user
    is_owner = slip.application.student_id == user.pk
    is_staff = user.is_officer or user.is_admin_role or user.is_superuser
    if not (is_owner or is_staff):
        messages.error(request, "You do not have access to that slip.")
        return redirect("accounts:redirect_after_login")

    return render(request, "confirmations/slip.html", {"slip": slip})


@login_required
def slip_download(request, verification_code):
    slip = get_object_or_404(ConfirmationSlip, verification_code=verification_code)
    user = request.user
    is_owner = slip.application.student_id == user.pk
    is_staff = user.is_officer or user.is_admin_role or user.is_superuser
    if not (is_owner or is_staff):
        messages.error(request, "You do not have access to that slip.")
        return redirect("accounts:redirect_after_login")

    if not slip.pdf_file:
        messages.error(request, "The PDF for this slip is not available yet.")
        return redirect("confirmations:slip_detail", verification_code=verification_code)

    try:
        f = slip.pdf_file.open("rb")
    except FileNotFoundError as exc:
        raise Http404("File not found.") from exc

    return FileResponse(
        f,
        as_attachment=True,
        filename=f"confirmation-slip-{slip.application.reference}.pdf",
    )


# ---------------------------------------------------------------------------
# Student entry point: view my slip
# ---------------------------------------------------------------------------
@student_required
def my_slip(request):
    """
    If the student's latest application is APPROVED, ensure a slip exists
    and redirect to it. Otherwise show a friendly message.
    """
    application = (
        Application.objects.filter(student=request.user)
        .order_by("-created_at")
        .first()
    )
    if application is None:
        messages.info(request, "You have not started an application yet.")
        return redirect("accounts:student_dashboard")

    if application.status != Application.Status.APPROVED:
        messages.info(request, "Your confirmation slip will be available once your application is approved.")
        return redirect("applications:status", reference=application.reference)

    slip = generate_slip(application, by_user=request.user)
    return redirect("confirmations:slip_detail", verification_code=slip.verification_code)


# ---------------------------------------------------------------------------
# Public verification (no login)
# ---------------------------------------------------------------------------
def verify_slip(request):
    """
    Public verification page.

    - Accepts ?code=<uuid> (from QR) or a POST with a code.
    - Shows minimal info: student name, programme, session, verification result.
    - Never exposes sensitive data such as phone, address, or DOB.
    """
    code = (request.GET.get("code") or request.POST.get("code") or "").strip()
    slip = None
    result = None  # "valid" | "revoked" | "not_found"

    if code:
        try:
            slip = ConfirmationSlip.objects.select_related(
                "application__student",
                "application__admission_record__programme",
                "application__admission_record__department",
                "application__session",
            ).get(verification_code=code)
            result = "valid" if slip.status == ConfirmationSlip.Status.VALID else "revoked"
        except ConfirmationSlip.DoesNotExist:
            result = "not_found"
        except Exception:  # noqa: BLE001
            result = "not_found"

        AuditLog.record(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.Action.OTHER,
            description=f"Public verification lookup for code {code}: {result}.",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

    return render(
        request,
        "confirmations/verify.html",
        {"code": code, "slip": slip, "result": result},
    )



def slip_qr_image(request, verification_code):
    """
    Return the QR PNG for a given slip. Public — no login required.
    The QR only contains a URL to the verification page.
    """
    slip = get_object_or_404(ConfirmationSlip, verification_code=verification_code)
    png = generate_qr_png(slip.verification_code)
    return HttpResponse(png.read(), content_type="image/png")    