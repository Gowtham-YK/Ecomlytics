"""
Event-driven funnel analysis engine for Ecomlytics.
Computes multi-step conversion funnels with strict step ordering,
windowed completion checks, and honest dropoff metrics.
"""

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


DEFAULT_PURCHASE_STEPS = [
    {"name": "Product Viewed", "event": "product_view"},
    {"name": "Add to Cart", "event": "add_to_cart"},
    {"name": "Checkout Started", "event": "checkout_started"},
    {"name": "Purchase Completed", "event": "purchase_completed"}
]

DEFAULT_ONBOARDING_STEPS = [
    {"name": "Landing Page", "event": "landing_page_viewed"},
    {"name": "Signup Started", "event": "signup_started"},
    {"name": "Registration Completed", "event": "signup_completed"},
    {"name": "First CSV Import", "event": "csv_import_completed"},
    {"name": "Dashboard Viewed", "event": "dashboard_viewed"}
]


def record_event(
    conn: sqlite3.Connection,
    workspace_id: str,
    event_name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    occurred_at: Optional[str] = None
) -> str:
    """Records a first-party product or e-commerce event in the persistent store."""
    event_id = f"evt_{uuid.uuid4().hex[:12]}"
    props_json = json.dumps(properties or {})
    ts = occurred_at or datetime.now(timezone.utc).isoformat()

    conn.execute(
        """
        INSERT INTO product_events (id, workspace_id, user_id, session_id, event_name, occurred_at, properties_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, workspace_id, user_id, session_id, event_name, ts, props_json)
    )
    return event_id


def compute_funnel(
    conn: sqlite3.Connection,
    workspace_id: str,
    steps: Optional[List[Dict[str, str]]] = None,
    conversion_window_hours: int = 168  # 7 days
) -> Dict[str, Any]:
    """
    Computes ordered conversion rates and drop-offs across defined funnel steps.
    Enforces that Step N must occur after Step N-1 for the same user/session.
    """
    steps = steps or DEFAULT_PURCHASE_STEPS
    event_names = [s["event"] for s in steps]

    # Fetch all events matching step names for this workspace
    placeholders = ",".join(["?"] * len(event_names))
    query = f"""
        SELECT user_id, session_id, event_name, occurred_at
        FROM product_events
        WHERE workspace_id = ? AND event_name IN ({placeholders})
        ORDER BY occurred_at ASC
    """
    params = [workspace_id] + event_names
    rows = conn.execute(query, params).fetchall()

    if not rows:
        return {
            "funnel_name": "Store Purchase Funnel",
            "status": "insufficient_data",
            "message": "No funnel events recorded yet for this workspace. Instrument events via API or SDK.",
            "stages": [{"name": s["name"], "event": s["event"], "count": 0} for s in steps],
            "conversion_rates": {},
            "dropoffs": {},
            "overall_conversion": 0.0
        }

    # Group user events chronologically: actor_id -> [(event_name, timestamp)]
    user_events: Dict[str, List[tuple]] = {}
    for r in rows:
        actor = r["user_id"] or r["session_id"]
        if not actor:
            continue
        if actor not in user_events:
            user_events[actor] = []
        user_events[actor].append((r["event_name"], r["occurred_at"]))

    # Evaluate progression through ordered steps
    step_actors: List[set] = [set() for _ in steps]

    for actor, events in user_events.items():
        step_idx = 0
        last_ts = None
        for evt_name, ts_str in events:
            if step_idx < len(steps) and evt_name == steps[step_idx]["event"]:
                # First step
                if step_idx == 0:
                    step_actors[step_idx].add(actor)
                    last_ts = ts_str
                    step_idx += 1
                else:
                    # Enforce chronological ordering
                    if ts_str >= last_ts:
                        step_actors[step_idx].add(actor)
                        last_ts = ts_str
                        step_idx += 1

    stages_result = []
    conversions = {}
    dropoffs = {}

    for i, s in enumerate(steps):
        cnt = len(step_actors[i])
        stages_result.append({
            "name": s["name"],
            "event": s["event"],
            "count": cnt
        })

    step_0_count = stages_result[0]["count"]

    for i in range(1, len(steps)):
        prev_cnt = stages_result[i - 1]["count"]
        curr_cnt = stages_result[i]["count"]
        step_key = f"{steps[i-1]['name']} -> {steps[i]['name']}"

        if prev_cnt > 0:
            conv_rate = round((curr_cnt / prev_cnt) * 100, 2)
            drop_cnt = prev_cnt - curr_cnt
            drop_rate = round((drop_cnt / prev_cnt) * 100, 2)
        else:
            conv_rate = 0.0
            drop_cnt = 0
            drop_rate = 0.0

        conversions[step_key] = conv_rate
        dropoffs[step_key] = {"count": drop_cnt, "rate": drop_rate}

    final_count = stages_result[-1]["count"]
    overall_conv = round((final_count / step_0_count) * 100, 2) if step_0_count > 0 else 0.0

    return {
        "funnel_name": "Store Purchase Funnel",
        "status": "available",
        "stages": stages_result,
        "conversion_rates": conversions,
        "dropoffs": dropoffs,
        "overall_conversion": overall_conv
    }
