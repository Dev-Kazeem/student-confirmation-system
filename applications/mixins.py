from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect

from .models import Application


class StudentOwnsApplicationMixin(LoginRequiredMixin):
    """
    Ensure the current user is a student AND owns the requested application.

    Adds `self.application` for the view. URLConf must provide the kwargs
    `reference` (the Application.reference UUID).
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_student or request.user.is_superuser):
            messages.error(request, "Only students can access this page.")
            return redirect("accounts:redirect_after_login")

        reference = kwargs.get("reference")
        self.application = get_object_or_404(Application, reference=reference)

        if (
            self.application.student_id != request.user.pk
            and not request.user.is_superuser
        ):
            messages.error(request, "You do not have access to that application.")
            return redirect("accounts:student_dashboard")

        return super().dispatch(request, *args, **kwargs)