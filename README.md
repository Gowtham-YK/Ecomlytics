# Ecomlytics — Multi-Tenant E-Commerce Product Intelligence & Decision Platform

[![Live App](https://img.shields.io/badge/Live%20Deployment-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://ecomlytics.onrender.com/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20v2.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20WAL%20%2F%20PostgreSQL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Google Analytics 4](https://img.shields.io/badge/Telemetry-GA4%20(G--KYK82K8M9J)-F9AB00?style=flat-square&logo=google-analytics&logoColor=white)](https://analytics.google.com/)
[![Test Suite](https://img.shields.io/badge/Tests-26%20Passed%20(100%25)-brightgreen?style=flat-square&logo=pytest&logoColor=white)](https://pytest.org/)

**Ecomlytics** is a multi-tenant, full-stack e-commerce intelligence and decision platform. Built for budding direct-to-consumer (D2C) brands, early-stage merchants, and data analysts, Ecomlytics turns fragmented catalog, order, and customer records into real-time financial KPIs, unit economics, customer lifetime value (CLV), RFM segmentation clusters, event-driven purchase funnels, and monthly acquisition cohort retention heatmaps.

Live Production URL: **[https://ecomlytics.onrender.com/](https://ecomlytics.onrender.com/)**  
Source Repository: **[https://github.com/Gowtham-YK/Ecomlytics](https://github.com/Gowtham-YK/Ecomlytics)**

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Key Features](#-key-features)
- [Repository Structure](#-repository-structure)
- [Data Ingestion & CSV Format Specifications](#-data-ingestion--csv-format-specifications)
- [Budding Business Demo Datasets (45 Stores)](#-budding-business-demo-datasets-45-stores)
- [Google Analytics 4 (GA4) Telemetry Architecture](#-google-analytics-4-ga4-telemetry-architecture)
- [Dashboard Modules](#-dashboard-modules)
- [REST API Reference](#-rest-api-reference)
- [Local Setup & Development Guide](#-local-setup--development-guide)
- [Automated Testing](#-automated-testing)
- [Production Deployment & Persistence Notes](#-production-deployment--persistence-notes)

---

## 🏛️ Architectural Overview

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND CLIENT LAYER                                 │
│  Vanilla HTML5 / Modern CSS Design System / JavaScript (ES6+ Asynchronous API)  │
│                                                                                  │
│   Overview    Sales Analytics   Products & Margins   Customers RFM   Cohorts     │
│   [/]         [/pages/sales]    [/pages/products]    [/pages/cust]   [/retention]│
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ HTTP Fetch + Credentials (Session Cookie)
                                         │ + Client GA4 Telemetry (gtag.js)
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                             FASTAPI BACKEND CORE                                 │
│                                                                                  │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────┐ │
│  │   Auth & Security      │  │ Analytics Engine       │  │ Ingestion Engine   │ │
│  │  - PBKDF2-SHA256 Hash  │  │  - KPI Aggregations    │  │  - RFC CSV Parser  │ │
│  │  - HMAC Session Tokens │  │  - RFM Segmentation    │  │  - Header Aliasing │ │
│  │  - Workspace Scoping   │  │  - Cohort Matrix Engine│  │  - Idempotency Gate│ │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────┘ │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │ Connection Manager (PRAGMA foreign_keys = ON)
┌────────────────────────────────────────▼─────────────────────────────────────────┐
│                          PERSISTENT RELATIONAL STORE                             │
│                    SQLite with WAL Mode (PostgreSQL compatible)                  │
│                                                                                  │
│   workspaces ──< workspace_members >── users                                     │
│   workspaces ──< products (SKUs, costs, pricing)                                 │
│   workspaces ──< customers (profiles, cities, emails)                            │
│   workspaces ──< orders (transactions, line items, revenue, delivery status)     │
│   workspaces ──< import_jobs (file audit records, row counts, error tracking)    │
│   workspaces ──< product_events (telemetry, funnel step timestamps, properties)  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

1. **Persistent Authentication & Multi-Tenancy:**
   * Server-side account registration, PBKDF2-HMAC-SHA256 password hashing (100,000 rounds), and secure HttpOnly signed session cookies.
   * Multi-tenant boundary isolation: every order, customer, product, import job, and telemetry event is scoped by `workspace_id`.
2. **Honest Metrics & Zero Fabrication:**
   * Zero fabricated numbers or mock trends on authenticated workspaces.
   * Empty (`no_data`) and `insufficient_data` states are handled transparently, giving store owners an honest audit of their operations.
3. **Validated CSV Ingestion & Idempotency:**
   * Fast drag-and-drop CSV importer for orders, products, and customer directories.
   * Header normalization, multi-format date parsing (`YYYY-MM-DD`, `DD/MM/YYYY`, ISO-8601), and external ID duplicate skipping to prevent metric inflation.
4. **Customer Acquisition Cohorts & Retention Matrix:**
   * Monthly customer acquisition cohorts ($M_0, M_1, M_2, \dots$) derived strictly from real customer order dates.
   * Heatmap table displaying retention percentages across dynamic monthly time windows.
5. **Event-Driven Funnel Conversion Analysis:**
   * Multi-stage e-commerce funnel with chronological event verification, conversion windows, step conversion rates, and drop-off analysis.
6. **Automated AI Business Insights:**
   * Evidence-backed opportunity identification (Average Order Value optimization, basket sizing, return rate warnings for defective inventory, and top SKU revenue drivers).
7. **Google Analytics 4 (GA4) Standard Telemetry:**
   * Complete client-side instrumentation of official GA4 recommended e-commerce events (`view_item`, `add_to_cart`, `begin_checkout`, `purchase`, `search`, `login`, `sign_up`).
   * Zero PII transmission policy with idempotent transaction protection against page refresh duplication.

---

## 🛠️ Repository Structure

```text
Ecomlytics/
├── analytics/                      # Central analytics and calculations engine
│   ├── cohorts.py                  # Customer acquisition cohort retention matrix ($M_0 \dots M_k$)
│   ├── funnel.py                   # Event-driven funnel progression & drop-off analysis
│   ├── metrics.py                  # Baseline e-commerce metric definitions
│   └── service.py                  # Multi-tenant workspace SQL aggregations
├── auth/                           # Security and authentication framework
│   ├── dependencies.py             # FastAPI dependency injection (get_current_user, get_current_workspace)
│   ├── security.py                 # PBKDF2-SHA256 hashing & signed HMAC tokens
│   └── service.py                  # User registration, authentication, workspace provisioning
├── database/                       # Relational storage and schema
│   ├── connection.py               # SQLite connection manager with WAL mode & foreign keys
│   └── schema.sql                  # Multi-tenant schema with 7 relational tables & indexes
├── docs/                           # Architectural and engineering specifications
│   ├── analytics-platform-evaluation.md
│   ├── architecture-proposal.md
│   ├── cohort-analysis.md
│   ├── current-state-audit.md
│   ├── data-lineage-and-metric-inventory.md
│   ├── deployment-render.md
│   ├── funnel-analysis.md
│   ├── implementation-plan.md
│   └── metric-definitions.md
├── frontend/                       # Client web application
│   ├── css/style.css               # Design system, cards, tables, heatmaps, modal UI
│   ├── js/app.js                   # Authenticated API client, routing, dynamic charts, GA4 telemetry
│   ├── pages/                      # Application sub-pages
│   │   ├── customers.html          # RFM Customer Intelligence
│   │   ├── data-sources.html       # CSV Importer and Data Source status
│   │   ├── insights.html           # Automated Business Insights
│   │   ├── products.html           # Product Catalog, margins & GA4 test modal
│   │   ├── retention.html          # Retention cohorts & funnel simulator
│   │   ├── sales.html              # Sales trends and revenue graphs
│   │   └── subscription.html       # Plans & Billing with demo checkout
│   ├── favicon.svg                 # Application favicon
│   ├── index.html                  # Overview Dashboard
│   └── login.html                  # Secure Sign-In & Workspace Creation portal
├── ingestion/                      # Data ingestion and normalization
│   └── importer.py                 # Robust CSV parser, validator, and idempotency logger
├── integrations/                   # External adapters
│   ├── google_analytics.py         # GA4 Data API integration
│   ├── razorpay_client.py          # Razorpay merchant client
│   └── product_analytics.py        # First-party telemetry and PostHog adapter
├── tests/                          # Automated test suite (Pytest)
│   ├── test_analytics_service.py   # Workspace aggregation queries
│   ├── test_api_endpoints.py       # API security, cookies & cross-tenant isolation
│   ├── test_cohorts_and_funnel.py  # Funnel chronological progression & cohort math
│   └── test_importer.py            # CSV parsing, date formats, idempotency
├── app.py                          # FastAPI server application entrypoint
├── config.py                       # Configuration & environment variables
├── generate_45_budding_stores.py   # Demo generator producing 45 budding store datasets
├── generate_datasets.py            # Generic dataset generator
├── build_generic_demo_data.py      # Quick demo data generation script
├── requirements.txt                # Production dependencies
└── README.md                       # Master platform documentation
```

---

## 📥 Data Ingestion & CSV Format Specifications

The CSV importer ([`ingestion/importer.py`](file:///C:/Users/Karna/.gemini/antigravity/scratch/Ecomlytics/ingestion/importer.py)) automatically normalizes headers to `lower_snake_case` and strips formatting symbols (₹, $, commas). You can upload three types of datasets via **Data Sources → Import Store CSV Dataset**:

### 1. Orders Dataset (`orders.csv`)
* **Purpose:** Drives Overview KPIs, Sales Analytics graphs, and Customer Acquisition Cohorts.
* **Canonical Headers:**
  ```csv
  order_id,customer_id,product_id,order_date,quantity,price,discount,revenue,status
  ORD-1001,CUST-001,PROD-01,2026-09-10,1,499,0,499,completed
  ORD-1002,CUST-002,PROD-02,2026-09-15,2,499,50,948,completed
  ORD-1003,CUST-001,PROD-03,2026-10-05,1,799,0,799,completed
  ORD-1004,CUST-003,PROD-01,2026-10-25,1,499,0,499,returned
  ```
* **Supported Aliases:** `date`, `created_at`, `total`, `amount`, `order_total`, `qty`, `sku`.
* **Accepted Statuses:** `completed`, `returned`, `cancelled`.

### 2. Products Dataset (`products.csv`)
* **Purpose:** Drives Product Intelligence table, gross margin calculations, and inventory return rates.
* **Canonical Headers:**
  ```csv
  product_id,product_name,category,price,cost
  PROD-01,Terracotta Coffee Mug 300ml,Mugs,399,140
  PROD-02,Speckled Cereal Bowl,Bowls,499,180
  PROD-03,Minimalist Ceramic Planter 6in,Planters,699,260
  ```
* **Supported Aliases:** `sku`, `name`, `title`, `product_category`, `unit_price`, `unit_cost`.

### 3. Customers Dataset (`customers.csv`)
* **Purpose:** Drives Customer Intelligence and automated RFM segmentation (*Champions, Loyal, At Risk, Prospects*).
* **Canonical Headers:**
  ```csv
  customer_id,customer_name,email,city
  CUST-001,Priya Sharma,priya.sharma@example.com,Bengaluru
  CUST-002,Aditya Mehta,aditya.mehta@example.com,Mumbai
  CUST-003,Rohan Verma,rohan.verma@example.com,Delhi
  ```
* **Supported Aliases:** `id`, `name`, `full_name`, `location`.

---

## 🛍️ Budding Business Demo Datasets (45 Stores)

To provide realistic demonstration data for academic and classroom presentations, the platform includes a dedicated dataset generator: [`generate_45_budding_stores.py`](file:///C:/Users/Karna/.gemini/antigravity/scratch/Ecomlytics/generate_45_budding_stores.py).

### Dataset Characteristics:
* **Modest, Realistic Scale:** 22 to 45 orders, 12 to 25 customers, 5 to 7 products, with total store revenues between **₹12,000 and ₹45,000** and Average Order Values (AOV) of **₹400 to ₹1,500**.
* **Date Range:** August 1, 2026 to October 31, 2026, ensuring period deltas and multi-month cohort tables ($M_0, M_1, M_2$) populate with authentic retention rates.
* **Integrity Guarantee:** Foreign keys across `customer_id` and `product_id` match across all three CSV files with 0 rejected rows.

### To Generate or Regenerate the ZIP Archive:
```powershell
python generate_45_budding_stores.py
```
This generates `Ecomlytics_45_Budding_Businesses_CSVs.zip` containing:
* `orders_only_csv/`: 45 individual orders CSV files (e.g. `store_01_auric_clay_orders.csv` to `store_45_urban_botanist_orders.csv`).
* `products_only_csv/`: 45 product catalogs.
* `customers_only_csv/`: 45 customer directories.
* `store_packages/`: 45 subfolders containing synchronized `orders.csv`, `products.csv`, and `customers.csv`.
* `ACCOUNTS_AND_STORES_CATALOG.csv`: Master spreadsheet index summarizing every store's metrics.

---

## 📊 Google Analytics 4 (GA4) Telemetry Architecture

Ecomlytics is configured with Measurement ID **`G-KYK82K8M9J`**. All frontend pages contain the Google Tag (`gtag.js`) snippet.

### Standard E-Commerce Event Implementation:

```text
Visitor Action                 Client Interaction Point               Dispatched GA4 Event
─────────────────────────────────────────────────────────────────────────────────────────────
Create Account            →    frontend/login.html               →    sign_up { method: 'email' }
Sign In                   →    frontend/login.html               →    login { method: 'email' }
Search Catalog            →    frontend/pages/products.html      →    search { search_term: ... }
Inspect Product Details   →    frontend/pages/products.html      →    view_item { items: [...] }
Add Product to Cart       →    Product Detail Modal              →    add_to_cart { items: [...] }
Initiate Checkout         →    Product Modal / Subscription Page →    begin_checkout { items: [...] }
Complete Transaction      →    Confirmed Payment Callback        →    purchase { transaction_id, items }
```

### Telemetry Safety Rules:
1. **Zero Personally Identifiable Information (PII):** No email addresses, personal names, phone numbers, or passwords are sent to GA4.
2. **Idempotent Purchase Tracking:** Every completed purchase generates a unique `transaction_id`. Before firing the `purchase` event, the client checks `sessionStorage` (`ga4_purchased_<txnId>`) to guarantee the event cannot fire repeatedly on page refreshes.
3. **Live Testing in GA4 Realtime / DebugView:**
   * Open the **Products** page (`/pages/products.html`), search for a product, and click **Inspect & Buy** to trigger `view_item`, `add_to_cart`, `begin_checkout`, and `purchase`.
   * Open the **Retention & Funnel** page (`/pages/retention.html`) and click **"Simulate Test Event Stream"** to dispatch the entire event chain simultaneously into the local store and GA4 telemetry.

---

## 🖥️ Dashboard Modules

| Module | Route | Key Metrics & Visualizations |
|---|---|---|
| **Overview Dashboard** | `/index.html` | Completed Orders, Gross Revenue, AOV, Delivered Units, Repeat Customer %, Return Rate %, Gross Profit, and Period Comparison deltas. |
| **Sales Analytics** | `/pages/sales.html` | Chronological daily sales trend, daily revenue volume, and completed units. |
| **Product Intelligence** | `/pages/products.html` | SKU ranking by revenue contribution, units sold, unit profit margin %, return rate warning indicators, and interactive GA4 telemetry test modals. |
| **Customer Intelligence** | `/pages/customers.html` | Automated RFM Segmentation: *Champions, Loyal Customers, Potential Loyalists, At Risk, One-Time Buyers, Prospects*. |
| **Retention & Funnel** | `/pages/retention.html` | Event-driven conversion funnel with drop-off percentages alongside monthly customer acquisition retention matrices ($M_0, M_1, M_2, \dots$). |
| **Business Insights** | `/pages/insights.html` | Automated AI decision engine surfacing basket size recommendations, stockout warnings, and elevated return rate alerts. |
| **Data Sources** | `/pages/data-sources.html` | Drag-and-drop CSV importer, import job history, and live synchronization health checks. |
| **Plans & Billing** | `/pages/subscription.html` | Tier management (Free vs. Pro Pack) with end-to-end checkout simulation. |

---

## 🌐 REST API Reference

All protected endpoints require an authenticated session cookie (`ecomlytics_session`) or Bearer token header (`Authorization: Bearer <token>`).

### Authentication & Account
* `POST /api/auth/register` — Register a new account, hash password with PBKDF2, provision workspace, and receive session cookie.
* `POST /api/auth/login` — Authenticate credentials and receive session cookie.
* `POST /api/auth/logout` — Invalidate session and clear session cookie.
* `GET /api/auth/me` — Fetch active user profile and authorized workspaces.

### Workspace & Data Ingestion
* `GET /api/workspaces/current` — Details of the active workspace.
* `GET /api/data-sources` — Connection state of CSV datasets, GA4, and PostHog adapters.
* `POST /api/imports` — Idempotent CSV ingestion (`orders`, `products`, or `customers`).
* `GET /api/imports` — History of import jobs, processed row counts, and skipped duplicates.

### Analytics (Workspace-Scoped)
* `GET /api/overview?days=30` — Overview KPI metrics, AOV, profit, and windowed period deltas.
* `GET /api/sales` — Daily sales trends and revenue volumes.
* `GET /api/products` — Product catalog ranked by revenue, units sold, and margins.
* `GET /api/customers/segments` — RFM customer segment distribution.
* `GET /api/funnels` — Chronologically ordered event funnel conversion and drop-offs.
* `GET /api/cohorts` — Monthly customer acquisition cohort retention matrix.
* `GET /api/insights` — Evidence-backed business recommendations.
* `POST /api/events` — Capture first-party product or e-commerce behavioral events.

### Platform Health
* `GET /api/health` — Public health probe returning service status and database state.

---

## 🏃 Local Setup & Development Guide

### Prerequisites
* Python 3.11+
* Git
* SQLite3 (pre-installed on most systems)

### 1. Clone & Set Up Virtual Environment
```powershell
# Clone repository
git clone https://github.com/Gowtham-YK/Ecomlytics.git
cd Ecomlytics

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # Windows PowerShell
# source venv/bin/activate   # macOS / Linux
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
pip install pytest
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Key configuration parameters:
```env
APP_ENV=development
SECRET_KEY=ecomlytics_secure_development_secret_key_32_bytes
GA4_MEASUREMENT_ID=G-KYK82K8M9J
DATABASE_PATH=data/ecomlytics.db
```

### 4. Run the Application
```powershell
python app.py
```
Open **`http://127.0.0.1:8000/`** in your browser.

---

## 🧪 Automated Testing

The automated test suite covers authentication security, cross-tenant workspace isolation, database transactions, CSV importer idempotency, funnel chronological ordering, cohort retention math, and API endpoint contracts:

```powershell
python -m pytest tests/
```

Test suite breakdown:
* `tests/test_analytics_service.py` — Workspace aggregation queries and empty-state handling.
* `tests/test_api_endpoints.py` — Route protection, cookie auth, and cross-workspace isolation tests.
* `tests/test_cohorts_and_funnel.py` — Windowed progression, step conversion rates, and retention calculations.
* `tests/test_importer.py` — Idempotency verification and header normalization.

---

## ☁️ Production Deployment & Persistence Notes

Ecomlytics is deployed on **Render** as a Python Web Service.

### Deployment Parameters:
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
* **Health Check Path:** `/api/health`

### ⚠️ Storage Persistence on Render Free Tier vs. Local Server:
* **Local Server (`python app.py`):** The SQLite database resides at `data/ecomlytics.db` on your local drive. All imported orders, products, customers, and user accounts persist permanently across restarts and reboots.
* **Render Free Web Service (`ecomlytics.onrender.com`):** Render's free tier uses an **ephemeral disk**. If the container goes to sleep after 15 minutes of inactivity or restarts, files written to local storage are reset. For permanent cloud persistence on Render, attach a persistent Render Disk or configure a managed PostgreSQL instance via `DATABASE_URL`.

---

## 📄 License & Attribution

Developed as an e-commerce intelligence and product analytics platform.  
Copyright © 2026 Ecomlytics. All rights reserved.
