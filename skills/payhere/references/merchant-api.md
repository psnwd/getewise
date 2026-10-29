# Merchant REST APIs (OAuth): Charging, Retrieval, Subscription Manager, Refund, Capture

All live under `/merchant/v1/`. Hosts: Live `https://www.payhere.lk`, Sandbox `https://sandbox.payhere.lk`.

## Contents
1. Auth setup (API key > Basic > token)
2. Rate limit & live restrictions
3. Charging API
4. Retrieval API
5. Subscription Manager API
6. Refund API
7. Capture API (Hold on Card)
8. Authorize API (redirect, gets the authorization_token)
9. Common errors

## 1. Auth setup
1. Dashboard > Settings > API Keys > Create API Key: app name + comma-separated whitelisted domains; tick the permission (e.g. "Automated Charging API"); save; View Credentials for **App ID** and **App Secret**.
   - Capture API docs call this "Business Apps" with the "Payment Capture API" permission; the UI may label it either way. Tick every permission your integration needs.
2. Authorization code = `base64(APP_ID + ":" + APP_SECRET)`. Compute in code, never on a public website.
3. Token: `POST /merchant/v1/oauth/token`
   - Headers: `Authorization: Basic <code>`, `Content-Type: application/x-www-form-urlencoded`
   - Body: `grant_type=client_credentials`
   - Response: `{access_token, token_type: "bearer", expires_in: 599, scope: "SANDBOX"}`. Token lives ~10 minutes: cache it and refresh on expiry/`invalid_token`.
4. Call APIs with `Authorization: Bearer <access_token>`.

## 2. Rate limit & live restrictions
- Max **20 requests per 10 seconds** on `/merchant/v1/*`.
- Live: only callable from whitelisted **domains**, and additionally from whitelisted **server IPs**: email `support@payhere.lk` with your server IP to get it enabled.
- Never call from a mobile app directly: put your own backend in between (keeps App Secret off devices).
- Sandbox: set the API key's allowed domain to `*` if you hit "Access denied for the domain".

## 3. Charging API: charge a preapproved customer
`POST /merchant/v1/payment/charge` (JSON)
```json
{
  "type": "PAYMENT",            // PAYMENT (default, capture now) | AUTHORIZE (hold; live only)
  "order_id": "Order12345",
  "items": "Taxi Hire 123",
  "currency": "LKR",
  "amount": 345.67,
  "customer_token": "<from preapproval notify>",
  "custom_1": "...", "custom_2": null,         // optional
  "notify_url": "https://...",                 // optional
  "itemList": [{"name":"..","number":"..","quantity":1,"unit_amount":300.00}]  // optional
}
```
Response: `{status, msg, data:{order_id, items, currency, amount, payment_id, status_code, status_message, md5sig, authorization_token}}`. `authorization_token` non-null only for `AUTHORIZE`. `data.status_code`: 2 success, 0 pending, -1 canceled, -2 failed.
Errors: `{status:-1,msg:"Invalid token"|"Invalid currency"|"Invalid amount"}`, `{status:-2,msg:"Authentication error"}`.

## 4. Retrieval API
`GET /merchant/v1/payment/search?order_id=<order_id>`
Returns `data[]` of successful payments for that order_id (PayHere does not enforce order_id uniqueness, so expect multiple). Each has `payment_id, order_id, date, description, status, currency, amount, customer{...}, amount_detail{gross, fee, net, exchange_rate,...}, payment_method{method, card_customer_name, card_no}, items`.
- Top-level `status`: 1 ok, 0 pending, -1 no records ("No payments found"), -2 declined.
- `data[].status`: `RECEIVED`, `REFUND REQUESTED`, `REFUND PROCESSING`, `REFUNDED`, `CHARGEBACKED`.
- Only successful payments are returned.

## 5. Subscription Manager API (for Recurring API subscriptions)
- List: `GET /merchant/v1/subscription`
- One: `GET /merchant/v1/subscription/{subscription_id}`
- Payments of one: `GET /merchant/v1/subscription/{subscription_id}/payments`
- Retry failed: `POST /merchant/v1/subscription/retry` body `{"subscription_id": 420075032251}` (error "not eligible for retrying" if not failed or already cancelled)
- Cancel: `POST /merchant/v1/subscription/cancel` body `{"subscription_id": ...}` (errors if already cancelled/completed)
Top-level `status`: 1 success, -1 failure (read `msg`). Subscription `status`: `ACTIVE`, `COMPLETED`, `FAILED`.
Note: response keys use the misspelling `fist_name` under `customer`.

## 6. Refund API
`POST /merchant/v1/payment/refund` (JSON)
- Refund a payment: `{"payment_id":"320027150501","description":"reason"}` 
- Refund an authorization (hold): `{"authorization_token":"...","description":"reason"}`
- Pass only one of payment_id / authorization_token. Optional `"amount":"100.50"` for a partial refund.
Success: `{status:1, msg:"Successfully processed the refund", data:<refund number>}` (authorization refund returns `data:null`). Status: 1 ok, 0 error initiating, -1 failed (see msg). Invalid id: "Error processing refund".

## 7. Capture API (Hold on Card)
`POST /merchant/v1/payment/capture`
```json
{"authorization_token":"...","amount":80.00,"deduction_details":"Item1 out of stock"}
```
Capture amount must be <= authorized amount. Response `data`: `status_code` (2 success, 0 unknown, -2 failed), `payment_id`, `amount`, `captured_amount`, `order_id`, `md5sig`, ...
Errors: "Invalid token", "Capture amount must be less than or equal to the authorized amount", "Authorization is already CAPTURED", "Authorization is already REFUNDED".
Needs the "Payment Capture API" permission on the key. Business rules (7-day window, Visa/Mastercard credit only) are in `account-business.md`.

## 8. Authorize API (customer authorizes a hold)
Redirect form POST to Live `https://www.payhere.lk/pay/authorize`, Sandbox `https://sandbox.payhere.lk/pay/authorize`. Params and hash identical to Checkout (amount required).
Notification extras: `authorization_token`, `status_code` of **3 = authorization success**, 0 pending, -1 canceled, -2 failed.
**Doc inconsistency**: the official PHP sample tests `status_code == 2` after md5sig verification, but the table says success is `3`. Trust the table: treat `3` as authorized, and log unexpected codes.
`AUTHORIZE` via the Charging API (token-based) is live-only.

## 9. Common errors (all merchant APIs)
- `{"error":"invalid_token","error_description":"Invalid access token: ..."}` / `"Access token expired: ..."`: refresh token.
- `{"status":-2,"msg":"Authentication error"}`: domain/IP not allowed, or key lacks permission.
- HTTP 401 `{"status":-1,"msg":"Access denied for the domain"}`: PayHere couldn't validate key's domain. Sandbox: use `*`. Live: email support@payhere.lk.
