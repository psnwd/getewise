# Card on File (customer tokenizer, automated charging)

Token auth (`Authorization: <APP_TOKEN>`), no hash. Visa and Mastercard only. Supports fixed recurring and variable (usage-based) charges with the same token.

## Flow
1. `POST /v3/customers/` body `app_id, first_name, last_name, email, phone_number (+94...), address, redirect_url` → `data.token_url`, `data.request_id`, `data.customer_id`.
2. Redirect the customer to `token_url` (OnePay-hosted card form), then they return to `redirect_url`.
3. `GET /v3/customers/{customer_id}/cards/?app_id=` → `token_id` (`tok_...`), `card_type`, `masked_number`, `expiry` (MM/YY).
4. Store `token_id` against the customer. Card numbers never touch your server.
5. Charge: `POST /v3/customers/{customer_id}/payments/` body `app_id, token_id, amount ("1000.00" string), currency` → `data.transaction_id, status (bool), amount, currency, token_id`.

Add another card to an existing customer: `POST /v3/customers/` with `app_id, customer_id, redirect_url`.

## Other endpoints
`GET /v3/customers/`, `GET /v3/customers/{id}/?app_id=`, `GET .../cards/{token_id}/?app_id=`, `DELETE .../cards/{token_id}/?app_id=` (soft delete, irreversible, history kept), `GET .../transactions/?app_id=` (newest first).

## Sandbox cards (tokenization/charge tests only)
Visa 4564456445644564, MC 5430489999999992, CVV 582, exp 12/26 (check expiry hasn't passed; fall back to the cards in `sandbox-currencies.md`).

## Notes
- The docs don't describe scheduling: **you** run the billing schedule and call the charge endpoint (the SDK's `processSubscription` is the separate, hosted option).
- No callback payload is documented for charges; read the sync response and confirm via transactions list.
- Ask the Relationship Officer whether Card on File is enabled for the account (not stated in the docs).
