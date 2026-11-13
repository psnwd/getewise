# Troubleshooting, gaps and security

Re-checked 13 Nov 2026 against the Stoplight spec-mock and the official PHP SDK.

## Contents
1. Common problems
2. Doc contradictions and gaps (flag these)
3. Security checklist

## 1. Common problems
| Symptom | Likely cause / fix |
|---|---|
| 401 / unauthorized | missing or wrong `Authorization`; key from the other environment (UAT vs prod); a `Bearer ` prefix — auth is the bare key, no scheme; key copied with whitespace |
| Amount is 100x too small or large | amount is minor units: LKR 25.00 is `2500`. Don't send floats |
| 400 on create | missing `currency`; field over its max length (`localId` 100, `webhook`/`redirectUrl` 200); malformed `customer{}` (billing fields are required inside it); `expiryDate` wrong format when RECURRING |
| Customer paid but order stays pending | you relied on `redirectUrl`; webhook not reachable (public HTTPS), blocked by CSRF/auth middleware, or you reject it on signature mismatch (wrong key/environment) |
| Signature mismatch | concatenation must be `nonce + timestamp + apiKey` with no separators, then SHA-256 hex; use the key for the same environment; headers read case-insensitively; compare the hex string you computed with the header as sent |
| Same webhook twice | several webhooks (global + per transaction + app) all fire; dedupe on `transactionId` and state |
| Webhook says CONFIRMED but Get says otherwise | trust Get Transaction |
| Checkout link dead | `CANCELLED` (timed out via `expires`) or `FAILED`; create a new transaction |
| Charging a saved card fails | MIT not enabled for the account; customer has no token; token expired (`tokenExpiryMonth/Year`); first token use needs 3DS |
| Refund stuck at `REFUND_REQUESTED` | normal; the gateway team reviews it. Check balance and ask support if it lingers |
| Works on UAT, not on prod | prod key, prod base URL, production account approved and the needed features (MIT, FX, plans) enabled |

## 2. Doc contradictions and gaps (flag these to users)
- **Get Transaction path is settled**: `GET /public/transactions/{id}` is live — the spec-mock resolves it (401, auth required) and the official SDK's `Transactions::get()` calls `transactions/{id}` under `/public/` (official SDK). `/public/v2/transactions/{id}` is **absent from the spec** (spec-mock: 422 "Route not resolved, no path matched") and appears only in the webhook page's Node sample — a typo. Create remains `POST /public/v2/transactions`.
- **`expiryDate` is unsatisfiable in the spec**: the field doc says "Format: yyyy-mm-dd … maximum 8 characters, pattern: dd-mm-yyyy" in one sentence; a 10-char `dd-mm-yyyy` fails the length cap and an 8-char string fails the pattern (spec-mock). Doc examples use both `12-07-2025` and `2025-12-31`. Only a UAT call settles which value the server accepts.
- **`paymentType` / `recurringFrequency`**: `paymentType` enum is exactly `UNSCHEDULED, RECURRING`. `recurringFrequency` lists 10 values (DAILY, WEEKLY, BIWEEKLY, FORTNIGHTLY, MONTHLY, QUARTERLY, TWICE_YEARLY, YEARLY, AD_HOC, OTHER) with `UNSCHEDULED` only in the UNSCHEDULED branch (spec-mock). `AD_HOC` is always valid; card-on-file examples do use `UNSCHEDULED`.
- **Refund `refundAmount` unit** is unstated: the schema is a **number** and accepts decimals (spec-mock), and the doc examples are `100.00` and `50.25`. Refund a small amount on UAT and observe.
- **Webhook `originalSignature`** is deprecated and is `base64(md5("amount=..&currency=..&apiKey=.."))`; the body field `signature` is `sha1(...)` hex (what the official plugin verifies). Different hashes; use header signature + API re-query.
- **Webhook timestamp** format and any tolerance / replay window are genuinely undocumented (the sample passes `'your_timestamp'`); cache nonces yourself.
- **Auth is a bare key, no scheme**: `Authorization: 123` in every official cURL, `'Authorization' => $apiKey` in the SDK (official SDK). `Bearer` appears only in third-party AI snippets.
- **Plugin vs API credentials**: client ID/secret (plugin) vs API key (API).
- **Documented endpoints**: create/delete webhook (`/public/webhooks`, `hookUrl`), customers list/get/update/delete (`/public-customers/`), token list/get/delete. **Still unresolved**: Create Customer's page exists but the POST body is unrecoverable and the mock does not implement create; Charge Stored Token is documented only as relative `POST /charge-stored-token` (absolute URL unverified); capture of `AUTHORIZED` has no public endpoint; FX has no recoverable path.
- Response field list is large and mostly "internal logic"; rely on the ones in `transaction-api.md`.
- The docs still mention the platform's former name (PomeloPay): `X-Originator: PomeloPay-Webhooks`. That's expected.
- Fees and settlement **are** published on the pricing page (see `environments-account.md`); limits and minimum amount are not. Test card numbers: the linked `Test API Keys 2.txt` now 404s.

## 3. Security checklist
- API key only on the server; env var or secret manager; rotate if leaked. Never in JS, mobile apps or Git.
- Amount and currency come from your database when you create the transaction, never from the browser.
- Webhook handler: verify header signature with a constant-time compare, then Get Transaction; require `CONFIRMED`; compare amount, currency, `localId`; ignore duplicates; log, don't print.
- Use `localId` = your order ID and look the order up by it; reject if the transaction ID isn't the one you stored for that order.
- Hosted page means card data never touches your server. Keep it that way; don't log `token`, mask `paddedCardNumber` in UI.
- Refund and recurring-charge endpoints behind staff auth and idempotency keys of your own.
- Test on UAT, then a tiny real payment on production before launch.
