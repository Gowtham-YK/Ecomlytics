"""
Google Analytics 4 integration adapter.

This module implements the OAuth *architecture* for connecting a
customer's GA4 property: building the consent URL, exchanging the
authorization code for tokens, and (once tokens exist) querying the
GA4 Data API and normalizing the response into the app's internal
shape.

It does NOT fabricate GA4 data. Until real GOOGLE_CLIENT_ID /
GOOGLE_CLIENT_SECRET / GOOGLE_REDIRECT_URI values are supplied via
environment variables, every function here reports a clear
"not configured" state instead of pretending to be connected.
"""

from urllib.parse import urlencode

import config

AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
GA4_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"


def status() -> dict:
    """Honest connection state for the Data Sources page."""
    if not config.google_analytics_configured():
        return {
            "id": "google_analytics",
            "name": "Google Analytics 4",
            "state": "not_configured",
            "message": (
                "Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and "
                "GOOGLE_REDIRECT_URI to enable this integration."
            ),
            "property_id": None,
            "last_synced": None,
        }

    # Credentials exist, but no stored OAuth tokens for a workspace
    # yet in this build (token storage is part of the still-pending
    # auth/workspace persistence layer — see ROADMAP.md).
    return {
        "id": "google_analytics",
        "name": "Google Analytics 4",
        "state": "disconnected",
        "message": "Configured. Click Connect to authorize a GA4 property.",
        "property_id": config.GA4_PROPERTY_ID or None,
        "last_synced": None,
    }


def build_authorization_url(state: str) -> str:
    """
    Build the real Google OAuth 2.0 consent URL for GA4 read access.
    Raises if credentials are not configured, rather than returning
    a fake link.
    """
    if not config.google_analytics_configured():
        raise RuntimeError(
            "Google Analytics is not configured. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI first."
        )

    params = {
        "client_id": config.GOOGLE_CLIENT_ID,
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GA4_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{AUTH_BASE_URL}?{urlencode(params)}"


def normalize_report(raw_ga4_response: dict) -> dict:
    """
    Convert a GA4 Data API runReport response into the app's internal
    NormalizedAnalyticsData shape, so the rest of the app never has to
    know about GA4-specific field names (dimensionHeaders/metricHeaders/rows).

    This is the adapter boundary described in the architecture: it is
    implemented and unit-testable now, even though it has no live data
    to normalize yet without real credentials.
    """
    dimension_headers = [h["name"] for h in raw_ga4_response.get("dimensionHeaders", [])]
    metric_headers = [h["name"] for h in raw_ga4_response.get("metricHeaders", [])]

    rows_out = []
    for row in raw_ga4_response.get("rows", []):
        dims = {
            dimension_headers[i]: v.get("value")
            for i, v in enumerate(row.get("dimensionValues", []))
        }
        mets = {
            metric_headers[i]: v.get("value")
            for i, v in enumerate(row.get("metricValues", []))
        }
        rows_out.append({"dimensions": dims, "metrics": mets})

    return {"rows": rows_out, "row_count": raw_ga4_response.get("rowCount", len(rows_out))}
