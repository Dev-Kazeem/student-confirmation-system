from django import forms

from accounts.models import StudentProfile

from .models import Application


class ApplicationForm(forms.ModelForm):
    """
    Allows the student to review and confirm personal information before
    submission. The underlying data lives on StudentProfile, so this form
    edits a *copy* of those fields and writes back on save.

    For Phase Five we keep it simple: the form is read-mostly and its main
    job is to show the student what will be submitted.
    """

    confirm = forms.BooleanField(
        required=True,
        label="I confirm that all information and uploaded documents are accurate.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Application
        fields = ()  # no direct Application fields are edited here

    def __init__(self, *args, application: Application = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.application = application


class CorrectionRequestForm(forms.Form):
    reason = forms.CharField(
        label="Reason for correction",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Explain what needs to be corrected and why.",
            }
        ),
    )

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 10:
            raise forms.ValidationError("Please provide a more detailed reason (at least 10 characters).")
        return reason


class RejectApplicationForm(forms.Form):
    reason = forms.CharField(
        label="Reason for rejection",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Explain why this application is being rejected.",
            }
        ),
    )

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        if len(reason) < 10:
            raise forms.ValidationError("Please provide a more detailed reason (at least 10 characters).")
        return reason


class ApproveApplicationForm(forms.Form):
    comment = forms.CharField(
        label="Comment (optional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional note to the student.",
            }
        ),
    )