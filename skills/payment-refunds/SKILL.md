---
name: payment-refunds
description: Refunds, partial refunds, voids and chargebacks across Sri Lankan payment gateways - which gateway has a refund API, request shape, refund states, what is undocumented, and how to build a safe refund endpoint (staff only, capped at paid amount, idempotent, reconciled). Use when the user asks "how do I refund", "partial refund", "refund API", "refund stuck in REFUND_REQUESTED", "chargeback", "customer disputes a payment", or designs refund handling for PayHere, OnePay, WebXPay, Genie Business or Koko. For exact signatures and auth use the gateway's own skill alongside this one; for general safety see payment-basics and payment-security-review.
---

# Payment refunds

Refunds move money out, so they are the highest-abuse path. Facts below come from the gateway skills; where docs are silent, **say so and ask the gateway**, never guess an endpoint.

## Gateway matrix
| Gateway | Refund API | Partial | States / notes |
|---|---|---|---|
| PayHere | `POST /merchant/v1/payment/refund` (OAuth). Body: `payment_id` **or** `authorization_token` (one only) plus `description` | **Docs contradict**: Refund API ships a "For partial refunds" sample with `"amount": "100.50"` (never marked optional), Refund Process says only full refunds. Confirm with support before shipping partials | Retrieval statuses: `RECEIVED`, `REFUND REQUESTED`, `REFUND PROCESSING`, `REFUNDED`, `CHARGEBACKED`. Result `status`: 1 ok, 0 error initiating, -1 failed. Instant refund same day (processed as a void); after payout 5-10 days+. Detail: the payhere skill's merchant-api reference |
| OnePay | `POST /v3/transaction/refund/`, `Authorization: <APP_TOKEN>`. Body: `app_id`, `onepay_transaction_id`, `refund_reason` (`DUPLICATED, FRAUDULENT, OUT_OF_ORDER, REQUESTED_BY_CUSTOMER, OTHER`), `is_partially`, `amount`, `refund_note` | Yes (`is_partially` + `amount`) | Live paid transactions only; **sandbox rejected**. One active refund per transaction. Returns `refund-initiated`. FX refunds use the rate on the refund date. No status lookup or webhook documented. Detail: the onepay skill's refund-payouts reference |
| Genie Business | `POST {base}/public/transactions/{id}/refunds`. Body: `refundAmount`, `refundReason` (max 255) | Yes; check `canRefundIfConfirmed`, `canPartialRefundIfConfirmed`, `canIncrementalPartialRefundIfConfirmed` on the transaction first | `REFUND_REQUESTED` (under review) then `REFUNDED`; `VOIDED` = reversed, no fee. `refundAmount` schema is a **number** and the unit is **not documented**: refund a small amount on UAT and observe. Detail: the genie skill's states-refunds reference |
| WebXPay | **None public.** Nav lists a Refund API with no page; Magento sets `$_canRefund = false`, the WHMCS function is a stub, the Woo plugin has no refund code | Unknown | Refund through the merchant portal or ask WebXPay for the API. `refundStatus: true` on a card-save response is a capability flag, not an endpoint |
| Koko | **None.** Refund is a merchant-portal action | **No** — Koko supports full refunds only | Commission is returned on refund, the processing fee is not. Use `orderView` to read order state. Detail: the koko skill |

## Safe refund endpoint
1. **Staff-only**, authenticated, audited (who, when, order, amount, reason). Never reachable from the storefront.
2. Order must be **paid** in your DB; load it by your id, not by a client-supplied gateway id.
3. Cap: `sum(refunds so far) + requested <= paid amount`, computed in your DB inside a transaction/row lock. Amount in minor units or `Decimal`, in the gateway's expected format.
4. **Idempotent:** record a refund row (`order, amount, reason, status=requested`) before calling the gateway; a retry or double click reuses the row. On timeout, look up the refund/transaction state before calling again.
5. Call the gateway; store the gateway refund id; set `requested`, not `refunded`.
6. Settle to `refunded` only from a verified callback or status lookup, through the same idempotent function as payments. Where the gateway has neither (OnePay), use a reconciliation job or manual confirm.
7. Forward-only states: `paid -> refund_requested -> refunded`. A late payment callback must not undo it.
8. Do the business side once: restock, revoke licence, cancel subscription (PayHere: `subscription/cancel`). Not before the refund is accepted.

## Chargebacks and disputes
- The card network, not you, decides. PayHere surfaces `CHARGEBACKED`; OnePay may hold settlement for unresolved chargebacks; Genie's chargeback rules are not public.
- Treat a chargeback as a state change: flag the order, stop fulfilment/subscription, keep evidence (order, delivery proof, IP, callback log, customer messages).
- Do not also refund a disputed payment; that pays twice. Ask the gateway for the dispute's status first.
- Fees, time limits and dispute windows are contractual: quote none, send the user to the gateway's account manager.

## Rules
- A refund API response is a request, not proof. Reconcile.
- Do not promise refund timing; banks settle on their own schedule.
- No gateway keys in output; env vars only.
- Test refunds only where the environment allows it (OnePay: not in sandbox); see payment-testing.
