"""
Local development settings.

- SQLite database
- DEBUG = True
- Console email backend
- Django serves static files itself
"""

from .base import *  # noqa: F401, F403
from .base import BASE_DIR

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# In dev, emails print to the console — perfect for testing without SMTP.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable manifest static storage in dev so missing files don't crash the app.
STORAGES["staticfiles"]["BACKEND"] = (  # noqa: F405
    "django.contrib.staticfiles.storage.StaticFilesStorage"
)