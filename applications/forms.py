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