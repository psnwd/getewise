---
name: koko
description: Expert knowledge of Koko (paykoko.com, Koko Pay, "Buy Now Pay Later"), a Sri Lankan BNPL payment gateway by Koko Pay, covering code integration AND account/support questions. Use whenever the user mentions Koko, paykoko.com, qaapi.paykoko.com, prodapi.paykoko.com, api/merchants/orderCreate, orderView, _mId, _responseUrl, dataString, Koko BNPL, or wants to let Sri Lankan customers pay in installments via Koko, even if they only describe an RSA-signed auto-submitting form checkout. Covers the RSA-SHA256 signed `dataString`/`signature` in PHP, Node/TypeScript, Python and Go, the orderCreate redirect, the server-to-server responseUrl callback and signature check, the Merchant Order View API, and troubleshooting.
---

# Koko

Koko is a Sri Lankan Buy-Now-Pay-Later gateway: customer is redirected to Koko, pays in installments, merchant is paid up front. Currency LKR. This skill packs the Koko API Developer Preview v1.05 and Merchant Order View API v1.0 PDFs. The docs have gaps; `references/troubleshooting.md` lists them. Flag them, don't invent.

## How to use this skill
1. Pick the integration from the routing table.
2. Read only the matching reference file(s).
3. For code, start from `references/code-examples.md`.
4. Use `scripts/koko_sign.py` to build `dataString` + `signature` for an order or order view, or verify a Koko callback signature while debugging.
5. Say that facts come from Koko's developer PDFs; contractual or account questions go to Koko merchant support (paykoko.com).

## Routing table
| User needs | Read |
|---|---|
| Create order: form fields, `dataString` order, signing, environments | `references/checkout-api.md` |
| `_returnUrl`, `_cancelUrl`, `_responseUrl` handling, verifying Koko's signature | `references/callbacks.md` |
| Check order status server-side (`orderView`) | `references/order-view-api.md` |
| Code in PHP, Node/TS, Python, Go | `references/code-examples.md` |
| Errors, doc gaps/contradictions, go-live checklist | `references/troubleshooting.md` |

## Core rules
1. **Request is a signed form POST** to `{host}/api/merchants/orderCreate` (`application/x-www-form-urlencoded`), done by the customer's browser via an auto-submitting hidden form. Hosts: `devapi`, `qaapi`, `prodapi` `.paykoko.com`.
2. **Signature:** `dataString` = plain concatenation (no separators) of `_mId, _amount, _currency, _pluginName, _pluginVersion, _returnUrl, _cancelUrl, _orderId, _reference, _firstName, _lastName, _email, _description, api_key, _responseUrl` in exactly that order. `signature = base64(RSA-SHA256 PKCS#1 v1.5 sign(merchant private key, dataString))`. Send both `dataString` and `signature`.
3. **Sign on the server**, amount from your DB, never from the client. The merchant private key never leaves the server; Koko holds the merchant public key.
4. **`_responseUrl` is the source of truth.** Koko POSTs `orderId, trnId, status, desc, signature` server-to-server. Verify `signature` over `orderId+trnId+status` with Koko's public key, then check `orderId`/amount against your DB, then mark paid (idempotently).
5. **`_returnUrl` / `_cancelUrl` are browser redirects**, unsigned (`status` SUCCESS/FAILURE/CANCELED). Use them for UX only; never fulfil an order from them.
6. `_orderId` must be unique per request; `_amount` is a decimal string like `300.00`; `_currency` is `LKR`.
7. **Reconcile** with `orderView` (status PENDING/SUCCESS/FAILED) when the callback is missing.
8. `_pluginName` is `customapi` for custom integrations; `_pluginVersion` is your own version string, and it is part of the signed data.

## Working style
- **Env files:** for several providers, one block per provider under a banner, **two blank lines between blocks**, every var prefixed (`PAYHERE_*`, `ONEPAY_*`, `WEBXPAY_*`, `GENIE_*`, `KOKO_*`), host/base URL first so sandbox vs live is obvious. Only vars the generated code reads; empty placeholders, never real keys. If the user names no provider, include a block for all five. Shape:
  ```
  # ============================ PayHere ============================
  PAYHERE_HOST=https://sandbox.payhere.lk
  PAYHERE_APP_ID=
  PAYHERE_APP_SECRET=


  # ============================ Koko ===============================
  KOKO_HOST=https://qaapi.paykoko.com
  KOKO_MID=
  KOKO_API_KEY=
  KOKO_PRIVATE_KEY_PEM=
  ```
- State assumptions, proceed. Show a full flow: create order > server-side sign > POST form > callback handler (verify, DB check, idempotent update) > orderView fallback.
- Flag documented gaps from `troubleshooting.md`.
- Anything not in the references: say so and suggest Koko support.
- Never put real keys in output; use env vars.

## Bundled files
- `references/`: topic files above
- `scripts/koko_sign.py`: `order`, `view`, `verify` subcommands (needs `pip install cryptography`)
