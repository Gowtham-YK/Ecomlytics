# Ecomlytics — Multi-Tenant E-Commerce Product Intelligence & Decision Platform

Ecomlytics is a full-stack e-commerce analytics SaaS application built with **FastAPI**, **SQLite / PostgreSQL**, and a modern **vanilla HTML/CSS/JS** frontend. It enables multi-tenant store owners to import their catalog, customer, and order records, generating real-time sales performance, product margins, RFM customer segmentation, event-driven funnel conversion, and acquisition cohort retention matrices.

---

## 🚀 Key Features

1. **Persistent Authentication & Multi-Tenancy:**
   - Server-side account registration, password hashing with PBKDF2-HMAC-SHA256, and secure HttpOnly session tokens.
   - Strict workspace isolation: every order, customer, product, and event is strictly bounded by `workspace_id`.
2. **Honest Metrics & Zero Fabrication:**
   - No mock numbers or fake trends on authenticated workspaces.
   - Comprehensive handling of empty (`no_data`) and `insufficient_data` states.
3. **Validated CSV Ingestion & Idempotency:**
   - Drag-and-drop CSV importer for orders, products, and customers.
   - Header normalization, date parsing, and duplicate skipping to prevent metric inflation.
4. **Event-Driven Funnel Analytics:**
   - Multi-step funnel with chronological ordering, windowed completion, step conversion rates, and drop-off analysis.
5. **Customer Acquisition Cohorts & Retention Matrix:**
   - Monthly customer acquisition cohorts ($M_0, M_1, M_2, \dots$) with dynamic retention rate heatmaps.
6. **Product Analytics Integration:**
   - First-party event ingestion (`POST /api/events`) with evaluated PostHog integration architecture.

---

## 🛠️ Project Structure

```text
├── analytics/           # Central analytics engine, funnels, cohorts, service
│   ├── cohorts.py       # Customer acquisition cohort retention matrix
│   ├── funnel.py        # Event-driven funnel analysis
│   ├── metrics.py       # Baseline metric calculations & backward compatibility
│   └── service.py       # Multi-tenant workspace analytics queries
├── auth/                # Security, password hashing, session tokens, FastAPI dependencies
│   ├── dependencies.py  # get_current_user, get_current_workspace
│   ├── security.py      # PBKDF2-SHA256 hashing & signed HMAC session tokens
│   └── service.py       # User registration, login & workspace provisioning
├── database/            # Relational database persistence & schema
│   ├── connection.py    # Connection manager (SQLite/PostgreSQL fallback)
│   └── schema.sql       # Multi-tenant schema with tables & indexes
├── docs/                # Architectural & audit specifications
│   ├── analytics-platform-evaluation.md
│   ├── architecture-proposal.md
│   ├── cohort-analysis.md
│   ├── current-state-audit.md
│   ├── data-lineage-and-metric-inventory.md
│   ├── deployment-render.md
│   ├── funnel-analysis.md
│   ├── implementation-plan.md
│   └── metric-definitions.md
├── frontend/            # Responsive web application UI
│   ├── css/style.css    # Modern SaaS visual design system & cohort heatmap styles
│   ├── js/app.js        # Authenticated API client, routing, and dynamic charts
│   ├── pages/           # Sales, products, customers, retention, data sources, billing
│   └── login.html       # Server-authenticated login & registration
├── ingestion/           # CSV importer, normalization, and idempotency
│   └── importer.py
├── integrations/        # Google Analytics 4, Razorpay, and PostHog adapters
├── tests/               # Automated test suite (26 passing tests)
├── app.py               # FastAPI application entrypoint
└── requirements.txt
```

---

## 🏃 Running Locally

### 1. Setup Environment & Dependencies
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
```

### 2. Run Application Server
```powershell
python app.py
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

## 🧪 Running Automated Tests

Run the full automated test suite covering authentication, workspace isolation, database persistence, CSV ingestion idempotency, funnel ordering, cohort retention, and API contracts:

```powershell
python -m pytest tests/
```
*Current test suite: **26 passed** in 2.40s (100% pass rate).*

---

## 🌐 API Overview

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register` | Register new user & provision workspace | No |
| `POST` | `/api/auth/login` | Authenticate & receive session cookie | No |
| `POST` | `/api/auth/logout` | Invalidate active session | No |
| `GET` | `/api/auth/me` | Fetch active user profile & workspaces | Yes |
| `GET` | `/api/overview` | Workspace overview KPIs & period deltas | Yes |
| `GET` | `/api/sales` | Workspace daily sales trends | Yes |
| `GET` | `/api/products` | Workspace product margin & revenue ranking | Yes |
| `GET` | `/api/customers/segments` | Workspace customer RFM segmentation | Yes |
| `GET` | `/api/funnels` | Event-driven conversion funnels & drop-offs | Yes |
| `GET` | `/api/cohorts` | Acquisition cohort retention matrix | Yes |
| `GET` | `/api/data-sources` | Connection status for CSV, GA4, PostHog | Yes |
| `POST` | `/api/imports` | Idempotent CSV import (orders/products/customers)| Yes |
| `POST` | `/api/events` | Ingest product usage / behavioral events | Yes |
| `GET` | `/api/health` | Service and database health check | No |
