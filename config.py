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

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")


def google_analytics_configured() -> bool:
    """True only if real GA4 OAuth credentials are present."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)


def razorpay_configured() -> bool:
    """True only if real Razorpay credentials are present."""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


# Product analytics providers (all optional; server-side credentials only).
MIXPANEL_PROJECT_TOKEN = os.environ.get("MIXPANEL_PROJECT_TOKEN", "").strip()
POSTHOG_PROJECT_TOKEN = (
    os.environ.get("POSTHOG_PROJECT_TOKEN", "").strip()
    or os.environ.get("POSTHOG_API_KEY", "").strip()
)
POSTHOG_HOST = os.environ.get("POSTHOG_HOST", "https://us.i.posthog.com").rstrip("/")
AMPLITUDE_API_KEY = os.environ.get("AMPLITUDE_API_KEY", "").strip()
AMPLITUDE_INGEST_URL = os.environ.get(
    "AMPLITUDE_INGEST_URL", "https://api2.amplitude.com/2/httpapi"
).strip()
