# Troubleshooting & doc quirks

Re-checked against the live docs on 13 Nov 2026; the items below are current.

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
| "Unexpected Error (PH-0022)" | Live action URL missing `www` (docs: this "may result in" PH-0022). Use `https://www.payhere.lk/pay/checkout` |
| Unexpected error only on HelaPay | Invalid/missing email or phone |
| "Something went wrong (code)" | Missing required fields; emoji / script tags / odd content in values |
| "Over Limit" for customer | Plan per-payment or monthly limit exceeded; upgrade plan |
| New domain doesn't work | Secret is per domain/app and approval takes up to ~24h |

## 2. notify_url problems
- Never fires on localhost: use a public URL (tunnel for dev).
- Content type is `application/x-www-form-urlencoded`, not JSON. Parse form bodies; in frameworks with CSRF protection (Laravel, Django, Rails) **exempt the notify route**.
- Respond 2xx fast; don't depend on printing to the screen: log to a file/DB.
- Make the handler idempotent, keyed on `payment_id` (or `order_id` + `message_type` for subscriptions): recurring sends several notifications per subscription and one can arrive late. PayHere does **not** redeliver a lost notification: "The notify call is initiated only once" (PayHere FAQ relayed through a 2024 community issue — third-party, not in the API docs) and there is no re-send API, so a scheduled `GET /merchant/v1/payment/search?order_id=<order_id>` reconciliation sweep is mandatory, not a nice-to-have.
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
- **Authorize API notification**: the status table lists success = `3` ("`3` - authorization success"), but the **same page's** PHP sample still tests `== 2` after md5sig verification (current as of 13 Nov 2026). The contradiction is intra-page, so re-reading won't resolve it: trust `3`.
- **Partial refunds**: the Refund API carries a "For partial refunds" sample with `"amount": "100.50"` (labelled only "Partial refund amount" — never marked optional or required, no sentence defines it; the sample is also invalid JSON and sets both `payment_id` and `authorization_token`), while the Refund Process page says "PayHere supports only full refunds. If you need to do a partial refund, you will have to refund it manually to your customer." No changelog note either way: flag it to the user, verify with support@payhere.lk, and treat an authenticated sandbox call with `amount` as the only test.
- **Preapproval error text** points to the checkout URL for PH-0022; preapproval/authorize have their own action URLs (`/pay/preapprove`, `/pay/authorize`), also needing `www` in live. (Both pages copy the checkout URL into their own PH-0022 sections.)
- **Menu/permission split**: Charging, Retrieval, Subscription Manager and Refund docs say `Settings > API Keys` > "Create API Key", tick **"Automated Charging API"**, then "View Credentials" (the Refund page then calls the result "the Business App in Step 1"). Capture docs say `Settings > Business Apps` > "Create App", tick **"Payment Capture API"**, "Add Business App", "View Credential". Merchant ID/Secret live under `Side Menu > Integrations`. "Domains & Credentials" appears nowhere in the current KB; the real UI needs a login to confirm.
- Subscription Manager responses use the typo `fist_name`, and the Retrieval API's `customer` objects carry it too — parse `customer` objects defensively everywhere.
- Docs examples have stray trailing commas in JSON (e.g. the Refund API full-refund sample); send valid JSON.
- The JS hash sample formats the amount with `toLocaleString`, which can add or change separators in other locales; format to `0.00` explicitly.

## 6. Security checklist (use when reviewing integrations)
- Merchant secret, App ID/Secret live only on the server; never in JS bundles or mobile apps (exception: per-app secret the Flutter SDK asks for; confirm on server anyway).
- Request `hash` generated server-side per order; amount comes from your DB, not the client.
- notify handler: verify md5sig, check `status_code`, compare amount/currency/merchant_id/order_id with your order, ignore duplicates. Respond 2xx before doing work.
- Reconciliation job: notify is sent once and never redelivered (PayHere FAQ via a community issue, third-party). Schedule a sweep of `GET /merchant/v1/payment/search?order_id=` for orders with no settled notification; that is the only fallback.
- Don't trust the JS SDK `onCompleted` or the redirect to `return_url` as proof of payment.
- Store `customer_token` encrypted; treat like a payment credential.
- Don't log full card data (PayHere only gives masked `card_no`).
- Whitelist PayHere? Docs don't publish notify source IPs, so rely on md5sig, not IP filtering.
- Chargeback exposure: no contest timeline or SLA is published. The T&C lets PayHere terminate if chargebacks exceed **1% of transactions per month consecutively**, and chargebacks "may lead to immediate account termination".
