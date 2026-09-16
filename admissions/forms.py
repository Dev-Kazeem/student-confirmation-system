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