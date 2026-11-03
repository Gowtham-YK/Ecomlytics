# Analytics Platform Evaluation: Mixpanel vs. PostHog vs. Amplitude (Stage J)

**Document Reference:** Section 11 of Ecomlytics Master Implementation Specification  
**Author:** AI Lead Product Analyst & Software Architect  
**Evaluation Date:** October 31, 2026  
**Verification Method:** Current official documentation and published pricing specifications  

---

## 1. Executive Summary & Recommended Strategy

### Recommended Pattern: Pattern 2 (First-Party Event Store + PostHog Primary Integration)
We recommend **PostHog** as the primary external product analytics platform, coupled with Ecomlytics' internal first-party event store.

**Core Rationale:**
1. **Separation of Concerns:** Business data (orders, customers, revenue) remains exclusively inside Ecomlytics' multi-tenant SQL database. Product behavior (onboarding, feature usage, UI navigation) streams to PostHog.
2. **Generous Free Tier with Zero Credit Card Requirement:** PostHog provides **1,000,000 product events/month**, **5,000 session replays/month**, **1,000,000 feature flag requests**, and **100,000 error tracking exceptions** completely free with no credit card required to start.
3. **Comprehensive Tooling for SaaS:** Unlike Mixpanel (which limits free users to 5 saved reports and disallows saved cohorts) or Amplitude (which has a steeper learning curve and enterprise-gated exports), PostHog provides out-of-the-box funnels, cohort retention, session replay with DOM masking, and feature flags in a single SDK.
4. **Lightweight Integration:** PostHog's JavaScript snippet and Python SDK require zero complex build tooling and integrate cleanly with FastAPI and vanilla HTML/JS.

---

## 2. Comparison Matrix

| Evaluation Criteria | Mixpanel | PostHog (Recommended) | Amplitude |
|---|---|---|---|
| **Free Tier Allowance** | 1,000,000 events / month | 1,000,000 events / month | 2,000,000 events / month |
| **Session Replay Free Tier** | 10,000 replays / month | 5,000 replays / month | 10,000 replays / month |
| **Team Seats (Free)** | Unlimited | Unlimited | Unlimited |
| **Report / Cohort Limits (Free)** | ⚠️ Limited to 5 saved reports; cannot save cohorts | ✅ Unlimited saved reports & cohorts | ✅ Core reports & basic cohorts included |
| **Identity Resolution** | `distinct_id`, `$identify`, `$alias` | `distinct_id`, `identify(id, props)` | `device_id` & `user_id` stitching |
| **SDK Support (Python / JS)** | `mixpanel-browser`, `mixpanel` (Python) | `posthog-js`, `posthog-python` | `@amplitude/analytics-browser`, `amplitude` |
| **Self-Hosting Capability** | ❌ No (Proprietary Cloud only) | ✅ Yes (Open source Docker/K8s) | ❌ No (Proprietary Cloud only) |
| **Feature Flags / Experiments** | 10 active flags; 1k MEU | 1,000,000 flag requests | Gated on higher tiers |
| **Data Retention (Free Plan)** | 1 Year | 1 Year | 1 Year |
| **Credit Card Required to Start?** | No | No | No |
| **Estimated Cost at Scale (10M events)**| ~$240 - $350 / month | ~$350 - $450 / month (usage-tiered)| ~$500+ / month (Plus plan) |

---

## 3. Event Taxonomy & Canonical Schema

Every product event follows a strict allowlisted contract:

```json
{
  "event_name": "string (snake_case)",
  "occurred_at": "ISO 8601 UTC timestamp",
  "user_id": "usr_... (authenticated user) or null",
  "session_id": "sess_... (browser session)",
  "workspace_id": "ws_... (tenant boundary)",
  "properties": {
    "page_path": "/pages/sales.html",
    "dataset_type": "orders",
    "filter_days": 30
  }
}
```

### Core Allowlisted Events
1. `page_viewed` — Triggered when a user navigates to an application view.
2. `signup_started` — Triggered when the user switches to the Create Account tab.
3. `signup_completed` — Triggered upon successful account & workspace creation.
4. `login_completed` — Triggered upon successful authentication.
5. `csv_import_started` — Triggered when a user initiates a dataset upload.
6. `csv_import_completed` — Triggered when the server persists imported rows.
7. `csv_import_failed` — Triggered if an import is rejected.
8. `funnel_viewed` — Triggered when inspecting the funnel analytics tab.
9. `cohort_report_viewed` — Triggered when inspecting retention cohorts.
10. `data_source_connected` — Triggered when a data source or integration connects.

---

## 4. Privacy, Governance & Compliance Rules

1. **No Sensitive PII in Event Properties:** Full passwords, plaintext credit card / payment tokens, customer home addresses, and confidential financial records are strictly prohibited from event properties.
2. **Pseudonymous Identifiers:** Client events use pseudonymous session tokens or opaque user IDs (`usr_...`).
3. **Opt-Out / DNT Support:** The tracking wrapper checks `navigator.doNotTrack` and provides an immediate disable switch via `POSTHOG_ENABLED=false` or client settings.
4. **Server Isolation:** Third-party vendor outages or network blocks (e.g. adblockers) will never block application requests or prevent users from viewing internal analytics.

---

## 5. Integration Architecture Diagram

```text
[ Browser Client ]
       │
       ├── (1) UI Actions ───────> [ PostHog JS SDK (Cloud / Self-Host) ]
       │                                  (Behavioral Analytics & Replays)
       │
       └── (2) Critical Actions ──> [ FastAPI POST /api/events ]
                                          │
                                          ├──> [ Persistent product_events Table ]
                                          │     (First-Party Funnel Engine)
                                          │
                                          └──> [ PostHog Python SDK (Async) ]
                                                (Server-Verified Events)
```

---

## 6. Actions Requiring Explicit User Approval

1. **Production PostHog Project API Key:** Deploying live tracking to Render requires the user to create a free PostHog project and provide `POSTHOG_API_KEY` and `POSTHOG_HOST`. (Until provided, the integration runs in graceful stub mode without errors).
2. **Paid Plan Upgrades:** PostHog will remain strictly within the free tier (up to 1,000,000 monthly events). No paid tier or credit card requirement will be activated without user authorization.
