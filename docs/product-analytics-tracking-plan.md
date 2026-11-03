# Multi-Provider Product Analytics Tracking Implementation

## Provider configuration
- Provider: PostHog.
- Set `POSTHOG_PROJECT_TOKEN` to the **Project API Key / Project Token** from PostHog Project Settings (usually starts with `phc_`).
- Set `POSTHOG_HOST` to `https://us.i.posthog.com` for US Cloud, `https://eu.i.posthog.com` for EU Cloud, or the ingestion host for a self-hosted instance.
- Keep both values in Render environment variables. Never put the project token in frontend JavaScript or commit it.
- The legacy `POSTHOG_API_KEY` environment variable is accepted as a fallback for existing deployments.

## Consent and identity
- Tracking is gated by explicit analytics consent in the Ecomlytics UI and the event API.
- `distinct_id` is the authenticated Ecomlytics database user ID (`users.id`), never email.
- Events are persisted in Ecomlytics first; PostHog forwarding is best-effort and logs delivery failures server-side.
- `$insert_id` uses the persisted first-party event ID to support PostHog duplicate-event deduplication.
- Session ID is sent as `$session_id` when available.
- Only allowlisted, non-sensitive event properties are forwarded.

## Event status

| Event | Status | Implementation notes |
|---|---|---|
| `account_signed_up` | Instrumented | Server-confirmed after account/workspace creation, only when registration consent is true. `plan_tier=free`, `signup_channel=web`, `timestamp_source=server`; unknown company size is omitted. |
| `invitation_accepted` | Blocked | No invitation/member-invite acceptance flow exists in this repository. |
| `integration_connection_started` | Blocked | No external integration OAuth/connect initiation route exists in this repository. |
| `integration_connected_successfully` | Blocked | No verified external integration callback/connection completion flow exists in this repository. |
| `integration_connection_failed` | Blocked | No external integration connection attempt/failure handler exists in this repository. |
| `setup_step_completed` | Instrumented | Emits after a successful first-party CSV import. |
| `first_integration_connected` | Blocked | No supported integration completion flow exists to establish this milestone. |
| `first_dashboard_viewed` | Instrumented | Emits on authenticated overview dashboard load; backend deduplicates per user/workspace. |
| `report_generated` | Blocked | No report-generation or report-delivery workflow exists in the current frontend/backend. |
| `first_analyzed_results_achieved` | Instrumented | Emits when the insights API returns at least one actual insight; backend deduplicates per user/workspace. |

## Deployment verification
After setting the token and host and deploying, sign in with analytics consent enabled, load the overview dashboard, import data if needed, and open Insights. Verify events in each provider's Live Events view. A configured status means credentials are present; it does not prove that events have arrived.
