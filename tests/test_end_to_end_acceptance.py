"""
End-to-end acceptance test fulfilling Section 15.10 of the Master Implementation Specification.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from database.connection import init_db
from app import app


@pytest.fixture(autouse=True)
def setup_acceptance_db(tmp_path: Path, monkeypatch):
    test_db = tmp_path / "acceptance.db"
    monkeypatch.setenv("DATABASE_PATH", str(test_db))
    init_db(test_db)
    return test_db


def test_full_acceptance_journey():
    client = TestClient(app)

    # 1. Register User A
    res_a = client.post("/api/auth/register", json={
        "email": "retailer_a@urbanthreads.com",
        "password": "PasswordA123!",
        "display_name": "Retailer A",
        "workspace_name": "Urban Threads"
    })
    assert res_a.status_code == 201
    user_a = res_a.json()
    token_a = user_a["token"]
    ws_a_id = user_a["workspace"]["id"]

    # 2. Verify User A initially has honest no_data state
    initial_overview = client.get("/api/overview", cookies={"ecomlytics_session": token_a}).json()
    assert initial_overview["status"] == "no_data"
    assert initial_overview["orders"] == 0

    # 3. User A imports controlled orders dataset
    orders_csv_a = """order_id,order_date,customer_id,product_id,quantity,revenue,status
A-101,2026-10-01,CUST-A1,PROD-1,2,500.0,completed
A-102,2026-10-02,CUST-A2,PROD-2,1,300.0,completed
A-103,2026-10-03,CUST-A1,PROD-1,1,250.0,completed
A-104,2026-10-04,CUST-A3,PROD-2,1,300.0,returned
"""
    imp_a = client.post(
        "/api/imports",
        json={"dataset_type": "orders", "csv_content": orders_csv_a, "filename": "orders_a.csv"},
        cookies={"ecomlytics_session": token_a}
    )
    assert imp_a.status_code == 200
    assert imp_a.json()["import_summary"]["imported_rows"] == 4

    # 4. Verify User A key metrics against manual calculations
    # Completed orders: A-101, A-102, A-103 -> 3 orders
    # Completed revenue: 500 + 300 + 250 = 1050.0
    # AOV = 1050 / 3 = 350.0
    # Units = 2 + 1 + 1 = 4
    # Returned = 1, Return Rate = 1 / 4 = 25.0%
    # Distinct purchasing customers: CUST-A1 (2 orders), CUST-A2 (1 order) -> 2 customers
    # Repeat customers: CUST-A1 (2 orders) -> Repeat rate = 1 / 2 = 50.0%
    overview_a = client.get("/api/overview", cookies={"ecomlytics_session": token_a}).json()
    assert overview_a["status"] == "available"
    assert overview_a["orders"] == 3
    assert overview_a["revenue"] == 1050.0
    assert overview_a["aov"] == 350.0
    assert overview_a["units"] == 4
    assert overview_a["returned_orders"] == 1
    assert overview_a["return_rate"] == 25.0
    assert overview_a["repeat_rate"] == 50.0

    # 5. Sign out User A
    signout_res = client.post("/api/auth/logout")
    assert signout_res.status_code == 200

    # 6. Register User B
    res_b = client.post("/api/auth/register", json={
        "email": "retailer_b@artisan.co",
        "password": "PasswordB123!",
        "display_name": "Retailer B",
        "workspace_name": "Artisan Co"
    })
    assert res_b.status_code == 201
    user_b = res_b.json()
    token_b = user_b["token"]
    ws_b_id = user_b["workspace"]["id"]
    assert ws_b_id != ws_a_id

    # 7. User B imports a completely different dataset
    orders_csv_b = """order_id,order_date,customer_id,product_id,quantity,revenue,status
B-901,2026-10-15,CUST-B1,PROD-B,10,2000.0,completed
"""
    imp_b = client.post(
        "/api/imports",
        json={"dataset_type": "orders", "csv_content": orders_csv_b, "filename": "orders_b.csv"},
        cookies={"ecomlytics_session": token_b}
    )
    assert imp_b.status_code == 200
    assert imp_b.json()["import_summary"]["imported_rows"] == 1

    # 8. Verify User B sees ONLY their data (1 order, 2000.0 revenue)
    overview_b = client.get("/api/overview", cookies={"ecomlytics_session": token_b}).json()
    assert overview_b["orders"] == 1
    assert overview_b["revenue"] == 2000.0

    # 9. Verify User B CANNOT read or forge access to User A's workspace
    cross_access = client.get(
        "/api/overview",
        headers={"X-Workspace-ID": ws_a_id},
        cookies={"ecomlytics_session": token_b}
    )
    assert cross_access.status_code == 403
    assert "Access denied" in cross_access.json()["detail"]

    # 10. Confirm sensitive secrets (passwords / hashes) never appear in responses
    user_profile = client.get("/api/auth/me", cookies={"ecomlytics_session": token_b}).json()
    assert "password" not in user_profile
    assert "password_hash" not in user_profile
