"""
Tests for PostHog product analytics integration and telemetry endpoints.
Verifies configuration detection, event capture, schema compliance,
and graceful offline/stub degradation.
"""

import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import config
from database.connection import init_db
from integrations import product_analytics
from auth.service import register_user


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_telemetry.db"
    init_db(db_file)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def test_posthog_configuration_detection():
    """Verifies that PostHog configuration status detects API key properly."""
    assert config.posthog_configured() is True
    status = product_analytics.get_analytics_status()
    assert status["platform"] == "PostHog"
    assert status["configured"] is True
    assert status["host"] == "https://us.i.posthog.com"
    assert status["mode"] == "live"


def test_posthog_event_local_capture_and_forwarding(test_db):
    """Verifies event is stored in SQLite first-party store and forwarded to PostHog."""
    # 1. Setup workspace
    user = register_user(test_db, "owner@example.com", "Password123!", "Store Owner", "Test Store")
    workspace_id = user["workspace"]["id"]
    user_id = user["id"]

    # 2. Mock httpx to intercept upstream PostHog HTTP POST
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client

        event_id = product_analytics.track_product_event(
            conn=test_db,
            workspace_id=workspace_id,
            event_name="csv_upload_succeeded",
            user_id=user_id,
            properties={
                "source_type": "orders",
                "row_count_bucket": "100-500",
                "imported_rows": 150,
                "skipped_rows": 0
            }
        )

        assert event_id is not None
        assert event_id.startswith("evt_")

        # Check local DB record
        row = test_db.execute("SELECT * FROM product_events WHERE id = ?", (event_id,)).fetchone()
        assert row is not None
        assert row["event_name"] == "csv_upload_succeeded"
        assert row["workspace_id"] == workspace_id
        assert row["user_id"] == user_id

        # Verify PostHog upstream HTTP dispatch was called
        mock_client.post.assert_called_once()
        call_args, call_kwargs = mock_client.post.call_args
        assert call_args[0].startswith("https://us.i.posthog.com/capture")
        payload = call_kwargs["json"]
        assert payload["event"] == "csv_upload_succeeded"
        assert payload["distinct_id"] == user_id
        assert payload["properties"]["source_type"] == "orders"
        assert payload["properties"]["workspace_id"] == workspace_id
        assert payload["properties"]["$lib"] == "ecomlytics_python"


def test_posthog_external_failure_never_breaks_core_flow(test_db):
    """Verifies external network/PostHog API errors are swallowed safely."""
    user = register_user(test_db, "owner2@example.com", "Password123!", "Owner 2", "Store 2")
    workspace_id = user["workspace"]["id"]

    # Mock httpx to raise an unexpected connection exception
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.side_effect = ConnectionError("PostHog connection timeout")
        mock_client_cls.return_value.__enter__.return_value = mock_client

        # Must not raise exception
        event_id = product_analytics.track_product_event(
            conn=test_db,
            workspace_id=workspace_id,
            event_name="user_logged_in",
            user_id=user["id"],
            properties={"login_method": "email"}
        )
        assert event_id is not None
