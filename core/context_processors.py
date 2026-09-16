from django.conf import settings


def site_metadata(request):
    """Expose site name and current year to every template."""
    from django.utils import timezone

    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Student Confirmation Portal"),
        "CURRENT_YEAR": timezone.now().year,
    }