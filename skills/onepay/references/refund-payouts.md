# Refunds, payouts and settlement

## Refund: `POST /v3/transaction/refund/`
Headers `Authorization: <APP_TOKEN>`, `Content-Type: application/json`. No hash.
Body: `app_id` (must match token's app), `onepay_transaction_id`, `refund_reason` (required: `DUPLICATED | FRAUDULENT | OUT_OF_ORDER | REQUESTED_BY_CUSTOMER | OTHER`), `is_partially` (bool, default false), `amount` (required if partial, ignored if full), `refund_note`.
- Only paid, **live** transactions; sandbox transactions are rejected. One active refund per transaction.
- Success (200): `data.refund_id`, `data.status = "refund-initiated"`, `requested_amount`, etc. Transaction becomes `REFUND INITIATED`; the bank partner processes it.
- Errors (400/401): missing Authorization; `refund_reason` required; amount required for partial; invalid app credentials; transaction not found; refund already requested.
- Foreign-currency refunds use the FX rate on the **refund date**, not the original date.
- Not documented: refund status lookup/webhook, cumulative partial limits, fee treatment.

## Payouts (read-only, token auth)
- Lookup: `GET /v3/payout/transaction/?onepay_transaction_id=...` → `order_id, currency, net_amount, commission_rate, commission_amount, settlement_amount, settlement_date`. `net_amount - commission_amount = settlement_amount`.
- List: `GET /v3/payout/transactions/?start_date=&end_date=&page=&page_size=` (all required; dates `YYYY-MM-DD` inclusive; page starts 1; page_size 20-100, keep constant). `total_pages = ceil(count/page_size)`. `settlement_date: null` = captured, not yet settled.

## Settlement rules
T+2 bank working days (Amex T+3); payout before 6 PM on payout day via CEFT to your registered bank account; report emailed only on payout days with a bank reference; no early or split payouts. Holds possible for unresolved chargebacks, business-nature conflicts, card-network fraud flags or chargeback recovery. Bank-side failures reschedule to next cycle; wrong account details go through your Relationship Officer. Settlement is always LKR.
Fee example in the docs: 2.5% MDR (illustrative; actual rates are contractual, confirm with OnePay).
