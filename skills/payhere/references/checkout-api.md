# Checkout API (one-time payments)

Form-POST redirect flow. Customer's browser is POSTed to PayHere, pays there, PayHere calls your `notify_url` (server-to-server), then redirects the browser to `return_url`.

## Contents
1. Prerequisites
2. Step 1: redirect the customer (params, hash)
3. Step 2: notify_url callback
4. Step 3: verify md5sig
5. Error handling
6. Gotchas

## 1. Prerequisites
- **Merchant ID**: PayHere dashboard > Integrations. Unique per account.
- **Merchant Secret**: per domain/app. Integrations > Add Domain/App > enter top-level domain (or app package name) > Request to Allow > wait up to ~24h for approval > copy secret. New domain/app = new secret.

## 2. Redirect the customer

POST (HTML form, `application/x-www-form-urlencoded`) to:
- Live: `https://www.payhere.lk/pay/checkout` (**must include `www`**, else error PH-0022)
- Sandbox: `https://sandbox.payhere.lk/pay/checkout`

Required params: `merchant_id`, `return_url`, `cancel_url`, `notify_url` (public IP/domain, not localhost), `first_name`, `last_name`, `email` (valid format), `phone` (valid), `address`, `city`, `country`, `order_id`, `items`, `currency` (LKR/USD), `amount`, `hash` (required since 2023-01-16).

Optional: `delivery_address`, `delivery_city`, `delivery_country`, per-item `item_name_N` / `item_number_N` / `amount_N` / `quantity_N`, `platform`, `custom_1`, `custom_2`, `payment_method` (skip method picker: VISA, MASTER, AMEX, HELAPAY, FRIMI, QPLUS).

### hash (request signing)
```
hash = UPPER( md5( merchant_id + order_id + amount + currency + UPPER(md5(merchant_secret)) ) )
```
- `amount` must be formatted with **exactly 2 decimals, no thousands separator** (`1000.00`). Same string you submit.
- Compute **server-side only**. Doing it in the browser leaks the secret.
- Use `scripts/payhere_sign.*` for ready-made implementations in all supported languages.

## 3. notify_url callback

PayHere POSTs form-encoded (NOT JSON) params:
`merchant_id, order_id, payment_id, payhere_amount, payhere_currency, status_code, md5sig, custom_1, custom_2, method, status_message`.
Card payments also include `card_holder_name`, `card_no` (masked), `card_expiry` (MMYY).
`payhere_currency` can be LKR/USD/GBP/EUR/AUD. `method` values include VISA, MASTER, AMEX, EZCASH, MCASH, GENIE, VISHWA, PAYAPP, HNB, FRIMI.

status_code: `2` success, `0` pending, `-1` canceled, `-2` failed, `-3` chargedback.

## 4. Verify md5sig

```
local = UPPER( md5( merchant_id + order_id + payhere_amount + payhere_currency + status_code + UPPER(md5(merchant_secret)) ) )
```
Use the values **exactly as received** (do not reformat `payhere_amount`). Compare with `md5sig` (constant-time compare is good practice). Only mark paid when signature matches AND `status_code == 2`. Also check amount/currency/order_id against your own order record, so a validly-signed notification for a different order cannot be replayed.

## 5. Errors seen on the PayHere page
| Error | Likely cause / fix |
|---|---|
| Unauthorized payment request | Wrong/mismatched hash values; request not from registered domain; wrong secret for that domain; `Referer` header stripped (avoid `no-referrer`); duplicate Integration records for one domain |
| Unexpected Error (PH-0022) | Live URL missing `www` |
| Unexpected error with HelaPay | Missing/invalid email or phone |
| Something went wrong (code) | Missing required params, or invalid content (emoji, script tags) in values |

## 6. Gotchas
- `notify_url` never renders in the browser: you can't debug with echo/print; log to DB/file.
- Can't test notify on localhost: use a tunnel (ngrok, cloudflared) or deployed URL.
- `return_url` gets **no payment status params**. Read status from your DB (written by notify handler).
- Respond 200 quickly from notify handler; do the heavy work after.
- Each domain/app has its own secret; sandbox and live use different merchant credentials/secrets (see sandbox reference).
