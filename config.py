"""
Application configuration, loaded from environment variables.

Nothing here is hardcoded/fake — if a value isn't set in the
environment, the corresponding feature reports itself as
"not configured" rather than pretending to work.
"""

import os

APP_ENV = os.environ.get("APP_ENV", "development")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def google_analytics_configured() -> bool:
    """True only if real GA4 OAuth credentials are present."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)
