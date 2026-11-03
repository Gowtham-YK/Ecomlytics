"""
Product analytics adapter for Ecomlytics.

Every event is persisted in Ecomlytics first, then best-effort forwarded to
each configured product analytics provider: Mixpanel, PostHog and Amplitude.
Provider credentials stay on the server and each provider remains optional.
"""

import base64
import json
import logging
import sqlite3
import time
import uuid
from typing import Dict, Any, Optional

import httpx
import config
from analytics.funnel import record_event

logger = logging.getLogger(__name__)


# Only these non-sensitive properties are forwarded to third-party providers.
# User email, names, passwords, payment credentials and raw customer/order data
# are deliberately excluded. Extend this list only after a privacy review.
SAFE_EVENT_PROPERTIES = {
    "page_path", "page_name", "dataset_type", "filter_days", "plan_name",
    "plan_id", "billing_cycle", "amount", "currency", "is_demo",
    "insight_type", "feature_name", "source", "report_type", "file_format",
    "success", "environment", "platform", "event_category", "error_code",
    "item_count", "imported_rows", "skipped_rows", "rejected_rows",
    "target_plan", "current_plan", "checkout_type", "session_id",
    "product_id", "product_category", "item_price", "quantity",
    # Mixpanel onboarding / activation event properties (no direct identifiers).
    "plan_tier", "signup_channel", "company_size", "timestamp_source",
    "inviter_role", "invite_source", "has_existing_shop_connection",
    "integration_name", "integration_type", "auth_flow", "connection_method",
    "scopes_granted_count", "time_to_connect_seconds", "failure_reason",
    "retry_attempt_count", "setup_step_name", "step_success",
    "step_order_number", "total_integrations_connected",
    "time_to_first_integration_seconds", "dashboard_name",
    "data_freshness_state", "integrations_connected_count",
    "time_to_first_dashboard_seconds", "delivery_mode", "integrations_used",
    "time_to_first_results_seconds", "successful_integrations_count",
    "analysis_type", "data_ready_mode"
}


