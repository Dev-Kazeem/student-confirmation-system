from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("start/", views.start_or_continue, name="start"),
    path("<uuid:reference>/preview/", views.ApplicationPreviewView.as_view(), name="preview"),
    path("<uuid:reference>/status/", views.ApplicationStatusView.as_view(), name="status"),
]