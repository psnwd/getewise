# Payment API (redirect checkout)

Base: `https://api.onepay.lk`, version prefix `/v3/`. JSON in/out.

## Flow
1. Get `app_id` + `hash_salt` (+ App Token) from the merchant dashboard (API Keys). Live and sandbox sets are separate.
2. `POST /v3/checkout/link/` with JSON body, `Authorization: <APP_TOKEN>`, `Content-Type: application/json`. The token is sent **raw** — no `Bearer` prefix; the server advertises the scheme as `WWW-Authenticate: AppToken` on 401.
3. Redirect the customer to `data.gateway.redirect_url` from the response, **same browser tab** (no popup/new tab).
4. Customer returns to `transaction_redirect_url`. Verify server-side with the status endpoint; do not trust URL params.

## Create transaction: `POST /v3/checkout/link/`
| Param | Req | Notes |
|---|---|---|
| `app_id` | yes | from dashboard |
| `amount` | yes | number, 2 decimals (`100.00`) |
| `currency` | yes | ISO 3-letter; must be enabled for the app |
| `hash` | yes | server-side SHA-256, see below |
| `reference` | yes | your order id, 10–64 characters |
| `customer_first_name`, `customer_last_name` | yes | |
| `customer_phone_number` | yes | E.164 `+94771234567` |
| `customer_email` | yes | receipts go here |
| `transaction_redirect_url` | yes | HTTPS |
| `additionalData` | no | string echoed back in the callback as `additional_data`. The docs table says `additionalData` and the Laravel SDK sends that; OnePay JS and the npm SDK send `additional_data` — contradiction, see `troubleshooting.md` |
| `items` | no | array of item IDs from the Items API (custom API integrations only; max 500, ids stringified; only 2 show on the receipt) |

### Hash
`hash = SHA256(app_id + currency + amount + HASH_SALT)`: plain string concatenation, no separators. Output is **lowercase hex, 64 chars**. `amount` must be the 2-decimal string — `toFixed(2)` in JS, `number_format($x, 2, '.', '')` in PHP — and `currency` is uppercased before hashing and sending. Worked example (archived docs, developer.onepay.lk, no longer live): input `80NR1189D04CD635D8ACDLKR100.00XXXHASHSALTXXX` → `126ff89348d80fb91ec4f25c2bd55e2f71d8f3986da9470eabe28b2f8becf21a`. `scripts/onepay_sign.py` computes it.

### Response
Documented body (sample from archived docs, developer.onepay.lk, no longer live; confirmed by the JS/npm/Laravel clients):
```json
{"status":200,"message":"Successfully generate checkout link","data":{
  "ipg_transaction_id":"XXXXXXXXXXXXXXXX",
  "amount":{"gross_amount":100.00,"discount":0,"handling_fee":0,"net_amount":100.0,"currency":"LKR"},
  "gateway":{"redirect_url":"https://payment.onepay.lk/redirect/XXXXXXXXXX"}}}
```
Parse `data.gateway.redirect_url` (nested under `gateway`) and `data.ipg_transaction_id` (direct child of `data`); `amount` is an object, not a scalar. **Don't hardcode the redirect host** — it appears as both `payment.onepay.lk/redirect/<id>` and `gateway.onepay.lk/checkout/<id>`; always use the URL as returned.

## Transaction status: `POST /v3/transaction/status/`
Body: `app_id`, `onepay_transaction_id` — "the transaction ID returned in the `ipg_transaction_id` field when the transaction was created" (doc quote), so the create and status ids are the same value.
200 response is nested: `data.ipg_transaction_id`, `data.amount` (number), `data.currency`, `data.transaction_request_datetime`, `data.status` (bool, true = paid), `data.paid_on` (`YYYY-MM-DD HH:mm:ss`, **`null` until paid**). Read `data.status`, not the top-level `status` (that's the HTTP-ish 200).

## Callback (webhook)
Set the URL in the portal's APP section. OnePay sends POST JSON after completion:
```json
{"transaction_id":"WQBV118E584C83CBA50C6","status":1,"status_message":"SUCCESS","additional_data":""}
```
`transaction_id` is the same string as the create response's `ipg_transaction_id` and the status API's `onepay_transaction_id`. Respond HTTP 200.

**No signature in the body or headers is documented.** Only status `1`/`SUCCESS` is published; do not assume other values. Retry/redelivery policy is not published for v3. Treat the callback as a trigger and confirm through the status API.

Two portal controls do exist (both per-app, neither documented on the API pages): a **Callback Token** — "a secret key to validate that incoming callbacks are genuinely from OnePay", set next to the callback URL; how it is transmitted (header name, body field, HMAC input) is **undocumented**, so it cannot be verified without a live callback — and a **CIDR/IP allowlist** (`*` allows all, or specific IPs), set at "Request to go Live". Callback authentication therefore exists in the product, even though the mechanism is undocumented.

## Rate limit and errors
Per App ID; 429 on excess. See `troubleshooting.md`.
