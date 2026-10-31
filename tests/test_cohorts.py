import pytest
from pathlib import Path
from database.connection import init_db, get_db
from ingestion.importer import import_csv_dataset
from analytics.cohorts import compute_customer_cohorts


@pytest.fixture
def cohort_db(tmp_path: Path):
    db_file = tmp_path / "test_cohorts.db"
    init_db(db_file)
    with get_db(db_file) as conn:
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_c1', 'Cohort Store 1')")
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_c2', 'Cohort Store 2')")
    return db_file


def test_empty_cohort_returns_honest_no_data(cohort_db):
    with get_db(cohort_db) as conn:
        res = compute_customer_cohorts(conn, "ws_c1")
        assert res["status"] == "insufficient_data"
        assert len(res["cohorts"]) == 0


def test_cohort_matrix_calculations_and_isolation(cohort_db):
    orders_csv = """order_id,order_date,customer_id,revenue,status
ORD-1,2026-07-05,C1,100,completed
ORD-2,2026-07-15,C2,150,completed
ORD-3,2026-08-10,C1,200,completed
ORD-4,2026-08-20,C3,300,completed
ORD-5,2026-09-05,C1,120,completed
ORD-6,2026-09-12,C3,180,completed
"""
    with get_db(cohort_db) as conn:
        import_csv_dataset(conn, "ws_c1", "orders", orders_csv)

        res = compute_customer_cohorts(conn, "ws_c1")
        assert res["status"] == "available"
        assert len(res["cohorts"]) >= 2

        # 2026-07 cohort: C1, C2 -> size 2
        jul_cohort = next(c for c in res["cohorts"] if c["cohort_month"] == "2026-07")
        assert jul_cohort["cohort_size"] == 2
        assert jul_cohort["periods"][0]["retention_rate"] == 100.0
        assert jul_cohort["periods"][0]["retained_customers"] == 2

        # In Month 1 (August 2026): C1 returned, C2 did not -> 1 / 2 = 50.0%
        assert jul_cohort["periods"][1]["retained_customers"] == 1
        assert jul_cohort["periods"][1]["retention_rate"] == 50.0

        # In Month 2 (September 2026): C1 returned -> 1 / 2 = 50.0%
        assert jul_cohort["periods"][2]["retained_customers"] == 1
        assert jul_cohort["periods"][2]["retention_rate"] == 50.0

        # 2026-08 cohort: C3 -> size 1
        aug_cohort = next(c for c in res["cohorts"] if c["cohort_month"] == "2026-08")
        assert aug_cohort["cohort_size"] == 1
        assert aug_cohort["periods"][0]["retention_rate"] == 100.0
        # In Month 1 (September 2026): C3 returned -> 1 / 1 = 100.0%
        assert aug_cohort["periods"][1]["retained_customers"] == 1
        assert aug_cohort["periods"][1]["retention_rate"] == 100.0

        # Isolation: ws_c2 has 0 cohorts
        res2 = compute_customer_cohorts(conn, "ws_c2")
        assert res2["status"] == "insufficient_data"
        assert len(res2["cohorts"]) == 0
