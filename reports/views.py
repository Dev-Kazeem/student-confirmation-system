from django.contrib import messages
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.shortcuts import redirect, render

from accounts.decorators import staff_required
from admissions.models import Department
from applications.models import Application
from auditlogs.models import AuditLog
from confirmations.models import ConfirmationSlip
from documents.models import Document

from . import exporters


# ===========================================================================
# Admin dashboard (real stats)
# ===========================================================================
@staff_required
def admin_dashboard(request):
    """
    The homepage of the administrative section.
    Real statistics pulled from the database.
    """
    apps_qs = Application.objects.all()
    stats = {
        "students": apps_qs.values("student").distinct().count(),
        "applications": apps_qs.count(),
        "draft": apps_qs.filter(status=Application.Status.DRAFT).count(),
        "submitted": apps_qs.filter(status=Application.Status.SUBMITTED).count(),
        "under_review": apps_qs.filter(status=Application.Status.UNDER_REVIEW).count(),
        "correction_required": apps_qs.filter(status=Application.Status.CORRECTION_REQUIRED).count(),
        "resubmitted": apps_qs.filter(status=Application.Status.RESUBMITTED).count(),
        "approved": apps_qs.filter(status=Application.Status.APPROVED).count(),
        "rejected": apps_qs.filter(status=Application.Status.REJECTED).count(),
        "documents": Document.objects.count(),
        "pending_documents": Document.objects.filter(status=Document.Status.PENDING).count(),
        "slips": ConfirmationSlip.objects.count(),
    }

    recent_apps = (
        apps_qs.select_related("student", "admission_record__department", "session")
        .order_by("-updated_at")[:10]
    )
    recent_audits = (
        AuditLog.objects.select_related("user").order_by("-created_at")[:10]
    )

    # Department breakdown for the chart
    dept_breakdown = (
        Department.objects.annotate(
            total=Count("admission_records__applications", distinct=True),
            approved=Count(
                "admission_records__applications",
                filter=Q(admission_records__applications__status=Application.Status.APPROVED),
                distinct=True,
            ),
        )
        .order_by("-total")[:10]
    )

    return render(
        request,
        "reports/admin_dashboard.html",
        {
            "stats": stats,
            "recent_apps": recent_apps,
            "recent_audits": recent_audits,
            "dept_breakdown": dept_breakdown,
        },
    )


# ===========================================================================
# Report index
# ===========================================================================
@staff_required
def report_index(request):
    return render(request, "reports/index.html")


# ===========================================================================
# Individual reports
# ===========================================================================
def _filtered_applications(request, base_qs):
    """Apply shared filters (status, session, department) from query params."""
    status = request.GET.get("status", "").strip()
    session_id = request.GET.get("session", "").strip()
    department_id = request.GET.get("department", "").strip()
    if status:
        base_qs = base_qs.filter(status=status)
    if session_id:
        base_qs = base_qs.filter(session_id=session_id)
    if department_id:
        base_qs = base_qs.filter(admission_record__department_id=department_id)
    return base_qs


@staff_required
def report_status(request):
    base = Application.objects.select_related(
        "student", "admission_record__department", "admission_record__programme", "session", "reviewing_officer"
    )
    qs = _filtered_applications(request, base).order_by("-created_at")
    return render(
        request,
        "reports/status.html",
        {"applications": qs[:500], "total": qs.count(), "filters": _get_filters(request)},
    )


@staff_required
def report_department(request):
    rows = (
        Department.objects.annotate(
            total=Count("admission_records__applications", distinct=True),
            approved=Count(
                "admission_records__applications",
                filter=Q(admission_records__applications__status=Application.Status.APPROVED),
                distinct=True,
            ),
            rejected=Count(
                "admission_records__applications",
                filter=Q(admission_records__applications__status=Application.Status.REJECTED),
                distinct=True,
            ),
            pending=Count(
                "admission_records__applications",
                filter=~Q(
                    admission_records__applications__status__in=[
                        Application.Status.APPROVED,
                        Application.Status.REJECTED,
                    ]
                ),
                distinct=True,
            ),
        )
        .order_by("-total")
    )
    rows_data = [
        {
            "department": d.name,
            "total": d.total,
            "approved": d.approved,
            "rejected": d.rejected,
            "pending": d.pending,
        }
        for d in rows
    ]
    return render(request, "reports/department.html", {"rows": rows_data})


@staff_required
def report_approved(request):
    base = Application.objects.filter(status=Application.Status.APPROVED).select_related(
        "student", "admission_record__department", "admission_record__programme", "session"
    )
    qs = _filtered_applications(request, base).order_by("-approved_at")
    return render(
        request,
        "reports/approved.html",
        {"applications": qs[:500], "total": qs.count(), "filters": _get_filters(request)},
    )


