from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import student_required
from auditlogs.models import AuditLog
from auditlogs.utils import get_client_ip
from notifications.models import Notification

from .forms import AdmissionCheckForm
from .models import AdmissionRecord


# ---------------------------------------------------------------------------
# Public admission check (no login required)
# ---------------------------------------------------------------------------
def check_admission(request):
    """
    Public page: enter JAMB or admission number → see a summary.

    Does NOT reveal personal data. Only shows enough for the student to
    recognize the record (name, department, programme, session, status).
    """
    record = None
    searched = False

    if request.method == "POST":
        form = AdmissionCheckForm(request.POST)
        if form.is_valid():
            searched = True
            record = form.lookup()
            if record is None:
                messages.warning(
                    request,
                    "No admission record matches that number. Please check and try again.",
                )
            else:
                messages.success(request, "Admission record found.")
    else:
        form = AdmissionCheckForm()

    return render(
        request,
        "admissions/check_admission.html",
        {"form": form, "record": record, "searched": searched},
    )


# ---------------------------------------------------------------------------
# Claim an admission record (login required, student only)
# ---------------------------------------------------------------------------
@student_required
def claim_admission(request, jamb_number: str):
    """
    Link an admission record to the logged-in student's profile.

    Rules:
      - The record must exist and be PENDING.
      - The student must not have already claimed a record.
      - The record must not be claimed by another user.
    """
    record = get_object_or_404(AdmissionRecord, jamb_number=jamb_number)
    profile = request.user.student_profile

    # Already claimed by this user → just redirect
    if profile.admission_record_id == record.pk:
        messages.info(request, "You have already claimed this admission record.")
        return redirect("admissions:my_admission")

    # Someone else already claimed it
    if record.claimed_by_id and record.claimed_by_id != request.user.pk:
        messages.error(
            request,
            "This admission record has already been claimed by another user. "
            "Please contact the admissions office if you believe this is an error.",
        )
        return redirect("admissions:check_admission")

    # Student already has another claim
    if profile.admission_record_id and profile.admission_record_id != record.pk:
        messages.error(
            request,
            "You have already claimed a different admission record. "
            "Contact the admissions office to resolve this.",
        )
        return redirect("admissions:my_admission")

    if record.status != AdmissionRecord.Status.PENDING:
        messages.error(
            request,
            f"This record cannot be claimed (status: {record.get_status_display()}).",
        )
        return redirect("admissions:check_admission")

    # Confirm page (POST to actually claim)
    if request.method == "POST":
        with transaction.atomic():
            record.status = AdmissionRecord.Status.CLAIMED
            record.claimed_by = request.user
            record.claimed_at = timezone.now()
            record.save(update_fields=["status", "claimed_by", "claimed_at", "updated_at"])

            profile.admission_record = record
            profile.jamb_number = record.jamb_number
            profile.admission_number = record.admission_number or ""
            profile.claimed_at = timezone.now()
            if not profile.full_name:
                profile.full_name = record.student_name
            profile.refresh_completion(save=False)
            profile.save()

            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.OTHER,
                description=f"Claimed admission record {record.jamb_number}.",
                target=record,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
            Notification.objects.create(
                recipient=request.user,
                title="Admission record claimed",
                message=(
                    f"You have successfully claimed your admission record for "
                    f"{record.session.name}. Complete your profile to continue."
                ),
                type=Notification.Type.SYSTEM,
                link_url="/accounts/student/profile/",
            )

        messages.success(
            request,
            "Admission record claimed. Please complete your profile.",
        )
        return redirect("accounts:student_profile")

    return render(
        request,
        "admissions/confirm_claim.html",
        {"record": record},
    )


# ---------------------------------------------------------------------------
# My admission (student sees their claimed record)
# ---------------------------------------------------------------------------
@student_required
def my_admission(request):
    profile = request.user.student_profile
    record = profile.admission_record
    return render(
        request,
        "admissions/my_admission.html",
        {"record": record, "profile": profile},
    )