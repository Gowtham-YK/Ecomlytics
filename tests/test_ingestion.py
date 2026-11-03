import pytest
from pathlib import Path
from database.connection import init_db, get_db
from ingestion.importer import import_csv_dataset, get_import_jobs


@pytest.fixture
def ingest_db(tmp_path: Path):
    db_file = tmp_path / "test_ingest.db"
    init_db(db_file)
    with get_db(db_file) as conn:
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_1', 'Store 1')")
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_2', 'Store 2')")
    return db_file


def test_import_orders_and_idempotency(ingest_db):
    sample_orders_csv = """order_id,order_date,customer_id,product_id,quantity,revenue,status
ORD-001,2026-09-01,CUST-1,PROD-1,2,500.00,completed
ORD-002,2026-09-02,CUST-2,PROD-2,1,250.00,completed
ORD-003,2026-09-03,CUST-1,PROD-1,1,250.00,returned
"""
    with get_db(ingest_db) as conn:
        res1 = import_csv_dataset(conn, "ws_1", "orders", sample_orders_csv, "test_orders.csv")
        assert res1["status"] == "completed"
        assert res1["total_rows"] == 3
        assert res1["imported_rows"] == 3
        assert res1["skipped_rows"] == 0

        # Verify DB counts in ws_1
        count_ws1 = conn.execute("SELECT count(*) as cnt FROM orders WHERE workspace_id = 'ws_1'").fetchone()["cnt"]
        assert count_ws1 == 3

        # Re-import identical CSV -> Idempotency test (all 3 should be skipped, no metric inflation)
        res2 = import_csv_dataset(conn, "ws_1", "orders", sample_orders_csv, "test_orders.csv")
        assert res2["imported_rows"] == 0
        assert res2["skipped_rows"] == 3
        count_ws1_after = conn.execute("SELECT count(*) as cnt FROM orders WHERE workspace_id = 'ws_1'").fetchone()["cnt"]
        assert count_ws1_after == 3

        # Workspace 2 should still be completely empty!
        count_ws2 = conn.execute("SELECT count(*) as cnt FROM orders WHERE workspace_id = 'ws_2'").fetchone()["cnt"]
        assert count_ws2 == 0


def test_malformed_rows_and_rejected_handling(ingest_db):
    csv_with_bad_date = """order_id,order_date,quantity,revenue,status
ORD-VALID,2026-10-01,1,100,completed
ORD-INVALID,not-a-date,1,200,completed
"""
    with get_db(ingest_db) as conn:
        res = import_csv_dataset(conn, "ws_1", "orders", csv_with_bad_date, "orders_bad.csv")
        assert res["total_rows"] == 2
        assert res["imported_rows"] == 1
        assert res["rejected_rows"] == 1
        assert len(res["errors"]) == 1
        assert "Invalid or missing date" in res["errors"][0]

        jobs = get_import_jobs(conn, "ws_1")
        assert len(jobs) >= 1
        assert jobs[0]["rejected_rows"] == 1


def test_import_products_and_customers(ingest_db):
    products_csv = """product_id,name,category,price,cost
P1,Organic Cotton Tee,Apparel,499,200
P2,Denim Jacket,Apparel,1299,600
"""
    customers_csv = """customer_id,name,email,city
C1,Aarav Patel,aarav@test.com,Mumbai
C2,Priya Sharma,priya@test.com,Bengaluru
"""
    with get_db(ingest_db) as conn:
        p_res = import_csv_dataset(conn, "ws_1", "products", products_csv, "products.csv")
        assert p_res["imported_rows"] == 2

        c_res = import_csv_dataset(conn, "ws_1", "customers", customers_csv, "customers.csv")
        assert c_res["imported_rows"] == 2

        p_cnt = conn.execute("SELECT count(*) as cnt FROM products WHERE workspace_id = 'ws_1'").fetchone()["cnt"]
        c_cnt = conn.execute("SELECT count(*) as cnt FROM customers WHERE workspace_id = 'ws_1'").fetchone()["cnt"]
        assert p_cnt == 2
        assert c_cnt == 2
