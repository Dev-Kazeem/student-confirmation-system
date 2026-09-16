from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)
from django.core.exceptions import ValidationError

from .models import User
from .models import StudentProfile, User

class StudentRegistrationForm(UserCreationForm):
    """
    Registration form for students only.

    Collects: first name, last name, email, username, phone, password1/2.
    The role is fixed to STUDENT — officers and admins are created by admins.
    """

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "phone_number",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bootstrap-friendly widgets
        for name, field in self.fields.items():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} form-control".strip()
            if name not in ("password1", "password2"):
                field.widget.attrs.setdefault("placeholder", field.label)
        # Override password widget placeholders
        self.fields["password1"].widget.attrs["placeholder"] = "Password"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirm password"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data["phone_number"].strip()
        # Deliberately permissive; the model validator catches the rest.
        if not phone:
            raise ValidationError("Phone number is required.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.STUDENT
        user.email = self.cleaned_data["email"]
        # Stash phone number on the in-memory instance so the signal can read it.
        user._pending_phone_number = self.cleaned_data["phone_number"]  # noqa: SLF001
        if commit:
            user.save()
        return user


class PortalAuthenticationForm(AuthenticationForm):
    """Login form with Bootstrap-styled widgets."""

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username", "autofocus": True}
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_active:
            raise ValidationError(
                "This account has been deactivated. Please contact the administrator.",
                code="inactive",
            )


class PortalPasswordResetForm(PasswordResetForm):
    """Same as Django's but with Bootstrap-styled email field."""

    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Email address", "autofocus": True}
        ),
    )


class PortalSetPasswordForm(SetPasswordForm):
    """Bootstrap-styled new password form (used after reset link)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class PortalPasswordChangeForm(PasswordChangeForm):
    """Bootstrap-styled change-password form (used while logged in)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class StudentProfileForm(forms.ModelForm):
    """
    Editable personal information for a student.

    Some fields (JAMB, admission number, full_name when claimed) are read-only
    once the student has claimed an admission record.
    """

    
    class Meta:
        model = StudentProfile
        fields = (
            "full_name",
            "phone_number",
            "date_of_birth",
            "gender",
            "state_of_origin",
            "lga",
            "residential_address",
            "profile_picture",
        )
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "date_of_birth": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "state_of_origin": forms.TextInput(attrs={"class": "form-control"}),
            "lga": forms.TextInput(attrs={"class": "form-control"}),
            "residential_address": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "profile_picture": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.required = name != "profile_picture"

    def clean_profile_picture(self):
        pic = self.cleaned_data.get("profile_picture")
        if pic and hasattr(pic, "content_type"):
            if not pic.content_type.startswith("image/"):
                raise forms.ValidationError("Please upload an image file.")
            if pic.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Profile picture must be 2 MB or smaller.")
        return pic