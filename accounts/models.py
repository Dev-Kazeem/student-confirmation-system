from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{7,15}$",
    message="Enter a valid phone number (7 to 15 digits, optional leading +).",
)

jamb_validator = RegexValidator(
    regex=r"^[0-9]{8,12}$",
    message="JAMB number must be 8 to 12 digits.",
)


# ---------------------------------------------------------------------------
# Custom user
# ---------------------------------------------------------------------------
class User(AbstractUser):
    """
    Custom user model with three roles:
      - STUDENT : newly admitted student using the confirmation portal
      - OFFICER : admission officer reviewing applications
      - ADMIN   : system administrator
    """

    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        OFFICER = "OFFICER", "Admission Officer"
        ADMIN = "ADMIN", "System Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
        help_text="Determines what the user can access.",
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate instead of deleting users to preserve records.",
    )

    # --- convenience helpers -------------------------------------------------
    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_officer(self) -> bool:
        return self.role == self.Role.OFFICER

    @property
    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def __str__(self) -> str:
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


# ---------------------------------------------------------------------------
# Student profile
# ---------------------------------------------------------------------------
class StudentProfile(models.Model):
    """
    Personal and academic information submitted by a student.

    One-to-one with User. Created automatically when a student registers
    (Phase Three) or when an admission record is claimed.
    """

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    # --- personal ------------------------------------------------------------
    full_name = models.CharField(max_length=200, blank=True)
    phone_number = models.CharField(
        max_length=20, blank=True, validators=[phone_validator]
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    state_of_origin = models.CharField(max_length=50, blank=True)
    lga = models.CharField("Local Government Area", max_length=80, blank=True)
    residential_address = models.TextField(blank=True)

    # --- academic ------------------------------------------------------------
    jamb_number = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        validators=[jamb_validator],
    )
    admission_number = models.CharField(max_length=30, blank=True, db_index=True)

    # --- meta ----------------------------------------------------------------
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    is_complete = models.BooleanField(
        default=False,
        help_text="Set to True once all required fields are filled.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        indexes = [
            models.Index(fields=["jamb_number"]),
            models.Index(fields=["admission_number"]),
        ]

    def __str__(self) -> str:
        return f"Profile — {self.user.get_full_name() or self.user.username}"