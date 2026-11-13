---
name: onepay
description: Expert knowledge of OnePay (onepay.lk, docs.onepay.lk), the Sri Lankan payment gateway, covering code integration AND account/support questions. Use whenever the user mentions OnePay, onepay.lk, api.onepay.lk, /v3/checkout/link, onepay_transaction_id, ipg_transaction_id, hash_salt, app_token, onePayData, onePaySuccess, @onepaynpm/onepay-sdk, or wants card, Frimi, QPlus, HelaPay or Google Pay payments in Sri Lanka through OnePay, even if they only describe its redirect checkout, Payment Link, Card on File (customer tokenizer), Items, Refund, Payouts/settlement or subscription APIs. Covers the SHA-256 request hash and callback/status verification in Node/TypeScript, Go, Python, PHP/Laravel, Rust, Java and C#; OnePay JS and the npm SDK; WordPress/WooCommerce, Shopify, WHMCS and Zoho plugins; test cards, currencies, settlement and refunds; and 400/401/429 errors.
---

# OnePay

OnePay (onepay.lk) is a Sri Lankan payment gateway (cards, Frimi, QPlus, HelaPay, Google Pay; 10 currencies, settled in LKR). API v3 at `https://api.onepay.lk`. This skill packs the public docs (docs.onepay.lk, read Oct 2026 and re-checked Nov 2026) into focused references. The docs are thin in places; `references/troubleshooting.md` lists the gaps and contradictions. Flag them, don't paper over them.

## How to use this skill
1. Pick the task from the routing table.
2. Read only the matching reference file(s).
3. For code, start from `references/code-examples.md` and adapt to the user's stack.
4. Use `scripts/onepay_sign.py` to compute or check a request hash.
5. Say that fees, limits and policies come from OnePay's docs as of late 2026, and send contractual questions to the user's OnePay Relationship Officer / support (Discord, onepay.lk/contact-us).

## Routing table
| User needs | Read |
|---|---|
| Redirect checkout, hash, create transaction, status check, callback | `references/payment-api.md` |
| Popup/overlay checkout (`onePayData`), npm SDK | `references/js-sdk.md` |
| Subscriptions / recurring API (`/v3/subscription/`, trials, manual retry) | `references/subscriptions.md` |
| Payment Links, Items | `references/links-items.md` |
| Card on File / tokenized auto-charging | `references/card-on-file.md` |
| Refunds, payouts, settlement, fees | `references/refund-payouts.md` |
| Test cards, sandbox vs live, currencies, payment methods | `references/sandbox-currencies.md` |
| WordPress/WooCommerce, Shopify, WHMCS, Zoho | `references/plugins.md` |
| Code in Node/TS, Go, Python, PHP/Laravel, Rust, Java, C# | `references/code-examples.md` |
| Any error, 401/400/429, "what does status 1 mean", doc gaps | `references/troubleshooting.md` |
| App uses several gateways: env layout, callback routes, shared idempotent settle | `references/multi-provider.md` |

## Core rules
1. **Two auth styles.** Payment API (create transaction) signs the body with `hash = SHA256(app_id + currency + amount + HASH_SALT)` (plain concatenation, lowercase 64-char hex; amount `toFixed(2)`, currency uppercased). Everything else (Refund, Payouts, Payment Link, Card on File, Items, Subscriptions) uses the App Token in the `Authorization` header — raw, not `Bearer` (the API advertises `WWW-Authenticate: AppToken`). Keep `HASH_SALT` and App Token server-side.
2. **Create transaction** = `POST /v3/checkout/link/`, send the App Token in `Authorization` too, then redirect the customer **in the same window** to `data.gateway.redirect_url` from the response.
3. **Never trust the return URL.** After the redirect, or on a callback, confirm with `POST /v3/transaction/status/` (`app_id` + `onepay_transaction_id`) and check `data.status == true` (nested), amount and currency against your order.
4. **Callbacks carry no signature in the body.** The JSON callback (`transaction_id`, `status`, `status_message`, `additional_data`) has no documented signature, so treat it as a trigger and verify through the status API. A per-app **Callback Token** and **CIDR allowlist** can be configured in the portal, but how the token is transmitted is undocumented. Callback URL is set in the portal's APP section; must accept POST JSON and return 200.
5. **IDs differ by name.** Create response gives `ipg_transaction_id`; Status/Refund/Payouts call it `onepay_transaction_id`; callbacks call it `transaction_id` — the same value under three labels. Store it at checkout.
6. **Sandbox is an app mode, not a host.** Same `https://api.onepay.lk`, app in `On Development` state with its own App ID/Token/Hash Salt. Refunds work only on live transactions.
7. **Rate limit** per App ID; 429 means back off (the docs say "per second"); retry with exponential backoff.
8. **Customer phone** must be E.164 (`+94771234567`); `transaction_redirect_url` must be HTTPS.

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
- If the goal is ambiguous (redirect vs overlay vs link vs recurring), state the assumption and proceed.
- Show a full flow: create order > server hash > create transaction > redirect > callback + status verification > idempotent DB update.
- Flag contradictions listed in `troubleshooting.md` instead of silently choosing.
- Anything not in the references: say so and suggest confirming with OnePay rather than inventing parameters.
- Secrets from env vars, never in code you output.

## Bundled files
- `references/`: topic files above
- `scripts/onepay_sign.py`: CLI to compute/verify the request hash
