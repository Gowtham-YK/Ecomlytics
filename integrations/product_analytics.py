"""Unified first-party event capture and multi-provider analytics forwarding.

Events are stored locally first. Each configured provider is then called
independently so an outage at one vendor never blocks the others.
"""
import base64
import json
import logging
import sqlite3
import time
from typing import Dict, Any, Optional

import httpx
import config
from analytics.funnel import record_event

logger = logging.getLogger(__name__)


def provider_statuses() -> list:
    return [
        {
            "id": "google_analytics",
            "name": "Google Analytics 4",
            "configured": config.ga4_measurement_configured(),
            "state": "configured" if config.ga4_measurement_configured() else "not_configured",
            "message": "Browser event tracking configured; OAuth reporting is separate.",
            "measurement_id": config.GA4_MEASUREMENT_ID if config.ga4_measurement_configured() else None,
        },
        {
            "id": "mixpanel",
            "name": "Mixpanel",
            "configured": config.mixpanel_configured(),
            "state": "configured" if config.mixpanel_configured() else "not_configured",
            "message": "Server-side event forwarding enabled." if config.mixpanel_configured() else "Add MIXPANEL_PROJECT_TOKEN to enable forwarding.",
        },
        {
            "id": "posthog",
            "name": "PostHog",
            "configured": config.posthog_configured(),
            "state": "configured" if config.posthog_configured() else "not_configured",
            "message": "Server-side event forwarding enabled." if config.posthog_configured() else "Add POSTHOG_PROJECT_TOKEN to enable forwarding.",
            "host": config.POSTHOG_HOST,
        },
        {
            "id": "amplitude",
            "name": "Amplitude",
            "configured": config.amplitude_configured(),
            "state": "configured" if config.amplitude_configured() else "not_configured",
            "message": "Server-side event forwarding enabled." if config.amplitude_configured() else "Add AMPLITUDE_API_KEY to enable forwarding.",
        },
    ]


def get_analytics_status() -> Dict[str, Any]:
    """Backward-compatible PostHog status helper."""
    posthog = next(x for x in provider_statuses() if x["id"] == "posthog")
    return {
        "platform": "PostHog",
        "configured": posthog["configured"],
        "host": config.POSTHOG_HOST if posthog["configured"] else None,
        "mode": "live" if posthog["configured"] else "first_party_only",
    }


def _post_json(url: str, payload: dict) -> None:
    with httpx.Client(timeout=4.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()


def _forward_mixpanel(event_name: str, distinct_id: str, workspace_id: str,
                      properties: dict, event_id: str) -> None:
    if not config.mixpanel_configured():
        return
    event = {
        "event": event_name,
        "properties": {
            **properties,
            "token": config.MIXPANEL_PROJECT_TOKEN,
            "distinct_id": distinct_id,
            "time": int(time.time()),
            "$insert_id": event_id,
            "workspace_id": workspace_id,
        },
    }
    encoded = base64.b64encode(json.dumps(event).encode("utf-8")).decode("ascii")
    with httpx.Client(timeout=4.0) as client:
        response = client.post(
            f"{config.MIXPANEL_HOST.rstrip('/')}/track?ip=0",
            data={"data": encoded},
        )
        response.raise_for_status()


def _forward_posthog(event_name: str, distinct_id: str, workspace_id: str,
                     properties: dict, event_id: str) -> None:
    if not config.posthog_configured():
        return
    _post_json(
        f"{config.POSTHOG_HOST.rstrip('/')}/i/v0/e/",
        {
            "api_key": config.POSTHOG_API_KEY,
            "event": event_name,
            "distinct_id": distinct_id,
            "properties": {
                **properties,
                "workspace_id": workspace_id,
                "$lib": "ecomlytics_python",
                "$insert_id": event_id,
            },
        },
    )


def _forward_amplitude(event_name: str, distinct_id: str, workspace_id: str,
                       properties: dict, event_id: str) -> None:
    if not config.amplitude_configured():
        return
    _post_json(
        config.AMPLITUDE_INGEST_URL,
        {
            "api_key": config.AMPLITUDE_API_KEY,
            "events": [{
                "user_id": distinct_id,
                "event_type": event_name,
                "time": int(time.time() * 1000),
                "insert_id": event_id,
                "event_properties": {**properties, "workspace_id": workspace_id},
                "platform": "Web",
                "library": "Ecomlytics",
            }],
        },
    )


def track_product_event(
    conn: sqlite3.Connection,
    workspace_id: str,
    event_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist one event, then best-effort forward it to all configured vendors."""
    safe_properties = dict(properties or {})
    for sensitive in ("password", "token", "secret", "authorization", "csv_content"):
        safe_properties.pop(sensitive, None)

    event_id = record_event(
        conn=conn,
        workspace_id=workspace_id,
        event_name=event_name,
        user_id=user_id,
        session_id=session_id,
        properties=safe_properties,
    )
    distinct_id = str(user_id or session_id or "anonymous")
    forwarders = (
        ("Mixpanel", _forward_mixpanel),
        ("PostHog", _forward_posthog),
        ("Amplitude", _forward_amplitude),
    )
    for provider, forwarder in forwarders:
        try:
            forwarder(event_name, distinct_id, workspace_id, safe_properties, event_id)
        except Exception:
            logger.exception("%s event forwarding failed for event_id=%s", provider, event_id)
    return event_id