def _safe_properties(properties: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return allowlisted scalar properties; never forward nested/raw records."""
    safe: Dict[str, Any] = {}
    for key, value in (properties or {}).items():
        if key not in SAFE_EVENT_PROPERTIES:
            continue
        if value is None or isinstance(value, (str, int, float, bool)):
            if isinstance(value, str):
                safe[key] = value[:200]
            else:
                safe[key] = value
        elif key == "integrations_used" and isinstance(value, list):
            # The tracking plan defines this field as a list of integration names.
            safe[key] = [item[:100] for item in value if isinstance(item, str)][:20]
    return safe


def provider_statuses() -> list:
    """Report configuration independently for all three analytics providers."""
    definitions = [
        ("mixpanel", "Mixpanel", bool(config.MIXPANEL_PROJECT_TOKEN),
         "Set MIXPANEL_PROJECT_TOKEN in Render to enable Mixpanel."),
        ("posthog", "PostHog", bool(config.POSTHOG_PROJECT_TOKEN),
         "Set POSTHOG_PROJECT_TOKEN and POSTHOG_HOST in Render to enable PostHog."),
        ("amplitude", "Amplitude", bool(config.AMPLITUDE_API_KEY),
         "Set AMPLITUDE_API_KEY in Render to enable Amplitude.")
    ]
    return [{
        "id": provider_id,
        "name": name,
        "configured": configured,
        "message": f"{name} server-side event forwarding is configured." if configured else missing_message,
        "state": "connected" if configured else "not_configured",
        "last_synced": None
    } for provider_id, name, configured, missing_message in definitions]


def get_analytics_status() -> Dict[str, Any]:
    """Backward-compatible summary; the provider status list is authoritative."""
    statuses = provider_statuses()
    return {
        "platform": "Mixpanel + PostHog + Amplitude",
        "configured": any(item["configured"] for item in statuses),
        "providers": statuses,
        "mode": "live" if any(item["configured"] for item in statuses) else "first_party_only"
    }


def _forward_mixpanel(event_name: str, distinct_id: str, event_id: str,
                      workspace_id: str, session_id: Optional[str], props: Dict[str, Any]) -> None:
    if not config.MIXPANEL_PROJECT_TOKEN:
        return
    event = {
        "event": event_name,
        "properties": {
            **props, "token": config.MIXPANEL_PROJECT_TOKEN,
            "distinct_id": distinct_id, "time": int(time.time()),
            "$insert_id": event_id, "workspace_id": workspace_id,
            **({"$device_id": session_id} if session_id else {}),
            "$lib": "ecomlytics-server"
        }
    }
    encoded = base64.b64encode(json.dumps(event, separators=(",", ":")).encode()).decode()
    response = httpx.post("https://api.mixpanel.com/track?ip=0", data=encoded, timeout=5.0)
    response.raise_for_status()
    if response.text.strip() not in {"1", "1\\n"}:
        raise RuntimeError(f"Mixpanel rejected event: {response.text[:200]}")


def _forward_posthog(event_name: str, distinct_id: str, event_id: str,
                     workspace_id: str, session_id: Optional[str], props: Dict[str, Any]) -> None:
    if not config.POSTHOG_PROJECT_TOKEN:
        return
    payload = {
        "api_key": config.POSTHOG_PROJECT_TOKEN,
        "event": event_name,
        "distinct_id": distinct_id,
        "properties": {
            **props, "workspace_id": workspace_id, "$insert_id": event_id,
            "$lib": "ecomlytics-server",
            **({"$session_id": session_id} if session_id else {})
        }
    }
    response = httpx.post(f"{config.POSTHOG_HOST}/i/v0/e/", json=payload, timeout=5.0)
    response.raise_for_status()
    try:
        result = response.json()
    except (ValueError, json.JSONDecodeError):
        result = {}
    if isinstance(result, dict) and result.get("quota_limited"):
        raise RuntimeError(f"PostHog ingestion quota limited: {result['quota_limited']}")


def _forward_amplitude(event_name: str, distinct_id: str, event_id: str,
                       workspace_id: str, session_id: Optional[str], props: Dict[str, Any]) -> None:
    if not config.AMPLITUDE_API_KEY:
        return
    event = {
        "user_id": distinct_id,
        "device_id": session_id or distinct_id,
        "event_type": event_name,
        "time": int(time.time() * 1000),
        "insert_id": event_id,
        "event_properties": {**props, "workspace_id": workspace_id, "session_id": session_id}
    }
    response = httpx.post(
        config.AMPLITUDE_INGEST_URL,
        json={"api_key": config.AMPLITUDE_API_KEY, "events": [event]},
        timeout=5.0
    )
    response.raise_for_status()
    result = response.json()
    if isinstance(result, dict) and result.get("code") not in (None, 200):
        raise RuntimeError(f"Amplitude rejected event: {result}")


def track_product_event(
    conn: sqlite3.Connection,
    workspace_id: str,
    event_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
) -> str:
    """Persist once in the first-party store, then best-effort fan out."""
    safe_props = _safe_properties(properties)
    event_id = record_event(
        conn=conn, workspace_id=workspace_id, event_name=event_name,
        user_id=user_id, session_id=session_id, properties=safe_props
    )
    conn.commit()

    distinct_id = str(user_id or session_id or "anonymous")
    # Deliver independently: a provider outage must not prevent the others receiving the event.
    for provider_name, forwarder in (
        ("Mixpanel", _forward_mixpanel),
        ("PostHog", _forward_posthog),
        ("Amplitude", _forward_amplitude)
    ):
        try:
            forwarder(event_name, distinct_id, event_id, workspace_id, session_id, safe_props)
        except Exception:
            logger.exception("%s event delivery failed (event=%s, event_id=%s)",
                             provider_name, event_name, event_id)
    return event_id
