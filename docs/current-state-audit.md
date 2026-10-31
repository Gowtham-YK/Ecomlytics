# Ecomlytics — Current-State Audit (Stage A)

**Date of Audit:** October 31, 2026  
**Auditor:** AI Lead Software & Security Engineer  
**Branch:** `feature/user-specific-analytics` (branched from `main` commit `7490dc3`)  
**Repository:** `https://github.com/Gowtham-YK/Ecomlytics`  
**Production URL:** `https://ecomlytics.onrender.com/`  

---

## 1. Executive Summary

Ecomlytics is a FastAPI-based e-commerce analytics web application. In its current baseline state:
1. **Authentication is client-side only and insecure:** Login and registration logic reside entirely in browser JavaScript (`frontend/login.html`) utilizing `localStorage` to save accounts with plaintext passwords. There are zero backend authentication routes (`/api/auth/*`), zero session cookies or tokens, and no server-side identity verification.
2. **Zero Workspace Isolation & Multi-Tenancy:** All analytics endpoints (`/api/overview`, `/api/products`, `/api/customers/segments`, `/api/funnel`, `/api/insights`) are unauthenticated public GET requests that read shared CSV files from `data/*.csv`. Any user logging in sees the exact same global dataset regardless of identity.
3. **Storage is Ephemeral/CSV-Only:** Although `database/schema.sql` defines 3 skeletal tables (`products`, `customers`, `orders`), no database connection, ORM, or SQL driver is active. The application has no persistent database.
4. **Funnel & Cohort Semantics are Compromised:** 
   - `funnel()` does not compute a user event journey; it simply sums column values (`views`, `add_to_cart`, `checkout`, `units_sold`) from `products.csv`.
   - `retention()` merely counts customers with order count thresholds ($\ge 1, \ge 2, \ge 3, \ge 4$), rather than cohort acquisition periods and multi-period retention matrices.
5. **Codebase Redundancy:** A nested folder `Ecomlytics_Complete_Project/` duplicates the entire project, causing `pytest` import collisions unless scoped directly to `tests/`. Furthermore, `backend/main.py` is an unmounted, older duplicate of `app.py`.

---

## 2. Environment & Dependency Inventory

### Runtime & System
- **Python Version:** 3.11.9
- **Operating System:** Windows 10/11
- **Installed Key Packages:**
  - `fastapi` (0.136.1), `starlette` (1.0.0), `uvicorn` (0.46.0), `pydantic` (2.13.3)
  - `pandas` (3.0.1), `numpy` (2.4.2)
  - `python-dotenv` (1.2.2)
  - `argon2-cffi` (25.1.0), `cryptography` (50.0.2)
  - `pytest` (9.2.0)
  - `httpx` (0.28.1)

### Test Baseline
- **Command:** `python -m pytest tests/`
- **Result:** 5 passed in 0.06s.
  - `test_overview_matches_dataset`: PASS
  - `test_products_row_count_matches_csv`: PASS
  - `test_zero_denominator_never_fabricated`: PASS
  - `test_period_comparison_shape`: PASS
  - `test_period_comparison_handles_no_data`: PASS
- **Baseline Test Coverage Gaps:**
  - Zero authentication tests.
  - Zero workspace isolation tests.
  - Zero CSV import/validation tests.
  - Zero real funnel event tests.
  - Zero cohort retention tests.
  - Zero security / authorization tests.

---

## 3. Feature Inventory & Implementation Status

| Route / Page | API Endpoint | Current Data Source | Auth Enforced? | Workspace Scoped? | State Handling (Empty/Error) | Decision |
|---|---|---|---|---|---|---|
| `/login.html` | None (Client `localStorage`) | Browser `localStorage` | ❌ None (Client only) | ❌ No | Inadequate (stores plaintext password in client) | **Replace** with real backend auth (`/api/auth/*`), secure cookies/tokens, password hashing |
| `/index.html` (Overview) | `GET /api/overview` | `data/orders.csv`, `customers.csv`, `products.csv` | ❌ No | ❌ No (global CSV) | Fixed fallback text on error | **Refactor** to workspace-scoped database service |
| `/pages/sales.html` | None dedicated (uses `/api/overview` & CSV) | Global CSV | ❌ No | ❌ No | Basic | **Refactor** to query workspace database orders |
| `/pages/products.html` | `GET /api/products` | `data/products.csv` | ❌ No | ❌ No | Basic | **Refactor** to query workspace products |
| `/pages/customers.html` | `GET /api/customers/segments` | `data/customers.csv` | ❌ No | ❌ No | Basic | **Refactor** to query workspace customers |
| `/pages/retention.html` | `GET /api/funnel`, `retention()` in metrics | Global CSV product columns & customer order counts | ❌ No | ❌ No | Incomplete / Not actual cohort table | **Replace** with genuine ordered event funnel & acquisition cohort retention matrix |
| `/pages/insights.html` | `GET /api/insights` | `insights/engine.py` over CSVs | ❌ No | ❌ No | Partial | **Refactor** to derive from workspace database metrics |
| `/pages/data-sources.html` | `GET /api/data-sources` | `integrations/data_sources.py` (checks CSV timestamp + GA4 env) | ❌ No | ❌ No | Decent honest status | **Refactor** to include CSV Upload workflow, import history, and workspace tracking |
| `/pages/subscription.html` | `GET /api/subscription/plans`, `POST /api/subscription/checkout` | Hardcoded plans + simulated token | ❌ No | ❌ No | Demo mode only | **Keep** as optional demo billing, ensure no real charge claim |
| `GET /api/health` | `GET /api/health` | In-memory app status | ❌ No | Public | Returns status: "running" | **Enhance** to report database and system health safely |

---

## 4. Security Audit Findings

1. **CRITICAL - Client-Side Pseudo Authentication:**  
   - Users register and sign in by storing passwords in browser `localStorage`.
   - Any visitor can bypass login by running `localStorage.setItem('ecomlytics_user', JSON.stringify({id: 'usr_1', email: 'admin@admin.com'}))` or simply calling the API endpoints directly via curl/fetch.
2. **CRITICAL - Total Absence of Backend Authorization:**  
   - No route in `app.py` requires credentials or inspects session cookies/headers.
   - All store metrics are publicly accessible without authentication.
3. **HIGH - Data Leakage & Lack of Multi-Tenancy:**  
   - There is no concept of a workspace foreign key. All data is read from a single shared set of CSV files.
4. **HIGH - Wildcard CORS with Credentials:**  
   - `app.py` configures `CORSMiddleware` with `allow_origins=["*"]` and `allow_credentials=True`. Modern browsers block credentialed requests with wildcard origins, and in standard CORS specifications, wildcard origin with credentials is a security risk.

---

## 5. Deployment & Persistence Review (Render)

- **Entrypoint:** `uvicorn app:app`
- **File System:** Render web services run on ephemeral disks. Any CSV file uploaded or modified at runtime will be wiped whenever the container restarts, deploys, or scales.
- **Persistence Target:** A relational database (SQLite for development/testing, PostgreSQL for production on Render) is required to persist users, workspaces, memberships, products, customers, orders, and event records across container lifecycles.
