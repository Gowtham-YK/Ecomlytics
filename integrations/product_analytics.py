"""
Product analytics integration adapter for Ecomlytics.
Supports first-party event capture and optional upstream forwarding to PostHog.
Operates gracefully in stub mode if external credentials are not configured.
"""

import os
import json
import sqlite3
from typing import Dict, Any, Optional
import httpx
from analytics.funnel import record_event

POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "")
POSTHOG_HOST = os.getenv("POSTHOG_HOST", "https://us.i.posthog.com")


def is_posthog_configured() -> bool:
    return bool(POSTHOG_API_KEY and POSTHOG_API_KEY.strip())


def get_analytics_status() -> Dict[str, Any]:
    """Reports configuration status for product analytics."""
    return {
        "platform": "PostHog",
        "configured": is_posthog_configured(),
        "host": POSTHOG_HOST if is_posthog_configured() else None,
        "mode": "live" if is_posthog_configured() else "first_party_only",
        "free_tier_allowance": "1,000,000 events/month"
    }


def track_product_event(
    conn: sqlite3.Connection,
    workspace_id: str,
    event_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
) -> str:
    """
    Captures an event in Ecomlytics' first-party store, and optionally
    fans out to PostHog if configured.
    """
    # 1. First-party local store
    event_id = record_event(
        conn=conn,
        workspace_id=workspace_id,
        event_name=event_name,
        user_id=user_id,
        session_id=session_id,
        properties=properties
    )

    # 2. Forward to PostHog if configured (best effort, non-blocking)
    if is_posthog_configured():
        try:
            payload = {
                "api_key": POSTHOG_API_KEY,
                "event": event_name,
                "distinct_id": user_id or session_id or "anonymous",
                "properties": {
                    **(properties or {}),
                    "workspace_id": workspace_id,
                    "$lib": "ecomlytics_python"
                }
            }
            # Fire HTTP POST with short timeout
            with httpx.Client(timeout=2.0) as client:
                client.post(f"{POSTHOG_HOST}/capture/", json=payload)
        except Exception:
            # External tracking failure must never break core application flow
            pass

    return event_id
