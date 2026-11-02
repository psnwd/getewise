---
name: payment-basics
description: Gateway-agnostic payment integration rules - idempotency, webhook/callback verification, amount checks, reconciliation, PCI scope and secrets handling. Use when the user asks how to make a payment integration safe or correct in general, reviews a payment flow, asks "is my webhook secure", "how do I avoid double charging / double fulfilment", "do I need PCI compliance", or designs checkout, callbacks or refunds without naming a gateway. For gateway-specific signatures, fields and endpoints use that gateway's own skill (payhere, onepay, webxpay, genie, koko) alongside this one.
---

# Payment basics

Rules that hold for every gateway. This skill has no gateway API facts; signature formulas, field names and endpoints live in the gateway skills. Say so and defer rather than guess.

## 1. The browser is not proof of payment
Redirect/return pages are for the customer. Mark an order paid only from a **verified server-to-server callback** or a **status API lookup** you made yourself.

## 2. Verify every callback, in this order
1. Read the **raw body** (re-serialised JSON/forms break signatures).
2. Verify the signature/hash with the gateway's scheme; compare with a **constant-time** function (`hmac.compare_digest`, `crypto.timingSafeEqual`, `hash_equals`). Bad signature: reject (400), log, do nothing else.
3. Load the order by **your** id. Unknown: 404.
4. Check **amount, currency and merchant id** against your DB, not against the callback alone.
5. Check state and idempotency (section 3), then update, then return 200.
6. If the gateway gives a timestamp/nonce, reject stale ones; if it offers a status API, confirm there before fulfilling high-value orders.

Callback routes: exempt from CSRF and session auth, POST only, no redirects, fast (queue slow work), always 200 once handled so the gateway stops retrying.

## 3. Idempotency
Callbacks repeat, arrive out of order and race with the return page. Make "mark paid" safe to run twice:
- Unique constraint on `(provider, gateway_ref)`; insert first, fulfil only if the insert was new.
- Forward-only state machine: `pending -> paid -> refunded`; a late `FAILED` must not undo `paid`.
- Outbound calls (create payment, refund, charge saved token) carry your own idempotency/order id; on timeout **look up** before retrying, never blind-retry a charge.
- Fulfilment (email, stock, licence) runs once, after the insert, not before.

## 4. Money handling
- Amounts in **minor units** (integers) or `Decimal`; never float. Match the gateway's format exactly (decimals, rounding) since many sign the amount string.
- Server computes the amount from the cart; never trust an amount from the browser.
- Refund unit and partial refunds differ per gateway: check the gateway skill.

## 5. Reconciliation
A job (hourly/daily) looks up every order `pending` older than N minutes via the gateway's status API and settles through the **same** function as callbacks. Callbacks get lost; this is the safety net.

## 6. PCI and secrets
- Use hosted/redirect checkout or the gateway's JS/SDK fields so card numbers never touch your server, logs, analytics or support tools. That keeps you at the lightest PCI scope (SAQ A style); handling PAN yourself is a different, far heavier burden.
- Never store CVV. Store gateway tokens, not PANs, for saved cards.
- Secrets (app secrets, salts, private keys) in env/secret store, never in the repo, front-end bundle or logs. Merchant secret in client code = compromised. Rotate on leak.
- HTTPS everywhere, including callback URLs. Redact secrets and card-like numbers from logs.
- Separate sandbox and live credentials; a switch per provider.

## 7. Test before live
Sandbox: success, failure, cancel, duplicate callback, tampered amount, bad signature, callback before return page, callback never arriving (reconciliation recovers).

Several gateways in one app: see the multi-provider reference bundled in each gateway skill.
