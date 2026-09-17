from django.urls import path

from . import views

app_name = "confirmations"

urlpatterns = [
    path("verify/", views.verify_slip, name="verify"),
    path("my-slip/", views.my_slip, name="my_slip"),
    path("slip/<uuid:verification_code>/", views.slip_detail, name="slip_detail"),
    path("slip/<uuid:verification_code>/download/", views.slip_download, name="slip_download"),
    path("slip/<uuid:verification_code>/qr.png", views.slip_qr_image, name="slip_qr"),
]