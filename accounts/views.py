from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import (
    PortalAuthenticationForm,
    PortalPasswordChangeForm,
    PortalPasswordResetForm,
    PortalSetPasswordForm,
    StudentRegistrationForm,
)
from .models import User


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def register(request):
    """Student self-registration."""
    if request.user.is_authenticated:
        return redirect("accounts:redirect_after_login")

    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the new student in immediately
            login(request, user)
            messages.success(
                request,
                "Your account was created successfully. Welcome to the portal.",
            )
            return redirect("accounts:redirect_after_login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
class PortalLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = PortalAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_short_name() or form.get_user().username}.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
class PortalLogoutView(LogoutView):
    """Handles both GET and POST for convenience, but POST is preferred."""

    next_page = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been logged out.")
        return super().dispatch(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Post-login dispatcher
# ---------------------------------------------------------------------------
@login_required
def redirect_after_login(request):
    """Route the user to the correct dashboard based on their role."""
    user = request.user
    if user.is_admin_role or user.is_superuser:
        return redirect("accounts:admin_dashboard")
    if user.is_officer:
        return redirect("accounts:officer_dashboard")
    return redirect("accounts:student_dashboard")


# ---------------------------------------------------------------------------
# Dashboards (placeholders for now; fleshed out in later phases)
# ---------------------------------------------------------------------------
@login_required
def student_dashboard(request):
    if not request.user.is_student and not request.user.is_superuser:
        messages.warning(request, "You are not authorized to view the student dashboard.")
        return redirect("accounts:redirect_after_login")
    return render(request, "accounts/student_dashboard.html")


@login_required
def officer_dashboard(request):
    if not (request.user.is_officer or request.user.is_superuser):
        messages.warning(request, "You are not authorized to view the officer dashboard.")
        return redirect("accounts:redirect_after_login")
    return render(request, "accounts/officer_dashboard.html")


@login_required
def admin_dashboard(request):
    if not (request.user.is_admin_role or request.user.is_superuser):
        messages.warning(request, "You are not authorized to view the admin dashboard.")
        return redirect("accounts:redirect_after_login")
    return render(request, "accounts/admin_dashboard.html")


# ---------------------------------------------------------------------------
# Password reset — thin wrappers around Django's class-based views
# ---------------------------------------------------------------------------
class PortalPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = PortalPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class PortalPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PortalPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = PortalSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class PortalPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class PortalPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = PortalPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated.")
        return super().form_valid(form)


@login_required
def password_change_done(request):
    return render(request, "accounts/password_change_done.html")