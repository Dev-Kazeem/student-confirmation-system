from django import forms

from .models import AdmissionRecord


class AdmissionCheckForm(forms.Form):
    """
    Public form to look up an admission record by JAMB number or admission number.
    """

    identifier = forms.CharField(
        label="JAMB number or Admission number",
        max_length=30,
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": "e.g. 20241234567 or UDS/CSC/24/0001",
                "autofocus": True,
            }
        ),
        help_text="Enter either your JAMB registration number or your admission number.",
    )

    def clean_identifier(self):
        value = self.cleaned_data["identifier"].strip()
        if not value:
            raise forms.ValidationError("Please enter a JAMB or admission number.")
        return value

    def lookup(self) -> AdmissionRecord | None:
        """Find the admission record matching the entered identifier."""
        value = self.cleaned_data["identifier"]
        return (
            AdmissionRecord.objects.filter(jamb_number__iexact=value).first()
            or AdmissionRecord.objects.filter(admission_number__iexact=value).first()
        )


from .models import AdmissionRecord, AdmissionSession, Department, Programme


class AdmissionRecordForm(forms.ModelForm):
    class Meta:
        model = AdmissionRecord
        fields = (
            "jamb_number",
            "admission_number",
            "student_name",
            "department",
            "programme",
            "session",
            "status",
        )
        widgets = {
            "jamb_number": forms.TextInput(attrs={"class": "form-control"}),
            "admission_number": forms.TextInput(attrs={"class": "form-control"}),
            "student_name": forms.TextInput(attrs={"class": "form-control"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "programme": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class AdmissionImportForm(forms.Form):
    csv_file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".csv,text/csv"}
        ),
        help_text=(
            "CSV with headers: jamb_number, student_name, admission_number, "
            "department_code, programme_code, session_name"
        ),
    )

    def clean_csv_file(self):
        f = self.cleaned_data["csv_file"]
        if f.size > 5 * 1024 * 1024:
            raise forms.ValidationError("CSV must be 5 MB or smaller.")
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Only .csv files are accepted.")
        return f    