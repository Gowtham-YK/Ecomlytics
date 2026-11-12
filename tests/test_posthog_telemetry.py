"""Tests for isolated multi-provider product analytics forwarding."""
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


def test_provider_statuses_reflect_configuration(monkeypatch):
    monkeypatch.setattr(config, "GA4_MEASUREMENT_ID", "G-N4DCRNR7VV")
    monkeypatch.setattr(config, "MIXPANEL_PROJECT_TOKEN", "mix-token")
    monkeypatch.setattr(config, "POSTHOG_API_KEY", "phc-test")
    monkeypatch.setattr(config, "AMPLITUDE_API_KEY", "amp-test")
    statuses = {item["id"]: item for item in product_analytics.provider_statuses()}
    assert statuses["google_analytics"]["configured"] is True
    assert statuses["mixpanel"]["configured"] is True
    assert statuses["posthog"]["configured"] is True
    assert statuses["amplitude"]["configured"] is True


def test_event_fans_out_independently_to_all_three_providers(test_db, monkeypatch):
    monkeypatch.setattr(config, "MIXPANEL_PROJECT_TOKEN", "mix-token")
    monkeypatch.setattr(config, "MIXPANEL_HOST", "https://api-eu.mixpanel.com")
    monkeypatch.setattr(config, "POSTHOG_API_KEY", "phc-test")
    monkeypatch.setattr(config, "POSTHOG_HOST", "https://us.i.posthog.com")
    monkeypatch.setattr(config, "AMPLITUDE_API_KEY", "amp-test")
    monkeypatch.setattr(config, "AMPLITUDE_INGEST_URL", "https://api2.amplitude.com/2/httpapi")

    user = register_user(test_db, "owner@example.com", "Password123!", "Store Owner", "Test Store")
    with patch.object(product_analytics, "_forward_mixpanel") as mixpanel, \
         patch.object(product_analytics, "_forward_posthog") as posthog, \
         patch.object(product_analytics, "_forward_amplitude") as amplitude:
        event_id = product_analytics.track_product_event(
            conn=test_db,
            workspace_id=user["workspace"]["id"],
            event_name="csv_upload_succeeded",
            user_id=user["id"],
            properties={"source_type": "orders", "password": "must-not-leak"},
        )
    assert event_id.startswith("evt_")
    row = test_db.execute("SELECT * FROM product_events WHERE id = ?", (event_id,)).fetchone()
    assert row["event_name"] == "csv_upload_succeeded"
    mixpanel.assert_called_once()
    posthog.assert_called_once()
    amplitude.assert_called_once()
    assert "password" not in mixpanel.call_args.args[3]


def test_provider_failure_does_not_block_other_providers(test_db, monkeypatch):
    monkeypatch.setattr(config, "MIXPANEL_PROJECT_TOKEN", "mix-token")
    monkeypatch.setattr(config, "POSTHOG_API_KEY", "phc-test")
    monkeypatch.setattr(config, "AMPLITUDE_API_KEY", "amp-test")
    user = register_user(test_db, "owner2@example.com", "Password123!", "Owner 2", "Store 2")
    with patch.object(product_analytics, "_forward_mixpanel", side_effect=ConnectionError("offline")), \
         patch.object(product_analytics, "_forward_posthog") as posthog, \
         patch.object(product_analytics, "_forward_amplitude") as amplitude:
        event_id = product_analytics.track_product_event(
            conn=test_db,
            workspace_id=user["workspace"]["id"],
            event_name="user_logged_in",
            user_id=user["id"],
        )
    assert event_id
    posthog.assert_called_once()
    amplitude.assert_called_once()
