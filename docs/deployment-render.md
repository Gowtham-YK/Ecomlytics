# Ecomlytics — Render Deployment and Operations Guide

**Application:** Ecomlytics  
**Platform:** Render Web Service  
**Date:** October 31, 2026  
**Document Reference:** Section 17 of Ecomlytics Master Implementation Specification  

---

## 1. Render Service Configuration

### Service Specification
- **Service Type:** Web Service
- **Runtime:** Python 3.11+
- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```bash
  uvicorn app:app --host 0.0.0.0 --port $PORT
  ```
- **Health Check Path:** `/api/health`

### Environment Variables
| Variable Name | Required | Purpose | Safe Example Placeholder |
|---|---|---|---|
| `SESSION_SECRET` | **Yes** (Production) | Cryptographic secret for signing session tokens and cookies | `<random-64-character-hex>` |
| `DATABASE_PATH` | No | SQLite file location (defaults to `data/ecomlytics.db`) | `/data/ecomlytics.db` |
| `POSTHOG_API_KEY` | Optional | PostHog project API key for external product behavioral events | `phc_...` |
| `POSTHOG_HOST` | Optional | PostHog host | `https://us.i.posthog.com` |
| `GOOGLE_CLIENT_ID` | Optional | GA4 OAuth Client ID | `<client-id>.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Optional | GA4 OAuth Client Secret | `<secret>` |
| `GOOGLE_REDIRECT_URI` | Optional | GA4 OAuth Redirect Callback | `https://ecomlytics.onrender.com/api/data-sources/google/callback` |
| `RAZORPAY_KEY_ID` | Optional | Razorpay Merchant Key ID | `rzp_test_...` or `rzp_live_...` |
| `RAZORPAY_KEY_SECRET` | Optional | Razorpay Merchant Key Secret | `<secret>` |

---

## 2. Post-Deployment Smoke Test Checklist

Execute these checks immediately after any release:
1. **Public Health Route:**
   - Verify `GET https://ecomlytics.onrender.com/api/health` returns HTTP 200 with `status: "running"` and `database: "healthy"`.
2. **Authentication Protection:**
   - Verify `GET https://ecomlytics.onrender.com/api/overview` returns HTTP 401 Unauthorized for anonymous callers.
3. **Registration & Isolation:**
   - Register a test account. Verify workspace provisioning and session cookie reception.
   - Verify overview displays honest `no_data` state for a fresh account.
4. **Data Import & Calculations:**
   - Import test CSV. Verify import counts and that calculations match expected totals.
5. **Session Invalidation:**
   - Call sign-out. Verify session cookie is deleted and subsequent requests are rejected.
