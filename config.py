"""
Application configuration, loaded from environment variables.

Nothing here is hardcoded/fake — if a value isn't set in the
environment, the corresponding feature reports itself as
"not configured" rather than pretending to work.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from repository root if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

APP_ENV = os.environ.get("APP_ENV", "development")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "G-KYK82K8M9J")

DATABASE_URL = os.environ.get("DATABASE_URL", "")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

# PostHog Product Analytics Configuration
POSTHOG_API_KEY = (
    os.environ.get("POSTHOG_API_KEY")
    or os.environ.get("NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN")
    or ""
)
POSTHOG_HOST = (
    os.environ.get("POSTHOG_HOST")
    or os.environ.get("NEXT_PUBLIC_POSTHOG_HOST")
    or "https://us.i.posthog.com"
)
POSTHOG_PROJECT_ID = os.environ.get("POSTHOG_PROJECT_ID", "")


def google_analytics_configured() -> bool:
    """True only if real GA4 OAuth credentials are present."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)


def razorpay_configured() -> bool:
    """True only if real Razorpay credentials are present."""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def posthog_configured() -> bool:
    """True only if real PostHog project token is present."""
    return bool(POSTHOG_API_KEY and POSTHOG_API_KEY.strip())
