from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.decorators import student_required
from auditlogs.models import AuditLog
from auditlogs.utils import get_client_ip
from documents.services import missing_required_document_types

from .forms import ApplicationForm
from .mixins import StudentOwnsApplicationMixin
from .models import Application
from .services import get_or_create_draft_for_student, submit_application


# ---------------------------------------------------------------------------
# Entry point: "start or continue my application"
# ---------------------------------------------------------------------------
@student_required
def start_or_continue(request):
    """
    Route the student to:
      - admission check if they haven't claimed a record,
      - profile edit if their profile is incomplete,
      - otherwise the application preview page.
    """
    profile = request.user.student_profile
    if not profile.admission_record_id:
        messages.info(request, "Please claim your admission record first.")
        return redirect("admissions:check_admission")

    profile.refresh_completion()
    if not profile.is_complete:
        messages.info(request, "Please complete your profile before continuing.")
        return redirect("accounts:student_profile_edit")

    application = get_or_create_draft_for_student(request.user)
    return redirect("applications:preview", reference=application.reference)


# ---------------------------------------------------------------------------
# Preview + submit
# ---------------------------------------------------------------------------
class ApplicationPreviewView(StudentOwnsApplicationMixin, View):
    template_name = "applications/preview.html"

    def get(self, request, *args, **kwargs):
        application = self.application
        profile = request.user.student_profile
        profile.refresh_completion()
        missing_docs = missing_required_document_types(application)
        form = ApplicationForm(application=application)
        return render(
            request,
            self.template_name,
            {
                "application": application,
                "profile": profile,
                "missing_docs": missing_docs,
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        application = self.application
        form = ApplicationForm(request.POST, application=application)
        if not form.is_valid():
            messages.error(request, "Please confirm the declaration before submitting.")
            return self.get(request, *args, **kwargs)

        try:
            submit_application(application, by_user=request.user)
            messages.success(request, "Application submitted successfully.")
            return redirect("applications:status", reference=application.reference)
        except ValueError as exc:
            messages.error(request, str(exc))
            return self.get(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Status page
# ---------------------------------------------------------------------------
class ApplicationStatusView(StudentOwnsApplicationMixin, View):
    template_name = "applications/status.html"

    def get(self, request, *args, **kwargs):
        application = self.application
        # Progress stages used by the template
        stages = [
            (Application.Status.DRAFT, "Draft"),
            (Application.Status.SUBMITTED, "Submitted"),
            (Application.Status.UNDER_REVIEW, "Under Review"),
            (Application.Status.CORRECTION_REQUIRED, "Correction Required"),
            (Application.Status.RESUBMITTED, "Resubmitted"),
            (Application.Status.APPROVED, "Approved"),
        ]
        return render(
            request,
            self.template_name,
            {"application": application, "stages": stages},
        )