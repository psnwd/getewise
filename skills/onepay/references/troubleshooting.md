# Troubleshooting and doc gaps

Re-checked against the live docs on 13 Nov 2026; the items below are current.

## Errors (create transaction)
| HTTP | Meaning / fix |
|---|---|
| 200 | Checkout link generated |
| 400 | Invalid body: invalid app ID, invalid amount, invalid app state (app not active), currency not enabled for the app. `error` carries the cause (`Invalid app id`, `Invalid amount`, `Invalid app state`, `Currency type not available for the app`); archived docs (developer.onepay.lk, no longer live) add `Monthly subscription quote exceed` |
| 401 | `Authorization` header missing, invalid App Token, or wrong hash. Body `{"status":401,"message":"Unauthorized request","error":"Invalid app credentials"}`; payment-link endpoints say `"error":"Invalid API key"`. Recheck: hash formula, amount string identical in hash and body (`100.00`), live vs sandbox credentials |
| 403 | Payout endpoints only: `{"detail":"Invalid app token"}` (different framework from the rest). Archived docs (developer.onepay.lk, no longer live) also show a 403 response tab on every endpoint, unexplained |
| 429 | Rate limit per App ID ("within a one second period"). Back off exponentially; ask support for higher limits |
5xx and transaction status codes are not documented.

## Common problems
- Hash mismatch: concatenation order is app_id, currency, amount, salt; amount formatted differently in hash vs body; wrong environment's salt; locale turning `.` into `,` (Java/C#/Go).
- Customer lands back but order unpaid: you relied on the return URL. Verify via the status API.
- Callback never arrives: URL not set in the portal APP section; not public; endpoint not returning 200; expects JSON, not form data.
- Phone rejected: not E.164. Redirect rejected: not HTTPS.
- Refund fails on test data: sandbox transactions can't be refunded.
- "Cannot reach sandbox": there is no sandbox host — `sandbox.onepay.lk`, `api.sandbox.onepay.lk` and `uat.onepay.lk` are NXDOMAIN. Use `https://api.onepay.lk` with sandbox-mode credentials.
- Payout call returns 403, everything else 401: expected, the payout endpoint uses a different error shape (`Invalid app token`).

## Gaps and contradictions in the official docs (flag these)
- Create-transaction headers are still not listed on the Payment API page; the 401 docs plus the live `WWW-Authenticate: AppToken` header settle it: raw App Token, **not** `Bearer` (the Laravel config comment "Bearer-style token" is misleading; its code sends the raw token).
- Callback: no signature in the body; the portal's **Callback Token** exists but its transmission is undocumented. Only status `1`/`SUCCESS` is published, and the retry/redelivery policy is unpublished.
- `additionalData` (docs table, Laravel SDK) vs `additional_data` (OnePay JS, npm SDK, callback) — both in circulation.
- Payment Link: create body undocumented (`expiration_date`, `allow_partial_payment` are prose only); `app_id` in query is confirmed by a doc sentence, yet the Update table still lists it in the body.
- Items: `metadata` object on write vs `[{key,value,is_deleted}]` on read; `is_deleted` per item and per metadata key vs "permanently removes" wording; `currency` LKR/USD only on that page vs 10 currencies globally.
- Rate limits: only the window ("within a one second period") and 429 are documented — no numbers, no 429 body, no `Retry-After`.
- 5xx behaviour and the transaction status code lists are absent, not merely hidden.
- Not documented: min/max transaction amount; whether `ipg_transaction_id` equals the id inside `redirect_url`; which test card approves vs declines.
- Subscription API (`/v3/subscription/`) exists only in the archived docs (developer.onepay.lk, no longer live) and the npm SDK — confirm before relying on it, see `subscriptions.md`.
