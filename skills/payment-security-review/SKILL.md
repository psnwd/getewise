---
name: payment-security-review
description: Security review of a payment integration's code - callback/webhook verification, forged or replayed payments, amount tampering, secret and key leaks, card-data exposure, refund abuse, IDOR on orders, and missing reconciliation. Use when the user asks to security review, audit, pen-test or "check the safety of" checkout, payment callbacks, refunds or saved-card code, including PayHere, OnePay, WebXPay, Genie Business and Koko integrations. Reports evidence-backed findings only. For fixes and gateway-specific signature details use the gateway's own skill and payment-basics alongside this one.
---

# Payment security review

Find flaws that let someone get goods without paying, pay less, redo or reverse a payment, read other customers' orders, or steal keys and card data. Method adapted from [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill): source first, every finding needs a trace, unproven leads are labelled, nothing is probed live.

## Rules
- **Read-only on source.** Do not call live gateway endpoints, real merchant accounts or production URLs. Use sandbox/dummy credentials only; run target code only in a sandbox with no external network. Never print real secrets in the report: redact to the first 4 chars.
- **No trace, no finding.** Each finding names the file:line where the untrusted input enters, where the check is missing or wrong, and the concrete outcome ("order 12 marked paid with a forged POST").
- **Three verdicts:** `confirmed` (full trace from input to impact), `needs-validation` (exact unresolved fact, e.g. "does the gateway sign the amount field?", no severity), `rejected` (disproved; say why in one line). Do not pad with theoretical issues.
- **Gateway facts come from the gateway's skill**, not memory. If its reference does not say, mark `needs-validation` instead of guessing.

## Steps
1. **Map.** List payment code: checkout start, return/cancel pages, callback routes, refund/charge/token calls, order model, env/config, logs. Note which gateway each file uses.
2. **Hunt** with the checklist below, one pass per class.
3. **Verify each candidate:** try to disprove it (middleware, DB constraint, framework default). Keep only what survives.
4. **Report** (format at the end). Order by impact; give the smallest fix per finding and which skill has the correct code.

## Checklist
**Callback / webhook**
- Signature or hash not verified, verified after acting, compared with `==` instead of constant-time, or verified over a re-serialised body.
- Verified fields not the ones used (signature covers `orderId` but code reads `amount` from elsewhere).
- Amount, currency or merchant id taken from the callback or the browser rather than the DB.
- Order looked up by a gateway-supplied id that another customer's order can match; callback for provider A accepted for an order created with provider B.
- No idempotency: duplicate callback re-fulfils; unique `(provider, ref)` missing; late `FAILED` overwrites `paid`.
- Return/redirect page marks the order paid.
- Callback route behind CSRF/auth (silently fails) **or** open and unauthenticated with no signature (forgeable).
- Stale or replayed callbacks accepted where the gateway provides a nonce/timestamp.

**Checkout and amounts**
- Amount or order total accepted from the client; price, qty, discount or currency tampering.
- Signed form or hash built in the browser (secret/private key in front-end code).
- Amount formatting (decimals/rounding) differs between what is signed and what is stored.
- Open redirect via return/cancel URL parameters.

**Orders and access**
- IDOR: order, invoice, payment status or receipt fetched by sequential id without an ownership check.
- Refund/capture/charge-token endpoints without admin auth, without amount cap, or repeatable (double refund). Refund amount above the paid amount.
- Saved-card token charged for a customer other than its owner.

**Secrets and data**
- App secret, salt, API key, private/public PEM in repo, front-end bundle, committed `.env`, logs, error pages, analytics or URLs. Sandbox and live keys mixed.
- Card number, CVV or full tokens stored or logged; card form posted to own server.
- Callback or API traffic over HTTP; TLS verification disabled in the HTTP client.
- Debug mode, verbose gateway errors or stack traces shown to customers.

**Resilience**
- No reconciliation job: a lost callback leaves a paid order pending forever, or a pending one never expires.
- No rate limit on payment-start, refund or order lookup endpoints (card testing, enumeration).
- Gateway plugins (WordPress/Woo, Shopify, OpenCart) outdated or unmaintained.

## Report format
```
## Summary
<n confirmed, n needs-validation, n rejected; one-line risk statement>

### [High|Medium|Low] <title>  (confirmed)
Where: path:line -> path:line
Trace: <input> -> <missing/wrong check> -> <impact>
Fix: <smallest change>; see <gateway skill / payment-basics>

### <title>  (needs-validation)
Open fact: <exact thing to confirm and how>
```
Severity: High = free goods, forged payment, secret/card exposure, cross-customer data. Medium = double fulfilment, refund abuse needing auth. Low = hardening.
