from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from applications.models import Application
from applications.mixins import StudentOwnsApplicationMixin
from auditlogs.models import AuditLog
from auditlogs.utils import get_client_ip
from notifications.models import Notification

from .forms import DocumentUploadForm
from .models import Document, DocumentType
from .services import missing_required_document_types


# ---------------------------------------------------------------------------
# Document management page (student)
# ---------------------------------------------------------------------------
class DocumentManageView(StudentOwnsApplicationMixin, View):
    template_name = "documents/manage.html"

    def get(self, request, *args, **kwargs):
        application = self.application
        if not application.is_editable:
            messages.info(
                request,
                "Your application is under review; documents cannot be changed now.",
            )
            return redirect("applications:status", reference=application.reference)

        required_types = list(DocumentType.objects.filter(is_required=True, is_active=True))
        optional_types = list(DocumentType.objects.filter(is_required=False, is_active=True))

        active_docs_qs = Document.objects.filter(
            application=application, replaced_by__isnull=True
        ).select_related("document_type")

        # { document_type_id: Document }
        active_docs = {d.document_type_id: d for d in active_docs_qs}

        # [{ type: DocumentType, current: Document|None }, ...]
        required_rows = [
            {"type": dt, "current": active_docs.get(dt.pk)} for dt in required_types
        ]
        optional_rows = [
            {"type": dt, "current": active_docs.get(dt.pk)} for dt in optional_types
        ]

        return render(
            request,
            self.template_name,
            {
                "application": application,
                "required_rows": required_rows,
                "optional_rows": optional_rows,
                "missing": missing_required_document_types(application),
            },
        )


# ---------------------------------------------------------------------------
# Upload a document
# ---------------------------------------------------------------------------
class DocumentUploadView(StudentOwnsApplicationMixin, View):
    def post(self, request, *args, **kwargs):
        application = self.application
        if not application.is_editable:
            messages.error(request, "Documents cannot be changed in the current application state.")
            return redirect("applications:status", reference=application.reference)

        form = DocumentUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            for err in form.errors.values():
                messages.error(request, "; ".join(err))
            return redirect("documents:manage", reference=application.reference)

        dt: DocumentType = form.cleaned_data["document_type"]
        f = form.cleaned_data["file"]

        # Replace any existing active document of this type
        previous = Document.objects.filter(
            application=application, document_type=dt, replaced_by__isnull=True
        ).first()

        new_doc = Document.objects.create(
            application=application,
            document_type=dt,
            file=f,
            status=Document.Status.PENDING,
        )
        if previous:
            previous.replaced_by = new_doc
            previous.save(update_fields=["replaced_by", "updated_at"])
            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.DOCUMENT_REPLACE,
                description=f"Replaced document '{dt.name}'.",
                target=new_doc,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        else:
            AuditLog.record(
                user=request.user,
                action=AuditLog.Action.DOCUMENT_UPLOAD,
                description=f"Uploaded document '{dt.name}'.",
                target=new_doc,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        messages.success(request, f"'{dt.name}' uploaded successfully.")
        return redirect("documents:manage", reference=application.reference)


# ---------------------------------------------------------------------------
# Preview/download a document (owner only)
# ---------------------------------------------------------------------------
class DocumentDownloadView(StudentOwnsApplicationMixin, View):
    def get(self, request, *args, **kwargs):
        application = self.application
        doc = get_object_or_404(Document, pk=kwargs["pk"], application=application)
        try:
            return FileResponse(doc.file.open("rb"), as_attachment=False, filename=doc.original_filename)
        except FileNotFoundError as exc:
            raise Http404("File not found.") from exc