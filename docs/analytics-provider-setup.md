# Ecomlytics analytics provider setup

## Google Analytics 4
- `GA4_MEASUREMENT_ID=G-N4DCRNR7VV`
- GA4 browser events are sent with the Google tag on Ecomlytics pages.
- This Measurement ID enables event collection. It does not by itself enable GA4 Data API reporting or OAuth access.

## Mixpanel
- `MIXPANEL_PROJECT_TOKEN` — Mixpanel project token
- `MIXPANEL_HOST` — `https://api-eu.mixpanel.com` for EU projects, or `https://api.mixpanel.com` for US projects.

## PostHog
- `POSTHOG_PROJECT_TOKEN` — PostHog project API key
- `POSTHOG_HOST` — `https://us.i.posthog.com` for US projects (use your region's ingestion host if different).

## Amplitude
- `AMPLITUDE_API_KEY` — Amplitude project API key
- `AMPLITUDE_INGEST_URL` — `https://api2.amplitude.com/2/httpapi` for US projects; use Amplitude's EU endpoint if your project is in the EU.

## Event flow
- GA4 receives browser events through `gtag`.
- Authenticated product events are stored in Ecomlytics first-party SQLite storage.
- The backend independently forwards each event to configured Mixpanel, PostHog, and Amplitude providers.
- Provider credentials stay server-side. Configure them as Render environment variables, never in frontend JavaScript.
- A provider marked `configured` means its credential is present; verify actual delivery in that provider's Live Events/Debugger view after deployment.
