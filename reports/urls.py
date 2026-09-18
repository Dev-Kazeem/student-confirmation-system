from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_index, name="index"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # HTML reports
    path("status/", views.report_status, name="status"),
    path("department/", views.report_department, name="department"),
    path("approved/", views.report_approved, name="approved"),
    path("rejected/", views.report_rejected, name="rejected"),
    path("pending/", views.report_pending, name="pending"),
    path("documents/", views.report_documents, name="documents"),

    # CSV exports
    path("status.csv", views.export_status, name="export_status"),
    path("department.csv", views.export_department, name="export_department"),
    path("approved.csv", views.export_approved, name="export_approved"),
    path("rejected.csv", views.export_rejected, name="export_rejected"),
    path("pending.csv", views.export_pending, name="export_pending"),
    path("documents.csv", views.export_documents, name="export_documents"),
]