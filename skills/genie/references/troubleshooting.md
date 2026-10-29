# Troubleshooting, gaps and security

## Contents
1. Common problems
2. Doc contradictions and gaps (flag these)
3. Security checklist

## 1. Common problems
| Symptom | Likely cause / fix |
|---|---|
| 401 / unauthorized | missing or wrong `Authorization`; key from the other environment (UAT vs prod); a `Bearer ` prefix when the docs show the bare key (try the bare key first); key copied with whitespace |
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
- **Get Transaction path**: Stoplight shows `GET /public/transactions/{id}`; the webhook guide calls `/public/v2/transactions/{id}`. Create is `/public/v2/transactions`. Verify on UAT.
- **`expiryDate` format**: field text says `yyyy-mm-dd`, but the pattern shown and every example use `dd-mm-yyyy` (`12-07-2025`), with a length limit of 8 characters that even a full date string would exceed. Test on UAT.
- **`recurringFrequency` for card on file**: card-on-file page says `UNSCHEDULED`; the field's allowed list has `AD_HOC` but no `UNSCHEDULED`. Test; `paymentType: UNSCHEDULED` is the real switch.
- **Refund amount unit** is unstated (assume minor units, verify).
- **Webhook `originalSignature`**: deprecated; samples differ in shape (base64 vs 40 hex). Use header signature + API re-query.
- **Webhook timestamp** format and tolerance are not specified.
- **Auth example** is `Authorization: 123` (bare key). The wording "API key token" doesn't say Bearer or not.
- **Plugin vs API credentials**: client ID/secret (plugin) vs API key (API).
- **No public endpoints seen** for Create Customer, Charge Stored Token, Create Webhook, capture of AUTHORIZED, FX in the pages we read. Say so, point to Stoplight.
- Response field list is large and mostly "internal logic"; rely on the ones in `transaction-api.md`.
- The docs still mention the platform's former name (PomeloPay): `X-Originator: PomeloPay-Webhooks`. That's expected.
- Fees, limits, settlement, test card numbers: not public (sandbox keys file wasn't fetchable).

## 3. Security checklist
- API key only on the server; env var or secret manager; rotate if leaked. Never in JS, mobile apps or Git.
- Amount and currency come from your database when you create the transaction, never from the browser.
- Webhook handler: verify header signature with a constant-time compare, then Get Transaction; require `CONFIRMED`; compare amount, currency, `localId`; ignore duplicates; log, don't print.
- Use `localId` = your order ID and look the order up by it; reject if the transaction ID isn't the one you stored for that order.
- Hosted page means card data never touches your server. Keep it that way; don't log `token`, mask `paddedCardNumber` in UI.
- Refund and recurring-charge endpoints behind staff auth and idempotency keys of your own.
- Test on UAT, then a tiny real payment on production before launch.
