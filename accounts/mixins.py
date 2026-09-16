from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Base mixin restricting a CBV to one or more roles.

    Subclass and set `allowed_roles` to a set of User.Role values, e.g.:

        class OfficerOnlyView(RoleRequiredMixin, View):
            allowed_roles = {User.Role.OFFICER}
    """

    allowed_roles: set = set()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role not in self.allowed_roles:
            messages.error(request, "You do not have permission to access that page.")
            return redirect("accounts:redirect_after_login")
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin(RoleRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        from .models import User

        self.allowed_roles = {User.Role.STUDENT}
        return super().dispatch(request, *args, **kwargs)


class OfficerRequiredMixin(RoleRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        from .models import User

        self.allowed_roles = {User.Role.OFFICER}
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        from .models import User

        self.allowed_roles = {User.Role.ADMIN}
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(RoleRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        from .models import User

        self.allowed_roles = {User.Role.OFFICER, User.Role.ADMIN}
        return super().dispatch(request, *args, **kwargs)