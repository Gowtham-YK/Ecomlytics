from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from analytics.metrics import (
    overview,
    product_metrics,
    customer_segments,
    funnel,
)

from insights.engine import generate_insights

from integrations.data_sources import list_data_sources
from integrations import google_analytics
import secrets
from fastapi import HTTPException, Request


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Ecomlytics API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CHECK FRONTEND DIRECTORIES
# ============================================================

if not FRONTEND_DIR.exists():
    raise RuntimeError(
        f"Frontend directory not found: {FRONTEND_DIR}"
    )

if not PAGES_DIR.exists():
    raise RuntimeError(
        f"Frontend pages directory not found: {PAGES_DIR}"
    )


# ============================================================
# ROOT
# ============================================================

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(
        url="/login.html",
        status_code=307,
    )


# ============================================================
# FRONTEND - MAIN PAGES
# ============================================================

@app.get("/login.html", include_in_schema=False)
def login_page():
    return FileResponse(
        FRONTEND_DIR / "login.html"
    )


@app.get("/index.html", include_in_schema=False)
def index_page():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# FRONTEND - CORRECT PAGE PATHS
# ============================================================

@app.get("/pages/sales.html", include_in_schema=False)
def sales_page():
    return FileResponse(
        PAGES_DIR / "sales.html"
    )


@app.get("/pages/products.html", include_in_schema=False)
def products_page():
    return FileResponse(
        PAGES_DIR / "products.html"
    )


@app.get("/pages/customers.html", include_in_schema=False)
def customers_page():
    return FileResponse(
        PAGES_DIR / "customers.html"
    )


@app.get("/pages/retention.html", include_in_schema=False)
def retention_page():
    return FileResponse(
        PAGES_DIR / "retention.html"
    )


@app.get("/pages/insights.html", include_in_schema=False)
def insights_page():
    return FileResponse(
        PAGES_DIR / "insights.html"
    )


@app.get("/pages/subscription.html", include_in_schema=False)
def subscription_page():
    return FileResponse(
        PAGES_DIR / "subscription.html"
    )


# ============================================================
# FRONTEND - OLD PATH COMPATIBILITY
# ============================================================
#
# These routes prevent 404 errors if an older app.js is still
# using /sales.html instead of /pages/sales.html.
#
# They redirect automatically to the correct location.
# ============================================================

@app.get("/sales.html", include_in_schema=False)
def old_sales_page():
    return RedirectResponse(
        url="/pages/sales.html",
        status_code=307,
    )


@app.get("/products.html", include_in_schema=False)
def old_products_page():
    return RedirectResponse(
        url="/pages/products.html",
        status_code=307,
    )


@app.get("/customers.html", include_in_schema=False)
def old_customers_page():
    return RedirectResponse(
        url="/pages/customers.html",
        status_code=307,
    )


@app.get("/retention.html", include_in_schema=False)
def old_retention_page():
    return RedirectResponse(
        url="/pages/retention.html",
        status_code=307,
    )


@app.get("/insights.html", include_in_schema=False)
def old_insights_page():
    return RedirectResponse(
        url="/pages/insights.html",
        status_code=307,
    )


# ============================================================
# API ROUTES
# ============================================================

@app.get("/api/overview")
def get_overview():
    return overview()


@app.get("/api/products")
def get_products():
    return product_metrics()


@app.get("/api/customers/segments")
def get_segments():
    return customer_segments()


@app.get("/api/funnel")
def get_funnel():
    return funnel()


@app.get("/api/insights")
def get_insights():
    return generate_insights()


@app.get("/api/subscription/plans")
def subscription_plans():
    return {
        "currency": "INR",
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "price": 0,
                "description": "Basic analytics for getting started.",
                "features": [
                    "Sales overview",
                    "Basic product analytics",
                    "Basic customer segments",
                    "Basic funnel metrics",
                ],
                "advanced": False,
            },
            {
                "id": "starter",
                "name": "Starter",
                "price": 999,
                "period": "month",
                "description": "Advanced analytics for growing stores.",
                "features": [
                    "Everything in Free",
                    "Advanced product intelligence",
                    "Margin and return analysis",
                    "Advanced retention analysis",
                    "Business insight recommendations",
                ],
                "advanced": True,
            },
            {
                "id": "growth",
                "name": "Growth",
                "price": 2999,
                "period": "month",
                "description": "Decision intelligence for scaling teams.",
                "features": [
                    "Everything in Starter",
                    "Advanced insight engine",
                    "Data-source integrations",
                    "Deeper customer intelligence",
                    "Priority analytics workflows",
                ],
                "advanced": True,
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 7999,
                "period": "month",
                "description": "The full Ecomlytics decision platform.",
                "features": [
                    "Everything in Growth",
                    "AI Advisor",
                    "Advanced recommendations",
                    "Executive decision views",
                    "Premium analytics capabilities",
                ],
                "advanced": True,
            },
        ],
    }


@app.post("/api/subscription/checkout")
async def demo_checkout(request: Request):
    payload = await request.json()
    plan = str(payload.get("plan", "")).lower()
    plans = {p["id"]: p for p in subscription_plans()["plans"]}
    if plan not in plans or plan == "free":
        raise HTTPException(status_code=400, detail="Choose a paid plan for checkout.")
    # Demo-only payment simulation. No real payment provider is connected.
    transaction_id = "ECO-" + secrets.token_hex(6).upper()
    return {
        "success": True,
        "mode": "demo",
        "transaction_id": transaction_id,
        "plan": plans[plan],
        "message": "Demo payment approved. No real money was charged.",
    }


@app.get("/api/health")
def health():
    return {
        "name": "Ecomlytics",
        "status": "running",
        "version": "1.0.0",
    }


# ============================================================
# DATA SOURCES / GOOGLE ANALYTICS
# ============================================================
#
# Honest connection state only. Nothing here claims to be "Live"
# unless real GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI are set.
# ============================================================

@app.get("/api/data-sources")
def get_data_sources():
    return {"sources": list_data_sources()}


@app.post("/api/data-sources/google/connect")
def connect_google_analytics():
    try:
        state = secrets.token_urlsafe(16)
        url = google_analytics.build_authorization_url(state)
        return {"authorization_url": url, "state": state}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/data-sources/google/callback")
def google_analytics_callback(code: str | None = None, state: str | None = None):
    # Token exchange against integrations.google_analytics.TOKEN_URL is
    # implemented at the adapter layer, but persisting the resulting
    # tokens requires the workspace/user model described in
    # ROADMAP.md, which is not yet built. Report this honestly rather
    # than pretending the connection succeeded.
    raise HTTPException(
        status_code=501,
        detail=(
            "OAuth callback received, but token storage requires the "
            "workspace/auth layer, which is not implemented yet. "
            "See ROADMAP.md."
        ),
    )


# ============================================================
# STATIC FILES
# ============================================================
#
# Serves:
#
# /css/style.css
# /js/app.js
# /favicon.svg
# /pages/...
#
# API routes and explicit page routes above take priority.
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True,
    ),
    name="frontend",
)


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )