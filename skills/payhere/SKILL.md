---
name: payhere
description: Expert knowledge of PayHere (payhere.lk), Sri Lanka's payment gateway, covering code integration AND account/support questions. Use whenever the user mentions PayHere, payhere.lk, sandbox.payhere.lk, md5sig, merchant secret, notify_url, payhere.js, "Sri Lankan payment gateway", LKR online payments, or wants to accept card, Genie, FriMi, HelaPay or Vishwa payments in Sri Lanka, even if they never say "PayHere" but describe the Checkout, Recurring, Preapproval, Charging, Retrieval, Subscription Manager, Refund, Authorize or Capture APIs. Covers hash/signature generation and callback verification in Node/TypeScript, Go, Python, PHP/Laravel, Rust, Java and C#; JS and mobile SDKs (Android, iOS, React Native, Flutter); WooCommerce, OpenCart, Shopify, Magento, PrestaShop, WHMCS, CS-Cart, Moodle plugins; sandbox test cards; subscriptions, tokenized auto-charging, hold-on-card; plans, fees, limits, payouts, refunds, account approval; and debugging errors like "Unauthorized payment request" or PH-0022.
---

# PayHere

PayHere (PayHere (Pvt) Ltd) is a CBSL-approved payment gateway for Sri Lankan businesses. This skill packs its public knowledge base (support.payhere.lk, read Oct 2026) into focused reference files so you can write correct integrations and answer account questions without guessing.

## How to use this skill
1. Identify what the user is doing, using the routing table.
2. Read only the matching reference file(s); they hold exact parameter names, URLs and gotchas.
3. When writing code, start from `references/code-examples.md` (signing/verification) and `references/code-rest-api.md` (OAuth REST calls); adapt to the user's stack and framework.
4. Use `scripts/payhere_sign.py` to compute or check a hash/md5sig when debugging a mismatch.
5. Money, plan, fee and policy facts can change. State that the figures come from PayHere's docs as of late 2026 and point to support@payhere.lk / the 24x7 helpline (0115 339 339) for anything contractual.

## Routing table
| User needs | Read |
|---|---|
| One-time web payment (redirect form), hash, notify_url, md5sig | `references/checkout-api.md` |
| Subscriptions, recurring billing, preapproval/tokenization | `references/recurring-preapproval.md` |
| OAuth token, Charging, Retrieval, Subscription Manager, Refund, Capture, Authorize APIs | `references/merchant-api.md` |
| Popup/onsite checkout on a website (`payhere.js`) | `references/js-sdk-onsite.md` |
| Android, iOS, React Native, Flutter apps | `references/mobile-sdks.md` |
| WooCommerce / Shopify / OpenCart / Magento / PrestaShop / WHMCS / CS-Cart / Moodle / ShopHere | `references/plugins.md` |
| Test cards, sandbox vs live | `references/sandbox-testing.md` |
| Code in Node/TS, Go, Python, PHP/Laravel, Rust, Java, C# | `references/code-examples.md`, `references/code-rest-api.md` |
| Applying for an account, plans/fees/limits, payouts, USD payouts, refunds policy, Links/Buttons, required policy pages | `references/account-business.md` |
| Any error, mismatch, "why isn't notify firing", security review, doc contradictions | `references/troubleshooting.md` |

## Core rules (the things most integrations get wrong)
1. **Server-side hash.** `hash = UPPER(md5(merchant_id + order_id + amount + currency + UPPER(md5(merchant_secret))))`, amount as `1000.00` (2 decimals, no commas). Never compute it in the browser or app; it would expose the secret. (Required since 2023-01-16.)
2. **Verify every notification.** PayHere POSTs form-encoded data to `notify_url`. Recompute `md5sig = UPPER(md5(merchant_id + order_id + payhere_amount + payhere_currency + status_code + UPPER(md5(secret))))` from the received strings, constant-time compare, then check `status_code` (2 success; for Authorize 3 = authorized), and check amount/currency/order against your DB. Redirects to `return_url` and JS-SDK `onCompleted` are not proof of payment.
3. **Per-domain secrets.** Merchant ID is per account; Merchant Secret is per registered domain/app (approval up to ~24 h). Sandbox and live are fully separate (different credentials, cannot be converted).
4. **Right URLs.** Live checkout is `https://www.payhere.lk/pay/checkout` (keep `www`, else PH-0022); sandbox is `https://sandbox.payhere.lk/pay/checkout`. Preapprove and authorize use `/pay/preapprove` and `/pay/authorize`. REST APIs live under `/merchant/v1/`.
5. **notify_url must be public.** localhost never works; tunnel for dev. Exempt the route from CSRF/auth; parse form bodies, not JSON.
6. **REST API auth** = API key (App ID/Secret) > Basic auth > Bearer token (~10 min) ; max 20 requests / 10 s; live needs whitelisted domain and server IP (email support@payhere.lk). Keep App Secret off clients.
7. **Plan gates features.** Recurring needs PLUS or higher; automated charging (preapproval + Charging API) needs PREMIUM; LITE is one-time LKR/USD only. Check `account-business.md` before designing around a feature.
8. **Hash exceptions.** Preapproval with no amount hashes `10.00` (LKR) / `0.51` (other currencies); recurring with a future `recurring_start_date` hashes `10.00` (LKR) / `0.50` (other) while still submitting the real amount.

## Working style
- When the user's goal is ambiguous (redirect vs popup vs mobile, one-time vs subscription vs on-demand), pick from the routing table by asking one short question or by stating the assumption and proceeding.
- Prefer showing a complete minimal flow: create order > server hash > form/popup > notify handler with verification > idempotent DB update > status page from DB.
- If the user's stack is not one of the seven covered, adapt the algorithm (MD5, uppercase hex) and say which part you adapted.
- Flag documented contradictions (listed in `troubleshooting.md` section 5) rather than silently picking one.
- If something isn't in the references, say so and suggest confirming with PayHere support rather than inventing parameters.
- Never put real merchant secrets, App Secrets, or customer tokens into code you output; use env vars.

## Bundled files
- `references/`: the topic files above
- `scripts/payhere_sign.py`: CLI to generate the request hash (including preapproval and future-start variants) and verify a notification md5sig
