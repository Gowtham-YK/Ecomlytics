import pytest
from pathlib import Path
from database.connection import init_db, get_db
from ingestion.importer import import_csv_dataset
from analytics.service import (
    get_workspace_overview,
    get_workspace_sales_trend,
    get_workspace_products,
    get_workspace_customer_segments
)


@pytest.fixture
def analytics_db(tmp_path: Path):
    db_file = tmp_path / "test_analytics.db"
    init_db(db_file)
    with get_db(db_file) as conn:
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_a', 'Store A')")
        conn.execute("INSERT INTO workspaces (id, name) VALUES ('ws_b', 'Store B')")
    return db_file


def test_empty_workspace_returns_honest_no_data(analytics_db):
    with get_db(analytics_db) as conn:
        res = get_workspace_overview(conn, "ws_a")
        assert res["status"] == "no_data"
        assert res["revenue"] == 0.0
        assert res["orders"] == 0
        assert res["aov"] == 0.0
        assert res["comparison"]["status"] == "insufficient_data"


def test_workspace_overview_calculations_and_isolation(analytics_db):
    orders_a = """order_id,order_date,customer_id,product_id,quantity,revenue,status
O1,2026-10-01,C1,P1,2,500.0,completed
O2,2026-10-05,C1,P1,1,250.0,completed
O3,2026-10-10,C2,P2,1,150.0,completed
O4,2026-10-12,C3,P2,1,150.0,returned
"""
    products_a = """product_id,name,category,price,cost
P1,Shirt,Apparel,250.0,100.0
P2,Cap,Apparel,150.0,50.0
"""
    customers_a = """customer_id,name,email,city
C1,Aarav,a@test.com,Delhi
C2,Bhavna,b@test.com,Mumbai
C3,Charan,c@test.com,Pune
"""

    with get_db(analytics_db) as conn:
        import_csv_dataset(conn, "ws_a", "orders", orders_a)
        import_csv_dataset(conn, "ws_a", "products", products_a)
        import_csv_dataset(conn, "ws_a", "customers", customers_a)

        overview_a = get_workspace_overview(conn, "ws_a")
        assert overview_a["status"] == "available"
        assert overview_a["orders"] == 3  # O1, O2, O3 completed
        assert overview_a["revenue"] == 900.0  # 500 + 250 + 150
        assert overview_a["aov"] == 300.0  # 900 / 3
        assert overview_a["units"] == 4  # 2 + 1 + 1
        assert overview_a["returned_orders"] == 1
        assert overview_a["return_rate"] == 25.0  # 1 return / 4 total
        # Repeat customer: C1 has 2 completed orders, C2 has 1 -> 1 / 3 = 33.3%
        assert overview_a["repeat_rate"] == 33.3

        # ISOLATION: Workspace B must have zero data
        overview_b = get_workspace_overview(conn, "ws_b")
        assert overview_b["status"] == "no_data"
        assert overview_b["orders"] == 0
        assert overview_b["revenue"] == 0.0


def test_products_and_segments_workspace_scoped(analytics_db):
    orders_a = """order_id,order_date,customer_id,product_id,quantity,revenue,status
O1,2026-10-01,C1,P1,4,1000.0,completed
"""
    products_a = """product_id,name,category,price,cost
P1,Shirt,Apparel,250.0,100.0
"""
    with get_db(analytics_db) as conn:
        import_csv_dataset(conn, "ws_a", "orders", orders_a)
        import_csv_dataset(conn, "ws_a", "products", products_a)

        prods = get_workspace_products(conn, "ws_a")
        assert len(prods) == 1
        assert prods[0]["name"] == "Shirt"
        assert prods[0]["units_sold"] == 4
        assert prods[0]["revenue"] == 1000.0
        assert prods[0]["margin"] == 60.0  # (250 - 100) / 250 = 60%

        prods_b = get_workspace_products(conn, "ws_b")
        assert len(prods_b) == 0
