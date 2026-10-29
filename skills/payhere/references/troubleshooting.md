# Troubleshooting & doc quirks

## Contents
1. Checkout page errors
2. notify_url problems
3. Signature mismatch checklist
4. Merchant REST API errors
5. Known inconsistencies in the official docs
6. Security checklist

## 1. Checkout page errors
| Symptom | Fix |
|---|---|
| "Unauthorized payment request" | Hash inputs differ from posted values (amount format `1000.00`, currency, order_id); wrong secret; page not served from the domain registered under Integrations; missing `Referer` header (remove `no-referrer` policies); duplicate Integration entries for one domain; for preapproval w/o amount, hash must use `10.00` (LKR) / `0.51` (others); recurring with future `recurring_start_date` hash uses `10.00` (LKR) / `0.50` (others) |
| "Unexpected Error (PH-0022)" | Live action URL missing `www`. Use `https://www.payhere.lk/pay/checkout` |
| Unexpected error only on HelaPay | Invalid/missing email or phone |
| "Something went wrong (code)" | Missing required fields; emoji / script tags / odd content in values |
| "Over Limit" for customer | Plan per-payment or monthly limit exceeded; upgrade plan |
| New domain doesn't work | Secret is per domain/app and approval takes up to ~24h |

## 2. notify_url problems
- Never fires on localhost: use a public URL (tunnel for dev).
- Content type is `application/x-www-form-urlencoded`, not JSON. Parse form bodies; in frameworks with CSRF protection (Laravel, Django, Rails) **exempt the notify route**.
- Respond 2xx fast; don't depend on printing to the screen: log to a file/DB.
- Good practice (not stated in the docs): make the handler idempotent, keyed on `payment_id` (or `order_id` + `message_type` for subscriptions), because callbacks can repeat or arrive late, and recurring sends several per subscription.
- `return_url` gets no status: show status from DB after notify wrote it (it may arrive slightly after the redirect, so poll/refresh).

## 3. Signature mismatch checklist
1. Use `payhere_amount` and `payhere_currency` strings exactly as received (not re-rounded).
2. Secret is for the **same domain/app and same environment** (sandbox vs live).
3. `UPPER(md5(secret))` is inserted, not the raw secret.
4. Result compared upper-case to `md5sig` (case-sensitive compare is fine if both upper-cased).
5. Concatenation order: merchant_id, order_id, payhere_amount, payhere_currency, status_code, hashedSecret. No separators.
6. Request-hash amount: 2 decimals, no thousands separators (JS `toLocaleString` adds commas; strip them).
7. Java/C#/Go: culture/locale can turn `.` into `,`: force invariant/US formatting.

Use `scripts/payhere_sign.py` to compute expected values.

## 4. Merchant REST API errors
| Response | Meaning / fix |
|---|---|
| `invalid_token` "Invalid access token" / "Access token expired" | Get a new token (lifetime ~599 s) |
| `status:-2 "Authentication error"` | Calling from non-whitelisted domain/IP, or key lacks the needed permission |
| 401 `"Access denied for the domain"` | Sandbox: key's domain `*`. Live: email support@payhere.lk |
| `status:-1 "Invalid token"` | Bad `customer_token` (charge) or `authorization_token` (capture) |
| `"Invalid currency"` / `"Invalid amount"` | Check currency enabled for plan; amount > 0 and numeric |
| "Subscription is not eligible for retrying" | Not failed, or cancelled |
| "Capture amount must be less than or equal to the authorized amount" | Reduce amount |
| "Authorization is already CAPTURED/REFUNDED" | Token spent |
| Rejected/blocked bursts | Rate limit 20 requests / 10 s |
| Works in sandbox, blocked live | Live also needs your server IP whitelisted by PayHere (email support@payhere.lk) |

## 5. Known inconsistencies in the official docs (flag these to users)
- **Authorize API notification**: status table says success = `3`, but the sample PHP checks `== 2`.
- **Partial refunds**: Refund Process page says unsupported; Refund API documents a partial `amount` param.
- **Preapproval error text** points to the checkout URL for PH-0022; preapproval/authorize have their own action URLs (`/pay/preapprove`, `/pay/authorize`), also needing `www` in live.
- **Retrieval / Subscription / Refund** docs tell you to tick the "Automated Charging API" permission; Capture docs mention "Business Apps" with "Payment Capture API". Menu names differ across doc pages (Settings > API Keys vs Business Apps vs Domains & Credentials).
- Subscription Manager response uses the typo `fist_name`.
- Docs examples have stray trailing commas in JSON (e.g. refund body); send valid JSON.
- The JS hash sample formats the amount with `toLocaleString`, which can add or change separators in other locales; format to `0.00` explicitly.

## 6. Security checklist (use when reviewing integrations)
- Merchant secret, App ID/Secret live only on the server; never in JS bundles or mobile apps (exception: per-app secret the Flutter SDK asks for; confirm on server anyway).
- Request `hash` generated server-side per order; amount comes from your DB, not the client.
- notify handler: verify md5sig, check `status_code`, compare amount/currency/merchant_id/order_id with your order, ignore duplicates.
- Don't trust the JS SDK `onCompleted` or the redirect to `return_url` as proof of payment.
- Store `customer_token` encrypted; treat like a payment credential.
- Don't log full card data (PayHere only gives masked `card_no`).
- Whitelist PayHere? Docs don't publish notify source IPs, so rely on md5sig, not IP filtering.
