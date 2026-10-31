# Target Architecture Proposal (Stage C)

**Document Reference:** Section 3 of Ecomlytics Master Implementation Specification  
**Project:** Ecomlytics  
**Date:** October 31, 2026  

---

## 1. Architectural Principles

1. **Strict Multi-Tenancy & Isolation:** Every business record, metric computation, import job, and event log is explicitly partitioned by `workspace_id`. Cross-workspace queries are impossible by construction.
2. **Persistence Guarantee:** Replace ephemeral CSV dependency with relational database persistence (SQLite for development & test suites, PostgreSQL via `DATABASE_URL` on Render for production).
3. **No Unauthenticated Business Routes:** All analytics endpoints require a verified user identity and confirmed workspace membership.
4. **Honest Metric Semantics:** Missing data yields explicit empty states (`no_data`, `insufficient_data`) rather than fabricated fallback percentages or fake zeros.
5. **Separation of Concerns:** Clean layered architecture with minimal disruption to the existing FastAPI structure:
   - `database/`: Schema, connection management, repository queries.
   - `auth/`: Security, password hashing (Argon2 / PBKDF2), session tokens, FastAPI dependencies.
   - `ingestion/`: CSV validation, normalization, idempotency, import job tracking.
   - `analytics/`: Central calculation engine parameterized by `workspace_id`.
   - `integrations/`: GA4, Razorpay, and product event analytics adapters.
   - `frontend/`: UI components with state management, loading skeletons, and real empty states.

---

## 2. Logical Data Model

```text
users (id, email, password_hash, display_name, created_at)
  └── workspace_members (workspace_id, user_id, role, created_at)
        └── workspaces (id, name, created_at, default_currency)
              ├── customers (id, workspace_id, external_id, name, email, city, created_at)
              ├── products (id, workspace_id, external_id, name, category, price, cost)
              ├── orders (id, workspace_id, external_id, customer_id, product_id, order_date, quantity, revenue, status)
              ├── import_jobs (id, workspace_id, dataset_type, status, processed, imported, skipped, errors, created_at)
              ├── data_sources (id, workspace_id, source_type, status, last_synced, metadata)
              └── product_events (id, workspace_id, user_id, session_id, event_name, occurred_at, properties)
```

---

## 3. Security & Session Flow

1. **Password Hashing:** Passwords are never stored in plaintext. They are hashed using `argon2id` / `cryptography` / PBKDF2 with salt.
2. **Authentication Flow:**
   - Client sends credentials to `POST /api/auth/login`.
   - Server validates password against `password_hash`.
   - Server issues a signed token stored in a secure cookie (`HttpOnly; Secure; SameSite=Lax`) or bearer token header.
   - Current user is retrieved via `GET /api/auth/me`.
3. **Authorization Flow:**
   - FastAPI dependency `get_current_user` extracts and verifies the session token.
   - Dependency `get_current_workspace` verifies user membership in `workspace_members`.
   - Every database query is scoped: `WHERE workspace_id = :workspace_id`.
   - Cross-workspace access attempts immediately return HTTP 403 Forbidden.

---

## 4. Analytics & Event Ingestion Design

- **Orders & Sales:** Aggregated directly from database orders scoped to the active workspace.
- **Funnel Analysis:** 
  - Dual funnel support:
    1. **Ecomlytics Onboarding Funnel:** First-party product events (`page_view` $\rightarrow$ `signup_completed` $\rightarrow$ `import_started` $\rightarrow$ `import_completed` $\rightarrow$ `dashboard_viewed`).
    2. **Store Purchase Funnel:** Recorded e-commerce events (`product_view` $\rightarrow$ `add_to_cart` $\rightarrow$ `checkout_started` $\rightarrow$ `purchase_completed`).
  - Strict step ordering, configurable conversion windows, unique user deduplication, and honest drop-off rates.
- **Cohort Retention Analysis:**
  - Group customers by first purchase month/week (Acquisition Cohort $M_0$).
  - Track repeat purchasing behavior across subsequent periods ($M_1, M_2, M_3, \dots$).
  - Calculate retention rate matrix with cell details (numerator = retained count, denominator = cohort size).
  - Explicitly flag incomplete current periods.

---

## 5. Technology Stack Decisions

- **Backend Framework:** FastAPI (existing).
- **Database Engine:** Python `sqlite3` for zero-setup local dev/testing with standard SQL schema + seamless PostgreSQL compatibility via standard SQL query design.
- **Security Primitives:** Standard Python `secrets` and `argon2-cffi` / `hashlib.pbkdf2_hmac` for constant-time comparison and secure hashing.
- **Frontend:** Vanilla HTML/CSS/JS with zero unnecessary heavy dependencies, ensuring fast rendering, rich styling, and zero build tool fragility.
