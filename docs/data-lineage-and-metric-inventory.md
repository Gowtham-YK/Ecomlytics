# Data Lineage and Metric Inventory (Stage B)

**Document Reference:** Section 2.2 of Ecomlytics Master Implementation Specification  
**Application:** Ecomlytics  
**Date:** October 31, 2026  

---

## 1. Lineage Classification Schema

Every metric displayed or returned by the system is classified into one of five categories:
1. **Hardcoded presentation placeholder:** Constant literal value embedded in frontend HTML or JS without computation.
2. **Sample fixture:** Static mock data from bundled fixture files (`data/*.csv`) not tied to user workspaces.
3. **Calculated from imported/persisted records:** Dynamically aggregated from persistent database records belonging strictly to the authenticated workspace.
4. **Returned by an external source:** Synced from third-party APIs (e.g. GA4, Razorpay, PostHog/Mixpanel).
5. **Unknown origin:** Requires further investigation.

---

## 2. Metric Inventory & Lineage Table

| Metric Name | Display Location | Current Calculation Origin | Classification | Target Implementation Plan |
|---|---|---|---|---|
| **Total Revenue** | Overview KPI, Sales Header | `sum(float(o['revenue']))` for `status == 'completed'` in `orders.csv` | **Sample Fixture** (CSV) | Calculate dynamically via SQL `SUM(revenue)` from `orders` where `workspace_id = :ws_id AND status = 'completed'` |
| **Order Count** | Overview KPI, Sales KPI | `len(completed_orders)` in `orders.csv` | **Sample Fixture** (CSV) | SQL `COUNT(*)` from `orders` where `workspace_id = :ws_id AND status = 'completed'` |
| **Average Order Value (AOV)** | Overview KPI, Sales KPI | `revenue / order_count` if `order_count > 0` else 0 | **Sample Fixture** (CSV) | SQL aggregate `revenue / count` or `NULL` if count = 0 |
| **Units Sold** | Overview KPI | `sum(int(o['quantity']))` in `orders.csv` | **Sample Fixture** (CSV) | SQL `SUM(quantity)` from workspace `orders` |
| **Repeat Customer Rate** | Overview KPI | Customers with `orders > 1` divided by total customers in `customers.csv` | **Sample Fixture** (CSV) | Calculate from workspace customer purchase history |
| **Gross Profit** | Overview KPI | `sum((price - cost) * units_sold)` across `products.csv` | **Sample Fixture** (CSV) | Join `orders` with `products` or compute from order items where price & cost exist |
| **30-Day Period Comparison Deltas** | Overview KPI Badges | `_period_stats()` anchored to max date in `orders.csv` vs prior 30d | **Sample Fixture** (CSV) | Date-window SQL comparison against workspace orders with honest `insufficient_data` handling |
| **Product Views** | Retention/Funnel Step 1 | `sum(p['views'])` in `products.csv` | **Sample Fixture** (Static Column) | **Replace:** Derive from first-party product events (`page_view` / `product_view`) logged per user session |
| **Add to Cart** | Retention/Funnel Step 2 | `sum(p['add_to_cart'])` in `products.csv` | **Sample Fixture** (Static Column) | **Replace:** Derive from recorded `add_to_cart` events |
| **Checkout Started** | Retention/Funnel Step 3 | `sum(p['checkout'])` in `products.csv` | **Sample Fixture** (Static Column) | **Replace:** Derive from recorded `checkout_started` events |
| **Purchase Completed** | Retention/Funnel Step 4 | `sum(p['units_sold'])` in `products.csv` | **Sample Fixture** (Static Column) | **Replace:** Derive from recorded `purchase_completed` events or completed orders |
| **Cohort Retention** | Retention Page | Customers with $\ge 1, \ge 2, \ge 3, \ge 4$ orders | **Sample Fixture** (Arbitrary thresholds) | **Replace:** Standard weekly/monthly customer acquisition cohorts ($M_0, M_1, M_2, \dots$) |
| **Customer Segments (RFM)** | Customer Intelligence | `determine_segment()` in `analytics/metrics.py` based on `total_spend` and `last_order_days` | **Sample Fixture** (CSV) | Calculate dynamically per workspace from customer order history |
| **Automated Insights** | Insights Page | `insights/engine.py` rule-based analysis over CSV metrics | **Sample Fixture** (CSV) | Run evidence engine over workspace database metrics |
| **Subscription Plans / Pricing** | Subscription Page | Hardcoded in `app.py::subscription_plans` | **Hardcoded Placeholder** | Maintain as transparent presentation pricing plans |
| **Dummy Payments Table** | Subscription Page | Randomly generated via `razorpay_client.generate_dummy_payments()` | **Sample Fixture** (In-memory mock) | Isolate exclusively to demo/testing view |

---

## 3. Data Flow Diagram: Current vs. Target

### Current Data Flow (Vulnerable & Non-Isolated)
```text
[ Browser / Client ] ──(Unauthenticated GET)──> [ FastAPI app.py ] ──> [ Shared CSV files data/*.csv ]
        │
  (localStorage:
   plaintext password)
```

### Target Data Flow (Secure & Multi-Tenant)
```text
[ Browser Client ]
       │
       ▼ (HTTPS + HttpOnly Session Cookie / Bearer Token)
[ FastAPI Authentication Layer ] ──> Validate Session & Identity
       │
       ▼
[ Workspace Authorization Layer ] ──> Validate Workspace Membership
       │
       ▼
[ Service / Analytics Layer ] ──> Parametric Workspace Queries
       │
       ▼
[ Persistent Database (SQLite / PostgreSQL) ]
  ├── users
  ├── workspaces & workspace_members
  ├── customers (scoped by workspace_id)
  ├── products (scoped by workspace_id)
  ├── orders & order_items (scoped by workspace_id)
  ├── data_sources & import_jobs (scoped by workspace_id)
  └── product_events (scoped by workspace_id)
```