@staff_required
def report_rejected(request):
    base = Application.objects.filter(status=Application.Status.REJECTED).select_related(
        "student", "admission_record__department", "admission_record__programme", "session"
    )
    qs = _filtered_applications(request, base).order_by("-rejected_at")
    return render(
        request,
        "reports/rejected.html",
        {"applications": qs[:500], "total": qs.count(), "filters": _get_filters(request)},
    )


@staff_required
def report_pending(request):
    base = Application.objects.filter(
        status__in=[
            Application.Status.SUBMITTED,
            Application.Status.UNDER_REVIEW,
            Application.Status.RESUBMITTED,
            Application.Status.CORRECTION_REQUIRED,
        ]
    ).select_related("student", "admission_record__department", "admission_record__programme", "session", "reviewing_officer")
    qs = _filtered_applications(request, base).order_by("submitted_at")
    return render(
        request,
        "reports/pending.html",
        {"applications": qs[:500], "total": qs.count(), "filters": _get_filters(request)},
    )


@staff_required
def report_documents(request):
    qs = Document.objects.select_related(
        "application__student", "document_type", "reviewed_by"
    ).order_by("-uploaded_at")
    status = request.GET.get("status", "").strip()
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "reports/documents.html",
        {"documents": qs[:500], "total": qs.count(), "filters": _get_filters(request)},
    )


def _get_filters(request):
    from admissions.models import AdmissionSession

    return {
        "status": request.GET.get("status", ""),
        "session": request.GET.get("session", ""),
        "department": request.GET.get("department", ""),
        "sessions": AdmissionSession.objects.order_by("-name"),
        "departments": Department.objects.filter(is_active=True).order_by("name"),
        "statuses": Application.Status.choices,
    }


# ===========================================================================
# CSV exports (streamed)
# ===========================================================================
@staff_required
def export_status(request):
    qs = Application.objects.select_related(
        "student", "admission_record__department", "admission_record__programme", "session", "reviewing_officer"
    )
    qs = _filtered_applications(request, qs).order_by("-created_at")
    return _csv_response(exporters.applications_by_status(qs), "applications_status.csv")


@staff_required
def export_department(request):
    rows = (
        Department.objects.annotate(
            total=Count("admission_records__applications", distinct=True),
            approved=Count(
                "admission_records__applications",
                filter=Q(admission_records__applications__status=Application.Status.APPROVED),
                distinct=True,
            ),
            rejected=Count(
                "admission_records__applications",
                filter=Q(admission_records__applications__status=Application.Status.REJECTED),
                distinct=True,
            ),
            pending=Count(
                "admission_records__applications",
                filter=~Q(
                    admission_records__applications__status__in=[
                        Application.Status.APPROVED,
                        Application.Status.REJECTED,
                    ]
                ),
                distinct=True,
            ),
        )
    )
    rows_data = [
        {
            "department": d.name,
            "total": d.total,
            "approved": d.approved,
            "rejected": d.rejected,
            "pending": d.pending,
        }
        for d in rows
    ]
    return _csv_response(exporters.applications_by_department(rows_data), "applications_by_department.csv")


@staff_required
def export_approved(request):
    qs = Application.objects.filter(status=Application.Status.APPROVED).select_related(
        "student", "admission_record__department", "admission_record__programme", "session"
    )
    qs = _filtered_applications(request, qs).order_by("-approved_at")
    return _csv_response(exporters.approved_students(qs), "approved_students.csv")


@staff_required
def export_rejected(request):
    qs = Application.objects.filter(status=Application.Status.REJECTED).select_related(
        "student", "admission_record__department", "admission_record__programme", "session"
    )
    qs = _filtered_applications(request, qs).order_by("-rejected_at")
    return _csv_response(exporters.rejected_applications(qs), "rejected_applications.csv")


@staff_required
def export_pending(request):
    qs = Application.objects.filter(
        status__in=[
            Application.Status.SUBMITTED,
            Application.Status.UNDER_REVIEW,
            Application.Status.RESUBMITTED,
            Application.Status.CORRECTION_REQUIRED,
        ]
    ).select_related(
        "student", "admission_record__department", "admission_record__programme", "session", "reviewing_officer"
    )
    qs = _filtered_applications(request, qs).order_by("submitted_at")
    return _csv_response(exporters.pending_review(qs), "pending_review.csv")


@staff_required
def export_documents(request):
    qs = Document.objects.select_related(
        "application__student", "document_type", "reviewed_by"
    ).order_by("-uploaded_at")
    status = request.GET.get("status", "").strip()
    if status:
        qs = qs.filter(status=status)
    return _csv_response(exporters.document_verification(qs), "document_verification.csv")


def _csv_response(stream, filename):
    response = StreamingHttpResponse(stream, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response