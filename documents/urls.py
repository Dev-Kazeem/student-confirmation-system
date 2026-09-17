from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("<uuid:reference>/manage/", views.DocumentManageView.as_view(), name="manage"),
    path("<uuid:reference>/upload/", views.DocumentUploadView.as_view(), name="upload"),
    path("<uuid:reference>/download/<int:pk>/", views.DocumentDownloadView.as_view(), name="download"),
]