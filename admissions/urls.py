from django.urls import path

from . import views, admin_views



app_name = "admissions"

urlpatterns = [
    path("check/", views.check_admission, name="check_admission"),
    path("claim/<str:jamb_number>/", views.claim_admission, name="claim_admission"),
    path("my-admission/", views.my_admission, name="my_admission"),
    path("admin/list/", admin_views.admission_list, name="admin_list"),
    path("admin/create/", admin_views.admission_create, name="admin_create"),
    path("admin/<int:pk>/edit/", admin_views.admission_edit, name="admin_edit"),
    path("admin/import/", admin_views.admission_import, name="admin_import"),
]