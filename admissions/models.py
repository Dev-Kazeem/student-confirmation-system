from django.db import models


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------
class Department(models.Model):
    """Academic department (e.g., Computer Science, Biochemistry)."""

    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short code used in references, e.g. CSC, BCH.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


# ---------------------------------------------------------------------------
# Programme
# ---------------------------------------------------------------------------
class Programme(models.Model):
    """
    A degree programme offered by a department (e.g., B.Sc. Computer Science).
    """

    class DegreeType(models.TextChoices):
        BSC = "BSC", "B.Sc."
        BA = "BA", "B.A."
        BENG = "BENG", "B.Eng."
        MBBS = "MBBS", "M.B.B.S."
        LLB = "LLB", "LL.B."
        OTHER = "OTH", "Other"

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="programmes",
    )
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=15, unique=True)
    degree_type = models.CharField(
        max_length=10, choices=DegreeType.choices, default=DegreeType.BSC
    )
    duration_years = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"], name="unique_programme_per_department"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


# ---------------------------------------------------------------------------
# Admission Session
# ---------------------------------------------------------------------------
class AdmissionSession(models.Model):
    """Academic session for which admissions are being processed."""

    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="E.g., 2024/2025",
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Only one session should be active at a time.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Admission Record
# ---------------------------------------------------------------------------
class AdmissionRecord(models.Model):
    """
    A record of an admitted student, imported by an administrator.

    Students use the JAMB number or admission number to look up their record
    and claim it for confirmation.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CLAIMED = "CLAIMED", "Claimed"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    # --- identifiers ---------------------------------------------------------
    jamb_number = models.CharField(max_length=20, unique=True, db_index=True)
    admission_number = models.CharField(
        max_length=30, unique=True, null=True, blank=True, db_index=True
    )
    student_name = models.CharField(max_length=200)

    # --- academic assignment -------------------------------------------------
    department = models.ForeignKey(
        Department, on_delete=models.PROTECT, related_name="admission_records"
    )
    programme = models.ForeignKey(
        Programme, on_delete=models.PROTECT, related_name="admission_records"
    )
    session = models.ForeignKey(
        AdmissionSession, on_delete=models.PROTECT, related_name="admission_records"
    )

    # --- status --------------------------------------------------------------
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    claimed_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claimed_admissions",
    )
    claimed_at = models.DateTimeField(null=True, blank=True)

    # --- meta ----------------------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["jamb_number"]),
            models.Index(fields=["admission_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_name} — {self.jamb_number}"