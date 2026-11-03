# Mixpanel, PostHog and Amplitude Integration

Ecomlytics keeps its first-party `product_events` table as the canonical event store.
The authenticated `POST /api/events` endpoint writes the event locally and then
best-effort forwards the same event to each configured provider. Vendor failures
never interrupt Ecomlytics requests. Provider credentials are server-side only.

## Render environment variables

Set only the providers you want to enable:

| Provider | Render environment variable | Where to find it |
|---|---|---|
| Mixpanel | `MIXPANEL_PROJECT_TOKEN` | Project Settings → Project Details → Project Token |
| PostHog | `POSTHOG_API_KEY` | Project Settings → Project API Key |
| PostHog host | `POSTHOG_HOST` | `https://us.i.posthog.com` for US cloud; use your EU host if applicable |
| Amplitude | `AMPLITUDE_API_KEY` | Settings → Projects → General → API Key |
| Amplitude region | `AMPLITUDE_INGEST_URL` | US: `https://api2.amplitude.com/2/httpapi`; EU: `https://api.eu.amplitude.com/2/httpapi` |

Do not put provider secrets in HTML, JavaScript, Git, or the public repository.
Do not set Mixpanel service-account secrets or Amplitude secret keys here; this
integration uses the project token/API key required for event ingestion.

## Events currently instrumented

- `page_viewed`, `dashboard_viewed`
- `product_view`, `add_to_cart`, `checkout_started`, `purchase_completed` (the built-in product purchase action is a demo/test interaction and is marked `is_demo: true`)
- `login_completed`, `signup_completed`, `logout_completed`
- `funnel_viewed`, `cohort_report_viewed`, `insights_page_viewed`
- `data_sources_viewed`
- `csv_import_started`, `csv_import_completed`, `csv_import_failed`
- `subscription_page_viewed`, `upgrade_clicked`, `plan_selected`
- `demo_payment_started`, `demo_payment_completed`, `demo_payment_failed`

Event properties are intentionally allowlisted in `integrations/product_analytics.py`.
Email addresses, names, passwords, raw customer/order rows, and payment credentials
are not forwarded. The demo payment events include `is_demo: true` and must not be
reported as real revenue.

## Verify the integration

1. Add the desired provider keys to Render → Ecomlytics service → Environment.
2. Redeploy the service.
3. Sign in and navigate through Overview, Retention, Insights, Data Sources and
   Plans & Billing.
4. Import a small test CSV and use the demo checkout if desired.
5. Open each provider's Live Events / Events view and confirm the events appear.
6. Open Ecomlytics → Data Sources to see which providers are configured.

If a provider is `not_configured`, the local first-party event store continues to
work. A `connected` status means credentials are present; it does not guarantee
that the provider has accepted a test event, so verify in that provider's live
event stream.

## Privacy and operations

Provide an appropriate privacy notice and consent/opt-out control for your users.
Review applicable privacy laws and each provider's data-processing terms before
production use. Keep all API keys in Render environment variables.
