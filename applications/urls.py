from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    # Student-side
    path("start/", views.start_or_continue, name="start"),
    path("<uuid:reference>/preview/", views.ApplicationPreviewView.as_view(), name="preview"),
    path("<uuid:reference>/status/", views.ApplicationStatusView.as_view(), name="status"),

    # Officer-side
    path("officer/", views.officer_dashboard, name="officer_dashboard"),
    path("officer/list/", views.application_list, name="officer_list"),
    path("officer/<uuid:reference>/", views.OfficerApplicationDetailView.as_view(), name="officer_detail"),
    path("officer/<uuid:reference>/start-review/", views.action_start_review, name="action_start_review"),
    path("officer/<uuid:reference>/request-correction/", views.action_request_correction, name="action_request_correction"),
    path("officer/<uuid:reference>/approve/", views.action_approve, name="action_approve"),
    path("officer/<uuid:reference>/reject/", views.action_reject, name="action_reject"),
    path("officer/<uuid:reference>/document/<int:pk>/review/", views.review_document_view, name="review_document"),
]