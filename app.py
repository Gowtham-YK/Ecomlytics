"""
Ecomlytics — Secure, Multi-Tenant E-Commerce Product Intelligence API.
"""

from pathlib import Path
import os
import sqlite3
import secrets
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from database.connection import init_db, get_db
from auth.security import create_session_token, verify_session_token
from auth.service import register_user, authenticate_user, get_user_by_id
from auth.dependencies import get_db_session, get_current_user, get_current_workspace
from ingestion.importer import import_csv_dataset, get_import_jobs
from analytics.service import (
    get_workspace_overview,
    get_workspace_sales_trend,
    get_workspace_products,
    get_workspace_customer_segments,
)
from analytics.funnel import compute_funnel, record_event
from analytics.cohorts import compute_customer_cohorts
from integrations import google_analytics, razorpay_client, product_analytics
import config

# ============================================================
# PATHS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="Ecomlytics API",
    version="2.0.0",
    description="Multi-Tenant E-Commerce Product Intelligence Engine"
)

# Initialize database tables on load
init_db()

# ============================================================
# PYDANTIC SCHEMAS
# ============================================================
class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)
    display_name: str
    workspace_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str

class ImportCsvRequest(BaseModel):
    dataset_type: str
    csv_content: str
    filename: Optional[str] = "dataset.csv"

class EventRequest(BaseModel):
    event_name: str
    session_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None

# ============================================================
# AUTHENTICATION API ROUTES
# ============================================================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def api_register(
    req: RegisterRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Registers a new user, hashes password, creates workspace, and sets session cookie."""
    try:
        user_data = register_user(
            conn=conn,
            email=req.email,
            password=req.password,
            display_name=req.display_name,
            workspace_name=req.workspace_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    token = create_session_token(user_data["id"])
    response.set_cookie(
        key="ecomlytics_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        secure=False  # Set True in production with HTTPS
    )

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "display_name": user_data["display_name"]
        },
        "workspace": user_data["workspace"]
    }


@app.post("/api/auth/login")
def api_login(
    req: LoginRequest,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Authenticates credentials, returns user profile, and sets session cookie."""
    try:
        user_data = authenticate_user(
            conn=conn,
            email=req.email,
            password=req.password
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_session_token(user_data["id"])
    response.set_cookie(
        key="ecomlytics_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
        secure=False
    )

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "display_name": user_data["display_name"]
        },
        "workspaces": user_data["workspaces"]
    }


@app.post("/api/auth/logout")
def api_logout(response: Response):
    """Logs out user by clearing session cookie."""
    response.delete_cookie(key="ecomlytics_session")
    return {"success": True, "message": "Signed out successfully."}


@app.get("/api/auth/me")
def api_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Returns currently authenticated user profile and workspaces."""
    return current_user


# ============================================================
# WORKSPACE & DATA SOURCE ROUTES
# ============================================================

@app.get("/api/workspaces/current")
def api_current_workspace(workspace: Dict[str, Any] = Depends(get_current_workspace)):
    """Returns details of the currently authorized workspace."""
    return workspace


@app.get("/api/data-sources")
def api_data_sources(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Reports real connection status of workspace data sources."""
    ws_id = workspace["id"]
    
    # Check import history counts in DB
    orders_cnt = conn.execute("SELECT COUNT(*) as c FROM orders WHERE workspace_id = ?", (ws_id,)).fetchone()["c"]
    prods_cnt = conn.execute("SELECT COUNT(*) as c FROM products WHERE workspace_id = ?", (ws_id,)).fetchone()["c"]
    custs_cnt = conn.execute("SELECT COUNT(*) as c FROM customers WHERE workspace_id = ?", (ws_id,)).fetchone()["c"]
    
    has_csv = (orders_cnt > 0 or prods_cnt > 0 or custs_cnt > 0)
    
    last_import = conn.execute(
        "SELECT MAX(created_at) as m FROM import_jobs WHERE workspace_id = ?", (ws_id,)
    ).fetchone()["m"]

    csv_source = {
        "id": "workspace_csv",
        "name": "Store CSV Data",
        "state": "connected" if has_csv else "disconnected",
        "message": f"{orders_cnt} orders, {prods_cnt} products, {custs_cnt} customers loaded." if has_csv else "No datasets imported yet. Use Import CSV above.",
        "last_synced": last_import
    }

    ga4_status = google_analytics.status()
    posthog_status = product_analytics.get_analytics_status()

    return [
        csv_source,
        ga4_status,
        {
            "id": "posthog",
            "name": "PostHog Analytics",
            "state": "connected" if posthog_status["configured"] else "stub_mode",
            "message": "Live PostHog capture active" if posthog_status["configured"] else "Local first-party event store active (PostHog API key optional).",
            "last_synced": None
        }
    ]


