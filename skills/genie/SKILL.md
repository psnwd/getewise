---
name: genie
description: Expert knowledge of Genie Business (Dialog Pay Business, geniebiz.lk, "Genie Business Connect"), Dialog's Sri Lankan payment gateway, covering code integration AND account/support questions. Use whenever the user mentions Genie, Genie Business, Genie Business Connect, Dialog Pay, geniebiz.lk, api.geniebiz.lk, api.uat.geniebiz.lk, geniebusiness.lk, PomeloPay (its X-Originator header), NOTIFY_TRANSACTION_CHANGE, X-Signature-Nonce, or wants to accept Visa/Mastercard/Amex cards, Genie wallet, eZ Cash, UPI, Alipay or JustPay in Sri Lanka through Dialog, even if they only describe a payment link, hosted payment page, card on file, merchant-initiated recurring charge or refund on that platform. Covers Create/Get Transaction V2, webhooks and signature verification, tokenization and MIT recurring payments, refunds and transaction states in Node/TypeScript, Go, Python, PHP/Laravel, Rust, Java and C#; WooCommerce and OpenCart plugins; sandbox (UAT) vs production; and doc gaps and contradictions.
---

# Genie Business (Dialog Pay Business)

Genie Business is Dialog's payment gateway for Sri Lankan merchants: cards (Visa, Mastercard, Amex) and wallets/QR (Genie, eZ Cash, UPI, Alipay, JustPay), local and foreign currency, hosted payment pages and payment links. The developer API is "Genie Business Connect" (REST + JSON, v2.0). This skill packs the public docs (geniebusiness.stoplight.io, geniebusiness.lk/developer, the WordPress plugin page, read Oct 2026). The public docs are partly auto-generated and have gaps; `references/troubleshooting.md` lists them. Flag them, don't paper over them.

## How to use this skill
1. Pick the task from the routing table.
2. Read only the matching reference file(s).
3. For code, start from `references/code-examples.md` and adapt to the user's stack.
4. Use `scripts/genie_webhook.py` to compute or check a webhook `X-Signature`.
5. Say that fees, limits and policies are not in the public docs; send those to Genie support (see `references/environments-account.md`).

## Routing table
| User needs | Read |
|---|---|
| Create a transaction, redirect to hosted page, fields, amount units, status check | `references/transaction-api.md` |
| Webhooks, `X-Signature` verification, event bodies | `references/webhooks.md` |
| Transaction states, refunds | `references/states-refunds.md` |
| Save a card, charge a saved card, recurring / MIT, scheduler | `references/tokenization-recurring.md` |
| Sandbox (UAT) vs production, API key, plugins, support contacts, account | `references/environments-account.md` |
| Code in Node/TS, Go, Python, PHP/Laravel, Rust, Java, C# | `references/code-examples.md` |
| Any error, doc contradiction, missing endpoint, security review | `references/troubleshooting.md` |

## Core rules
1. **Auth** = your API key in the `Authorization` header, as the docs show it (`Authorization: <key>`, no `Bearer`). Server-side only. Production base `https://api.geniebiz.lk`, sandbox/UAT `https://api.uat.geniebiz.lk`; they use different keys.
2. **Amount is an integer in minor units** (cents): `1000` = LKR 10.00. Responses also give `amountAsDecimal` (`"4.00"`) and `amountFormatted` (`"LKR 4.00"`). Never send a float like `10.00`.
3. **Create Transaction (V2)** = `POST /public/v2/transactions` with at least `{amount, currency}`; use the third (amount + currency) request variant. Redirect the customer to the returned `url` (hosted payment page); `shortUrl` is the share link. Store the returned `id` and your own `localId`.
4. **Paid means `state == "CONFIRMED"`** and nothing else. The redirect back to `redirectUrl` and the webhook are triggers, not proof: call Get Transaction (docs call it mandatory) and compare `state`, `amount`, `currency` and `localId` with your order.
5. **Webhooks** are POSTs to the `webhook` URL on the transaction, the global URL (dashboard Connect > Webhooks) or a Webhook App; all active ones fire. Verify `X-Signature = SHA256(X-Signature-Nonce + X-Signature-Timestamp + apiKey)` (hex, constant-time compare), then still re-query the API. That signature does not cover the body, so never trust body fields.
6. **Refunds** are `POST /public/transactions/{id}/refunds` with `refundAmount` and `refundReason`; the original stays `CONFIRMED` and a new refund transaction goes `REFUND_REQUESTED` then `REFUNDED`.
7. **Card on file** needs a Customer and `card_payments`. MIT (merchant-initiated) recurring is off by default; Genie support must enable it. Scheduler-driven charging also needs enabling.
8. **Test first on UAT.** Sandbox keys are issued on request; production keys are in the dashboard under Connect. Production can also run a "test payment provider" that bills nothing.

## Working style
- If the goal is ambiguous (hosted page vs payment link vs recurring), state the assumption and proceed.
- Show a full flow: create order > create transaction (minor units) > redirect to `url` > webhook with signature check > Get Transaction > idempotent DB update > status page from the DB.
- Flag contradictions listed in `troubleshooting.md` (Get Transaction path, `expiryDate` format, `recurringFrequency` values, refund unit) instead of silently choosing; tell the user to confirm with Genie support or in the Stoplight "Try it" console.
- Anything not in the references (endpoint paths for Customer, Charge Stored Token, Create Webhook, FX): say so, point to the Stoplight group, don't invent.
- Secrets from env vars, never in code you output.

## Bundled files
- `references/`: topic files above
- `scripts/genie_webhook.py`: CLI to compute/verify the webhook signature
