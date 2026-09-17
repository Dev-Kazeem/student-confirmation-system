from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from accounts.decorators import officer_required, student_required
from auditlogs.models import AuditLog
from documents.services import missing_required_document_types, review_document

from .forms import (
    ApplicationForm,
    ApproveApplicationForm,
    CorrectionRequestForm,
    RejectApplicationForm,
)
from .mixins import StudentOwnsApplicationMixin
from .models import Application, ApplicationReview
from .services import (
    approve_application,
    get_or_create_draft_for_student,
    reject_application,
    request_correction,
    start_review,
    submit_application,
)


# ===========================================================================
# STUDENT-SIDE VIEWS (from Phase Five — kept here, do not remove)
# ===========================================================================
@student_required
def start_or_continue(request):
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


class ApplicationStatusView(StudentOwnsApplicationMixin, View):
    template_name = "applications/status.html"

    def get(self, request, *args, **kwargs):
        application = self.application
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


# ===========================================================================
# OFFICER-SIDE VIEWS
# ===========================================================================
@officer_required
def officer_dashboard(request):
    """Real stats dashboard for officers."""
    base = Application.objects.all()
    stats = {
        "total": base.count(),
        "draft": base.filter(status=Application.Status.DRAFT).count(),
        "submitted": base.filter(status=Application.Status.SUBMITTED).count(),
        "under_review": base.filter(status=Application.Status.UNDER_REVIEW).count(),
        "correction_required": base.filter(status=Application.Status.CORRECTION_REQUIRED).count(),
        "resubmitted": base.filter(status=Application.Status.RESUBMITTED).count(),
        "approved": base.filter(status=Application.Status.APPROVED).count(),
        "rejected": base.filter(status=Application.Status.REJECTED).count(),
    }
    pending_docs = (
        Application.objects.filter(status=Application.Status.UNDER_REVIEW)
        .aggregate(n=Count("documents", filter=Q(documents__status="PENDING")))["n"]
        or 0
    )

    recent = base.order_by("-updated_at")[:10]

    return render(
        request,
        "officer/dashboard.html",
        {"stats": stats, "recent": recent, "pending_docs": pending_docs},
    )


@officer_required
def application_list(request):
    """
    Officer queue with search and filters.
    """
    qs = (
        Application.objects.select_related(
            "student", "admission_record__department", "admission_record__programme", "session"
        )
        .exclude(status=Application.Status.DRAFT)
    )

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    session_id = request.GET.get("session", "").strip()
    department_id = request.GET.get("department", "").strip()
    programme_id = request.GET.get("programme", "").strip()

    if q:
        qs = qs.filter(
            Q(reference__icontains=q)
            | Q(student__first_name__icontains=q)
            | Q(student__last_name__icontains=q)
            | Q(student__username__icontains=q)
            | Q(admission_record__jamb_number__icontains=q)
            | Q(admission_record__admission_number__icontains=q)
            | Q(admission_record__student_name__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if session_id:
        qs = qs.filter(session_id=session_id)
    if department_id:
        qs = qs.filter(admission_record__department_id=department_id)
    if programme_id:
        qs = qs.filter(admission_record__programme_id=programme_id)

    qs = qs.order_by("-submitted_at", "-updated_at")

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get("page"))

    # Filter option data
    from admissions.models import AdmissionSession, Department, Programme

    context = {
        "page": page,
        "total": qs.count(),
        "statuses": Application.Status.choices,
        "sessions": AdmissionSession.objects.order_by("-name"),
        "departments": Department.objects.filter(is_active=True).order_by("name"),
        "programmes": Programme.objects.filter(is_active=True).order_by("name"),
        "filters": {
            "q": q,
            "status": status,
            "session": session_id,
            "department": department_id,
            "programme": programme_id,
        },
    }
    return render(request, "officer/application_list.html", context)


class OfficerApplicationDetailView(View):
    """Officer view of a single application with document review actions."""

    template_name = "officer/application_detail.html"

    def get(self, request, reference):
        if not (request.user.is_officer or request.user.is_admin_role or request.user.is_superuser):
            messages.error(request, "Only officers can access that page.")
            return redirect("accounts:redirect_after_login")

        application = get_object_or_404(
            Application.objects.select_related(
                "student", "admission_record__department", "admission_record__programme", "session"
            ),
            reference=reference,
        )

        documents = (
            application.documents.select_related("document_type")
            .filter(replaced_by__isnull=True)
            .order_by("document_type__name")
        )

        context = {
            "application": application,
            "documents": documents,
            "review_form": CorrectionRequestForm(),
            "approve_form": ApproveApplicationForm(),
            "reject_form": RejectApplicationForm(),
        }
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# Action endpoints
# ---------------------------------------------------------------------------
@officer_required
def action_start_review(request, reference):
    if request.method != "POST":
        return redirect("applications:officer_detail", reference=reference)
    application = get_object_or_404(Application, reference=reference)
    try:
        start_review(application, officer=request.user)
        messages.success(request, "Review started.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("applications:officer_detail", reference=reference)


@officer_required
def action_request_correction(request, reference):
    if request.method != "POST":
        return redirect("applications:officer_detail", reference=reference)
    application = get_object_or_404(Application, reference=reference)
    form = CorrectionRequestForm(request.POST)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, "; ".join(err))
        return redirect("applications:officer_detail", reference=reference)
    try:
        request_correction(application, officer=request.user, reason=form.cleaned_data["reason"])
        messages.success(request, "Correction requested.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("applications:officer_detail", reference=reference)


@officer_required
def action_approve(request, reference):
    if request.method != "POST":
        return redirect("applications:officer_detail", reference=reference)
    application = get_object_or_404(Application, reference=reference)
    form = ApproveApplicationForm(request.POST)
    comment = form.cleaned_data["comment"] if form.is_valid() else ""
    try:
        approve_application(application, officer=request.user, comment=comment)
        messages.success(request, "Application approved.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("applications:officer_detail", reference=reference)


@officer_required
def action_reject(request, reference):
    if request.method != "POST":
        return redirect("applications:officer_detail", reference=reference)
    application = get_object_or_404(Application, reference=reference)
    form = RejectApplicationForm(request.POST)
    if not form.is_valid():
        for err in form.errors.values():
            messages.error(request, "; ".join(err))
        return redirect("applications:officer_detail", reference=reference)
    try:
        reject_application(application, officer=request.user, reason=form.cleaned_data["reason"])
        messages.success(request, "Application rejected.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("applications:officer_detail", reference=reference)


# ---------------------------------------------------------------------------
# Document review (officer)
# ---------------------------------------------------------------------------
@officer_required
def review_document_view(request, reference, pk):
    if request.method != "POST":
        return redirect("applications:officer_detail", reference=reference)

    from documents.models import Document

    application = get_object_or_404(Application, reference=reference)
    document = get_object_or_404(Document, pk=pk, application=application)

    status = request.POST.get("status", "").strip()
    comment = request.POST.get("comment", "").strip()

    try:
        review_document(document, officer=request.user, status=status, comment=comment)
        messages.success(request, f"Document '{document.document_type.name}' updated.")
    except ValueError as exc:
        messages.error(request, str(exc))

    return redirect("applications:officer_detail", reference=reference)