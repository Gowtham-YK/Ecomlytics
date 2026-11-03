# Mixpanel Tracking Implementation

## Consent
Mixpanel forwarding uses the existing server-side product analytics adapter and is gated by an explicit browser consent choice. The login/registration page offers an optional analytics checkbox. Existing signed-in users without a saved choice see an Allow / Decline prompt. The event API rejects events unless `analytics_consent: true` is supplied. The choice is stored in browser local storage.

## Identity and delivery
- `distinct_id` is the authenticated Ecomlytics database user ID (`users.id`), never email.
- The existing first-party `product_events` store remains the source event log.
- Mixpanel receives the event through the existing server-side HTTP ingestion adapter.
- `$insert_id` uses the persisted first-party event ID, providing a stable deduplication key for retries.
- The Mixpanel project token remains server-side in `MIXPANEL_PROJECT_TOKEN`; do not put it in browser JavaScript or commit it.

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

## Properties
Only properties present in the supplied tracking plan and available from a real source are sent. Values that the current app cannot establish (for example company size, invitation metadata, OAuth scopes, connection duration, delivery mode, and time-to-first-result) are omitted rather than fabricated. `integrations_used` is preserved as a string array.

## Deployment
Set `MIXPANEL_PROJECT_TOKEN` in the Render service environment. The token is intentionally not hardcoded in the repository. After deploying, sign in with analytics consent enabled and verify events in Mixpanel Live View. A `connected` configuration state only means a token is configured; it does not prove that events have arrived.
