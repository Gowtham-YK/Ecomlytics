import pytest
from pathlib import Path
from database.connection import init_db, get_db
from analytics.funnel import record_event, compute_funnel, DEFAULT_PURCHASE_STEPS


@pytest.fixture
def funnel_db(tmp_path: Path):
    db_file = tmp_path / "test_funnel.db"
    init_db(db_file)
    with get_db(db_file) as conn:
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_f1', 'Funnel Store 1')")
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_f2', 'Funnel Store 2')")
    return db_file


def test_empty_funnel_honest_state(funnel_db):
    with get_db(funnel_db) as conn:
        res = compute_funnel(conn, "ws_f1")
        assert res["status"] == "insufficient_data"
        assert res["overall_conversion"] == 0.0
        assert all(s["count"] == 0 for s in res["stages"])


def test_ordered_funnel_progression_and_dropoffs(funnel_db):
    with get_db(funnel_db) as conn:
        # User 1: Completed all 4 steps
        record_event(conn, "ws_f1", "product_view", user_id="u1", occurred_at="2026-10-01T10:00:00")
        record_event(conn, "ws_f1", "add_to_cart", user_id="u1", occurred_at="2026-10-01T10:05:00")
        record_event(conn, "ws_f1", "checkout_started", user_id="u1", occurred_at="2026-10-01T10:10:00")
        record_event(conn, "ws_f1", "purchase_completed", user_id="u1", occurred_at="2026-10-01T10:15:00")
        # Duplicate event from User 1 should not inflate
        record_event(conn, "ws_f1", "purchase_completed", user_id="u1", occurred_at="2026-10-01T10:16:00")

        # User 2: Steps 1, 2, 3 (dropped off before purchase)
        record_event(conn, "ws_f1", "product_view", user_id="u2", occurred_at="2026-10-01T11:00:00")
        record_event(conn, "ws_f1", "add_to_cart", user_id="u2", occurred_at="2026-10-01T11:05:00")
        record_event(conn, "ws_f1", "checkout_started", user_id="u2", occurred_at="2026-10-01T11:10:00")

        # User 3: Step 1 and 2 only
        record_event(conn, "ws_f1", "product_view", user_id="u3", occurred_at="2026-10-01T12:00:00")
        record_event(conn, "ws_f1", "add_to_cart", user_id="u3", occurred_at="2026-10-01T12:05:00")

        # User 4: Step 1 only
        record_event(conn, "ws_f1", "product_view", user_id="u4", occurred_at="2026-10-01T13:00:00")

        # User 5: Out of order! Fired add_to_cart WITHOUT viewing product
        record_event(conn, "ws_f1", "add_to_cart", user_id="u5", occurred_at="2026-10-01T14:00:00")

        res = compute_funnel(conn, "ws_f1")
        assert res["status"] == "available"
        # Step 0 (View): u1, u2, u3, u4 -> 4 users
        assert res["stages"][0]["count"] == 4
        # Step 1 (Cart): u1, u2, u3 (u5 ignored as didn't start at step 0) -> 3 users
        assert res["stages"][1]["count"] == 3
        # Step 2 (Checkout): u1, u2 -> 2 users
        assert res["stages"][2]["count"] == 2
        # Step 3 (Purchase): u1 -> 1 user
        assert res["stages"][3]["count"] == 1

        # Conversions
        # 3 / 4 = 75.0%
        assert res["conversion_rates"]["Product Viewed -> Add to Cart"] == 75.0
        # 2 / 3 = 66.67%
        assert res["conversion_rates"]["Add to Cart -> Checkout Started"] == 66.67
        # 1 / 2 = 50.0%
        assert res["conversion_rates"]["Checkout Started -> Purchase Completed"] == 50.0
        # Overall: 1 / 4 = 25.0%
        assert res["overall_conversion"] == 25.0

        # Isolation: ws_f2 must have 0 events
        res2 = compute_funnel(conn, "ws_f2")
        assert res2["status"] == "insufficient_data"
        assert res2["stages"][0]["count"] == 0
