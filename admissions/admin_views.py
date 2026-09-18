from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import admin_required
from auditlogs.models import AuditLog
from auditlogs.utils import get_client_ip

from .forms import AdmissionRecordForm, AdmissionImportForm
from .importers import import_admission_records
from .models import AdmissionRecord


from django.db.models import Q

@admin_required
def admission_list(request):
    qs = AdmissionRecord.objects.select_related(
        "department", "programme", "session", "claimed_by"
    ).order_by("-created_at")

    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    session_id = request.GET.get("session", "").strip()

    if q:
        qs = qs.filter(
            Q(jamb_number__icontains=q)
            | Q(student_name__icontains=q)
            | Q(admission_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if session_id:
        qs = qs.filter(session_id=session_id)

    paginator = Paginator(qs, 30)
    page = paginator.get_page(request.GET.get("page"))

    from .models import AdmissionSession

    return render(
        request,
        "admissions/admin/list.html",
        {
            "page": page,
            "total": qs.count(),
            "statuses": AdmissionRecord.Status.choices,
            "sessions": AdmissionSession.objects.order_by("-name"),
            "filters": {"q": q, "status": status, "session": session_id},
        },
    )


@admin_required
def admission_create(request):
    if request.method == "POST":
        form = AdmissionRecordForm(request.POST)
        if form.is_valid():
            record = form.save()
            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.ADMISSION_IMPORT,
                description=f"Created admission record {record.jamb_number}.",
                target=record,
                ip_address=get_client_ip(request),
            )
            messages.success(request, "Admission record created.")
            return redirect("admissions:admin_list")
    else:
        form = AdmissionRecordForm()
    return render(
        request,
        "admissions/admin/form.html",
        {"form": form, "title": "Create Admission Record"},
    )


@admin_required
def admission_edit(request, pk):
    record = get_object_or_404(AdmissionRecord, pk=pk)
    if request.method == "POST":
        form = AdmissionRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Admission record updated.")
            return redirect("admissions:admin_list")
    else:
        form = AdmissionRecordForm(instance=record)
    return render(
        request,
        "admissions/admin/form.html",
        {"form": form, "title": f"Edit {record.jamb_number}"},
    )


@admin_required
def admission_import(request):
    result = None
    if request.method == "POST":
        form = AdmissionImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_admission_records(form.cleaned_data["csv_file"])
            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.ADMISSION_IMPORT,
                description=(
                    f"Imported admission CSV: {result['created']} created, "
                    f"{result['updated']} updated, {len(result['errors'])} errors."
                ),
                ip_address=get_client_ip(request),
            )
            if result["errors"]:
                messages.warning(request, f"Imported with {len(result['errors'])} errors.")
            else:
                messages.success(request, "Import completed successfully.")
    else:
        form = AdmissionImportForm()

    return render(
        request,
        "admissions/admin/import.html",
        {"form": form, "result": result},
    )