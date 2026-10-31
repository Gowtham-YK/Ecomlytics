import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from database.connection import init_db
from app import app


@pytest.fixture(autouse=True)
def setup_test_app_db(tmp_path: Path, monkeypatch):
    test_db = tmp_path / "test_api.db"
    monkeypatch.setenv("DATABASE_PATH", str(test_db))
    init_db(test_db)
    return test_db


@pytest.fixture
def client():
    return TestClient(app)


def test_unauthenticated_requests_blocked(client):
    # Public endpoints work
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "running"

    # Protected endpoints require auth
    protected_urls = [
        "/api/auth/me",
        "/api/overview",
        "/api/sales",
        "/api/products",
        "/api/customers/segments",
        "/api/funnels",
        "/api/cohorts",
        "/api/data-sources",
        "/api/imports"
    ]
    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 401, f"Expected 401 on {url}, got {res.status_code}"


def test_registration_and_login_flow(client):
    reg_payload = {
        "email": "owner@brand.com",
        "password": "SecurePassword123!",
        "display_name": "Brand Owner",
        "workspace_name": "Brand Store"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    assert reg_res.json()["user"]["email"] == "owner@brand.com"
    assert "token" in reg_res.json()
    token = reg_res.json()["token"]

    # Verify session cookie was set
    assert "ecomlytics_session" in reg_res.cookies

    # Test /api/auth/me using the cookie
    me_res = client.get("/api/auth/me", cookies={"ecomlytics_session": token})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "owner@brand.com"
    assert len(me_res.json()["workspaces"]) == 1

    # Test login with same credentials
    login_res = client.post("/api/auth/login", json={"email": "owner@brand.com", "password": "SecurePassword123!"})
    assert login_res.status_code == 200
    assert login_res.json()["success"] is True

    # Test login with bad password
    bad_login = client.post("/api/auth/login", json={"email": "owner@brand.com", "password": "WrongPassword"})
    assert bad_login.status_code == 401


def test_cross_user_workspace_data_isolation(client):
    # 1. Register User A
    user_a = client.post("/api/auth/register", json={
        "email": "user_a@test.com",
        "password": "PasswordA123!",
        "display_name": "User A",
        "workspace_name": "Store A"
    }).json()
    token_a = user_a["token"]
    ws_a_id = user_a["workspace"]["id"]

    # 2. User A imports orders
    csv_orders = """order_id,order_date,customer_id,product_id,quantity,revenue,status
ORD-101,2026-10-01,CUST-A,PROD-A,2,1000.0,completed
ORD-102,2026-10-02,CUST-A,PROD-A,1,500.0,completed
"""
    import_res = client.post(
        "/api/imports",
        json={"dataset_type": "orders", "csv_content": csv_orders, "filename": "orders_a.csv"},
        cookies={"ecomlytics_session": token_a}
    )
    assert import_res.status_code == 200
    assert import_res.json()["import_summary"]["imported_rows"] == 2

    # User A checks overview -> should see 2 orders, 1500 revenue
    overview_a = client.get("/api/overview", cookies={"ecomlytics_session": token_a}).json()
    assert overview_a["status"] == "available"
    assert overview_a["orders"] == 2
    assert overview_a["revenue"] == 1500.0

    # 3. Register User B
    user_b = client.post("/api/auth/register", json={
        "email": "user_b@test.com",
        "password": "PasswordB123!",
        "display_name": "User B",
        "workspace_name": "Store B"
    }).json()
    token_b = user_b["token"]

    # User B checks overview -> MUST BE EMPTY!
    overview_b = client.get("/api/overview", cookies={"ecomlytics_session": token_b}).json()
    assert overview_b["status"] == "no_data"
    assert overview_b["orders"] == 0
    assert overview_b["revenue"] == 0.0

    # User B attempts to access User A's workspace by header forgery
    forbidden_res = client.get(
        "/api/overview",
        headers={"X-Workspace-ID": ws_a_id},
        cookies={"ecomlytics_session": token_b}
    )
    assert forbidden_res.status_code == 403
    assert "Access denied" in forbidden_res.json()["detail"]
