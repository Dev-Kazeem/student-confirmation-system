from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def _redirect_unauthorized(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    messages.error(request, "You do not have permission to access that page.")
    return redirect("accounts:redirect_after_login")


def student_required(view_func):
    """Allow only authenticated students (or superusers)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not (request.user.is_student or request.user.is_superuser):
            return _redirect_unauthorized(request)
        return view_func(request, *args, **kwargs)

    return _wrapped


def officer_required(view_func):
    """Allow only authenticated officers (or superusers)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not (request.user.is_officer or request.user.is_superuser):
            return _redirect_unauthorized(request)
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required(view_func):
    """Allow only authenticated admins (or superusers)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not (request.user.is_admin_role or request.user.is_superuser):
            return _redirect_unauthorized(request)
        return view_func(request, *args, **kwargs)

    return _wrapped


def staff_required(view_func):
    """Allow any authenticated staff user (officer or admin)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if not (
            request.user.is_officer
            or request.user.is_admin_role
            or request.user.is_superuser
        ):
            return _redirect_unauthorized(request)
        return view_func(request, *args, **kwargs)

    return _wrapped