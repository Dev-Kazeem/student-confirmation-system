from django import forms

from .models import Document, DocumentType


class DocumentUploadForm(forms.Form):
    """
    One form that handles a single document upload for a given DocumentType.
    Used on the manage page, repeated per required type.
    """

    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        widget=forms.HiddenInput(),
    )
    file = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}
        )
    )

    def clean(self):
        cleaned = super().clean()
        dt = cleaned.get("document_type")
        f = cleaned.get("file")
        if not dt or not f:
            return cleaned

        from .services import validate_upload

        ok, error = validate_upload(document_type=dt, uploaded_file=f)
        if not ok:
            raise forms.ValidationError(error)
        return cleaned


class DocumentReplaceForm(DocumentUploadForm):
    """Same rules as upload — replacement is just a new upload of the same type."""