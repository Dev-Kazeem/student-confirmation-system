from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Registration & session
    path("register/", views.register, name="register"),
    path("login/", views.PortalLoginView.as_view(), name="login"),
    path("logout/", views.PortalLogoutView.as_view(), name="logout"),
    path("redirect/", views.redirect_after_login, name="redirect_after_login"),

    # Dashboards
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("officer/", views.officer_dashboard, name="officer_dashboard"),
    path("admin/", views.admin_dashboard, name="admin_dashboard"),

    # Password reset (anonymous)
    path("password-reset/", views.PortalPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.PortalPasswordResetDoneView.as_view(), name="password_reset_done"),
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        views.PortalPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.PortalPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),

    # Password change (logged in)
    path("password-change/", views.PortalPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", views.password_change_done, name="password_change_done"),
]