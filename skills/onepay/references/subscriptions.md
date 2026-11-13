# Subscriptions (recurring API)

**Provenance: archived docs (developer.onepay.lk, no longer live) plus the npm SDK `onepay-sdk` 1.0.3.** The current docs site has no Subscription page, so treat every field below as unconfirmed against live behaviour and confirm before relying on it. The endpoint itself is live: `POST /v3/subscription/` without credentials returns 401 with `WWW-Authenticate: AppToken`.

Auth: `Authorization: <APP_TOKEN>` (raw, no `Bearer`), `Content-Type: application/json`.

## Create: `POST /v3/subscription/`
| Field | Notes |
|---|---|
| `app_id` | |
| `name` | plan/description label |
| `amount` | number |
| `currency` | |
| `interval` | `MINUTE \| DAY \| WEEK \| MONTH \| YEAR` |
| `interval_count` | string |
| `days_until_due` | retry/defer window; "the subscription will automatically be retried after the number of days specified in the `days_until_due` attribute" |
| `trial_period_days` | |
| `customer_details` | `{first_name, last_name, email, phone_number}` |

Response `data`: `subscription_id` (`sub_…`), `customer_id` (`cus_…`), `status` (`TRIAL_PERIOD` or `ACTIVE`), `url` — the hosted management page, `https://subscription.onepay.lk/?id=sub_…&is_iframe=False`. Send the customer there to enter card details.

## Get / update
- `GET /v3/subscription/{subscription_id}`
- `PUT /v3/subscription/` with `days_until_due`, `trial_period_days`, `is_delete`, `is_paused`, `is_canceled`. Docs typo: the field table says `is_paused`, the FAQ says `is_pause` — use `is_paused` and verify.

## Manual retry
`https://subscription.onepay.lk/redirect/<subscription_id>` re-attempts the charge.

## Notes
- Subscription hashing in the npm SDK is `SHA256(app_id + currency + amount + APP_TOKEN)` — the App Token instead of the Hash Salt. Suspicious and unverified; don't copy it without testing.
- The client-side alternative is the npm SDK's `processSubscription` (see `js-sdk.md`); there is no documented callback payload for subscription charges.
- Unknown: subscription status enum beyond `TRIAL_PERIOD`/`ACTIVE`, retry counts/intervals, cancellation semantics.
