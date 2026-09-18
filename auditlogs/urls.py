from django.urls import path

from . import views

app_name = "auditlogs"

urlpatterns = [
    path("", views.auditlog_list, name="list"),
    path("<int:pk>/", views.auditlog_detail, name="detail"),
]