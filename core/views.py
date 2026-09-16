from django.shortcuts import render


def home(request):
    """Public landing page."""
    return render(request, "core/home.html")


def about(request):
    """About the confirmation portal."""
    return render(request, "core/about.html")


def contact(request):
    """Static contact information page."""
    return render(request, "core/contact.html")


# --- Custom error handlers -------------------------------------------------
def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)