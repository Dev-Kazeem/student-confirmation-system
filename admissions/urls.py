from django.urls import path

from . import views

app_name = "admissions"

urlpatterns = [
    path("check/", views.check_admission, name="check_admission"),
    path("claim/<str:jamb_number>/", views.claim_admission, name="claim_admission"),
    path("my-admission/", views.my_admission, name="my_admission"),
]