# Payment API (redirect checkout)

Base: `https://api.onepay.lk`, version prefix `/v3/`. JSON in/out.

## Flow
1. Get `app_id` + `hash_salt` (+ App Token) from the merchant dashboard (API Keys). Live and sandbox sets are separate.
2. `POST /v3/checkout/link/` with JSON body, `Authorization: <APP_TOKEN>`, `Content-Type: application/json`.
3. Redirect the customer to `redirect_url` from the response, **same browser tab** (no popup/new tab).
4. Customer returns to `transaction_redirect_url`. Verify server-side with the status endpoint; do not trust URL params.

## Create transaction: `POST /v3/checkout/link/`
| Param | Req | Notes |
|---|---|---|
| `app_id` | yes | from dashboard |
| `amount` | yes | number, 2 decimals (`100.00`) |
| `currency` | yes | ISO 3-letter; must be enabled for the app |
| `hash` | yes | server-side SHA-256, see below |
| `reference` | yes | your order id |
| `customer_first_name`, `customer_last_name` | yes | |
| `customer_phone_number` | yes | E.164 `+94771234567` |
| `customer_email` | yes | receipts go here |
| `transaction_redirect_url` | yes | HTTPS |
| `additionalData` | no | string echoed back in the callback as `additional_data` |
| `items` | no | array of item IDs from the Items API (custom API integrations only; up to 2 show on the receipt) |

### Hash
`hash = SHA256(app_id + currency + amount + HASH_SALT)`: plain string concatenation, no separators, `amount` exactly as in the body (`"100.00"`). The docs don't state hex casing or encoding: use lowercase hex of the UTF-8 bytes (what SHA-256 libraries emit by default) and confirm in sandbox. `scripts/onepay_sign.py` computes it.

Response: the docs name `redirect_url` and `ipg_transaction_id` (store it) but don't publish the full response schema.

## Transaction status: `POST /v3/transaction/status/`
Body: `app_id`, `onepay_transaction_id` (the `ipg_transaction_id` from create).
200 response: `status` (bool, true = paid), `ipg_transaction_id`, `amount`, `currency`, `paid_on` (`YYYY-MM-DD HH:mm:ss`).

## Callback (webhook)
Set the URL in the portal's APP section. OnePay sends POST JSON after completion:
```json
{"transaction_id":"WQBV118E584C83CBA50C6","status":1,"status_message":"SUCCESS","additional_data":""}
```
Respond HTTP 200. No signature is documented: verify with the status API before marking paid. The full list of numeric `status` values is not documented (1 = SUCCESS is the only one shown).

## Rate limit and errors
Per App ID; 429 on excess. See `troubleshooting.md`.
