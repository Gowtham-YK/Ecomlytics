import sqlite3
import pytest
from pathlib import Path
from database.connection import create_connection, init_db, get_db


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_ecomlytics.db"
    init_db(db_file)
    return db_file


def test_schema_initialization(test_db):
    with get_db(test_db) as conn:
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]
        expected_tables = {
            "users",
            "workspaces",
            "workspace_members",
            "customers",
            "products",
            "orders",
            "import_jobs",
            "data_sources",
            "product_events",
        }
        assert expected_tables.issubset(set(tables))


def test_foreign_key_enforcement(test_db):
    with get_db(test_db) as conn:
        # Inserting a customer without a valid workspace should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO customers (id, workspace_id, name) VALUES ('c1', 'nonexistent_ws', 'Alice')"
            )


def test_cascade_delete(test_db):
    with get_db(test_db) as conn:
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws1', 'Test Store')")
        conn.execute("INSERT INTO customers (id, workspace_id, name) VALUES ('c1', 'ws1', 'Alice')")
        assert conn.execute("SELECT count(*) as cnt FROM customers WHERE workspace_id = 'ws1'").fetchone()["cnt"] == 1

        # Deleting workspace should cascade to customer
        conn.execute("DELETE FROM workspaces WHERE id = 'ws1'")
        assert conn.execute("SELECT count(*) as cnt FROM customers WHERE workspace_id = 'ws1'").fetchone()["cnt"] == 0