@app.post("/api/imports")
def api_import_csv(
    req: ImportCsvRequest,
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Safely parses and imports CSV dataset into the authenticated workspace."""
    try:
        summary = import_csv_dataset(
            conn=conn,
            workspace_id=workspace["id"],
            dataset_type=req.dataset_type,
            csv_content=req.csv_content,
            filename=req.filename or "uploaded.csv"
        )
        return {"success": True, "import_summary": summary}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Import error: {str(exc)}")


@app.get("/api/imports")
def api_list_imports(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Retrieves import job history for current workspace."""
    return get_import_jobs(conn, workspace["id"])


# ============================================================
# ANALYTICS API ROUTES (WORKSPACE-SCOPED)
# ============================================================

@app.get("/api/overview")
def get_overview(
    days: int = 30,
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns standardized overview KPI metrics for the authorized workspace."""
    return get_workspace_overview(conn, workspace["id"], days=days)


@app.get("/api/sales")
def get_sales(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns sales trend metrics for the authorized workspace."""
    return {
        "workspace_id": workspace["id"],
        "sales_trend": get_workspace_sales_trend(conn, workspace["id"])
    }


@app.get("/api/products")
def get_products(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns workspace-scoped products ranked by revenue and units sold."""
    return get_workspace_products(conn, workspace["id"])


@app.get("/api/customers/segments")
def get_segments(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns customer RFM segmentation based on verified workspace order history."""
    return get_workspace_customer_segments(conn, workspace["id"])


@app.get("/api/funnels")
@app.get("/api/funnel")
def get_funnel(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns event-driven funnel conversion rates and drop-offs."""
    return compute_funnel(conn, workspace["id"])


@app.get("/api/cohorts")
@app.get("/api/retention")
def get_cohorts(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Returns customer acquisition cohort matrix and retention rates."""
    return compute_customer_cohorts(conn, workspace["id"])


@app.get("/api/insights")
def get_insights(
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Generates evidence-backed business insights from workspace data."""
    overview_data = get_workspace_overview(conn, workspace["id"])
    if overview_data["status"] == "no_data":
        return {
            "status": "no_data",
            "message": "No store orders available yet. Import a dataset to generate automated insights.",
            "insights": []
        }

    products = get_workspace_products(conn, workspace["id"])
    insights = []

    # Insight 1: AOV & Basket size
    aov = overview_data.get("aov", 0)
    if aov > 0:
        insights.append({
            "type": "opportunity",
            "title": f"Average Order Value at ₹{aov:,.2f}",
            "detail": f"Completed orders average ₹{aov:,.2f}. Introducing product bundles or post-checkout cross-sells can raise basket size.",
            "metric": "aov",
            "value": aov
        })

    # Insight 2: Return Rate warning
    return_rate = overview_data.get("return_rate", 0)
    if return_rate > 15:
        insights.append({
            "type": "warning",
            "title": f"Elevated Return Rate ({return_rate}%)",
            "detail": f"Returns account for {return_rate}% of processed volume. Inspect product descriptions and sizing charts to reduce return frequency.",
            "metric": "return_rate",
            "value": return_rate
        })

    # Insight 3: Top Performing Product
    if products:
        top_prod = products[0]
        if top_prod.get("revenue", 0) > 0:
            insights.append({
                "type": "growth",
                "title": f"Top Revenue Driver: {top_prod['name']}",
                "detail": f"Generated ₹{top_prod['revenue']:,.2f} with {top_prod['units_sold']} units sold. Ensure adequate inventory to prevent stockouts.",
                "metric": "top_product",
                "value": top_prod["revenue"]
            })

    return {
        "status": "available",
        "workspace_id": workspace["id"],
        "insights": insights
    }


# ============================================================
# EVENT INGESTION ROUTE
# ============================================================

@app.post("/api/events")
def api_track_event(
    req: EventRequest,
    workspace: Dict[str, Any] = Depends(get_current_workspace),
    current_user: Dict[str, Any] = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db_session)
):
    """Captures first-party product usage events."""
    event_id = product_analytics.track_product_event(
        conn=conn,
        workspace_id=workspace["id"],
        event_name=req.event_name,
        user_id=current_user["id"],
        session_id=req.session_id,
        properties=req.properties
    )
    return {"success": True, "event_id": event_id}


# ============================================================
# SUBSCRIPTION & BILLING (DEMO / OPTIONAL)
# ============================================================

@app.get("/api/subscription/plans")
def subscription_plans():
    return {
        "currency": "INR",
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "description": "Essential analytics for small stores.",
                "features": [
                    "Sales overview & metrics",
                    "Product analytics",
                    "Customer segmentation",
                    "Funnel analysis"
                ],
                "advanced": False,
            },
            {
                "id": "pro",
                "name": "Pro Pack",
                "price": 49,
                "period": "month",
                "description": "Full Ecomlytics decision platform & AI insights.",
                "features": [
                    "Everything in Free",
                    "Cohort retention analysis",
                    "Automated business insights",
                    "PostHog / GA4 integrations"
                ],
                "advanced": True,
            }
        ],
    }


@app.post("/api/subscription/checkout")
async def demo_checkout(request: Request):
    payload = await request.json()
    plan = str(payload.get("plan", "")).lower()
    if plan != "pro":
        raise HTTPException(status_code=400, detail="Choose a paid plan for checkout.")
    transaction_id = "ECO-" + secrets.token_hex(6).upper()
    return {
        "success": True,
        "mode": "demo",
        "transaction_id": transaction_id,
        "message": "Demo payment approved. No real money was charged."
    }


@app.get("/api/subscription/razorpay/config")
def razorpay_config():
    return {
        "configured": razorpay_client.is_configured(),
        "key_id": config.RAZORPAY_KEY_ID or "rzp_test_demo",
        "mode": "live" if "live" in config.RAZORPAY_KEY_ID.lower() else ("test" if razorpay_client.is_configured() else "demo"),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health(conn: sqlite3.Connection = Depends(get_db_session)):
    """Safe system and database health check."""
    try:
        conn.execute("SELECT 1").fetchone()
        db_status = "healthy"
    except Exception:
        db_status = "degraded"

    return {
        "name": "Ecomlytics",
        "status": "running",
        "version": "2.0.0",
        "database": db_status
    }


# ============================================================
# STATIC PAGES & FRONTEND MOUNT
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login.html", status_code=307)

@app.get("/login.html", include_in_schema=False)
def login_page():
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/index.html", include_in_schema=False)
def index_page():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/pages/{page_name}.html", include_in_schema=False)
def get_page(page_name: str):
    target = PAGES_DIR / f"{page_name}.html"
    if target.exists():
        return FileResponse(target)
    raise HTTPException(status_code=404, detail="Page not found")

# Compatibility redirects
@app.get("/{page_name}.html", include_in_schema=False)
def redirect_old_pages(page_name: str):
    target = PAGES_DIR / f"{page_name}.html"
    if target.exists():
        return RedirectResponse(url=f"/pages/{page_name}.html", status_code=307)
    raise HTTPException(status_code=404, detail="Page not found")

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)