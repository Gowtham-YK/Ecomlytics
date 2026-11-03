# Product Analytics Integrations

Ecomlytics keeps its first-party `product_events` table as the canonical event store. Each event is persisted locally, then independently forwarded to every configured provider: Mixpanel, PostHog, and Amplitude. A failure at one provider does not stop delivery attempts to the others or interrupt core Ecomlytics workflows.

## Render environment variables

Configure any one, two, or all three providers:

| Provider | Environment variable | Where to find it |
|---|---|---|
| Mixpanel | `MIXPANEL_PROJECT_TOKEN` | Project Settings → Project Details → Project Token |
| PostHog | `POSTHOG_PROJECT_TOKEN` | Project Settings → Project API Key / Project Token |
| PostHog host | `POSTHOG_HOST` | US: `https://us.i.posthog.com`; EU: `https://eu.i.posthog.com` |
| Amplitude | `AMPLITUDE_API_KEY` | Settings → Projects → General → API Key |
| Amplitude region | `AMPLITUDE_INGEST_URL` | US: `https://api2.amplitude.com/2/httpapi`; EU: `https://api.eu.amplitude.com/2/httpapi` |

All credentials must remain in Render environment variables. Do not put them in HTML, JavaScript, Git, or the public repository. The legacy `POSTHOG_API_KEY` variable remains accepted as a fallback for existing deployments.

## Delivery and privacy

- All providers receive the same event name and allowlisted event properties.
- Ecomlytics user database ID is used as the analytics identity, never email.
- The persisted first-party event ID is used as the provider deduplication key where supported.
- Explicit analytics consent remains required.
- Raw customer/order rows, email addresses, names, passwords and payment credentials are excluded.
- Provider statuses mean credentials are configured; they do not prove successful event ingestion. Check each provider's live event stream.

## Current tracking plan

See `posthog-tracking-plan.md` for the status of the 10 onboarding and activation events. The same implemented events are forwarded to each configured provider.
