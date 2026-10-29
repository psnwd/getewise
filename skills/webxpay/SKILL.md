---
name: webxpay
description: Expert knowledge of WEBXPAY (webxpay.com, developers.webxpay.com), a Sri Lankan payment gateway, covering code integration AND account/support questions. Use whenever the user mentions WebXPay or WEBXPAY, webxpay.com, stagingxpay.info, route=checkout/billing, payment_gateway_id, multiple_payment_gateway_ids, custom_fields, enc_method, Bank MID, "Token V2", "Pay From Token", or wants to take card, eZ Cash, mCash, FriMi, Genie, Lanka QR, Sampath Vishwa or EMI/installment payments in Sri Lanka through WebXPay, even if they only describe an RSA-encrypted redirect checkout. Covers the RSA-encrypted `payment` parameter and signature check in PHP, Node/TypeScript, Python, Go, Java, Rust and C#; the redirect integration, Token V2 card-saving/MIT API, transaction retrieval, gateway IDs and MIDs; Shopify and WooCommerce plugins; and error codes 401-424.
---

# WEBXPAY

WEBXPAY is a Sri Lankan payment aggregator: one checkout across bank card gateways (Commercial, Cargills, HNB, Seylan, Sampath, NTB Amex...), wallets (eZ Cash, mCash, FriMi, Genie, DFCC Wallet), Lanka QR and EMI plans. Currencies LKR, USD, GBP, AUD. This skill packs developers.webxpay.com (read Oct 2026). The docs are partly screenshots and have gaps; `references/troubleshooting.md` lists them. Flag them, don't invent.

## How to use this skill
1. Pick the integration from the routing table.
2. Read only the matching reference file(s).
3. For code, start from `references/code-examples.md`.
4. Use `scripts/webxpay_crypto.py` to build the `payment` value or check a response `payment` + `signature` while debugging.
5. Say that facts come from WebXPay's developer docs as of late 2026; contractual or account questions go to WebXPay support (webxpay.com, merchant.webxpay.com).

## Routing table
| User needs | Read |
|---|---|
| Redirect checkout (HTML form POST), encrypted `payment`, return URL, response check | `references/redirect-integration.md` |
| Saved cards, CIT/MIT charges, recurring, 3DS (Token V2 `/api/v2/merchant/...`) | `references/token-v2-api.md` |
| Merchant login tokens, transaction lookup by order ref | `references/merchant-retrieval-api.md` |
| Which `payment_gateway_id`, EMI IDs, staging/live Bank MIDs | `references/gateways-mids.md` |
| Shopify, WooCommerce (Magento/OpenCart/PrestaShop/WHMCS are listed but undocumented) | `references/plugins.md` |
| Code in PHP, Node/TS, Python, Go, Java, Rust, C# | `references/code-examples.md` |
| Any error code, "why declined", doc gaps/contradictions | `references/troubleshooting.md` |

## Core rules
1. **No MD5/SHA request hash.** Redirect checkout sends `payment = base64(RSA_PKCS1v15_encrypt(WEBXPAY_PUBLIC_KEY, "unique_order_id|total_amount"))`, e.g. `12001|2567.50`. The public key is in Dashboard > Settings > Integration Information (generated after activation). The `secret_key` (same page) goes in the POST too.
2. **Build `payment` on the server** and take the amount from your DB, never from the client. The sample HTML shows `secret_key` in a hidden field: that is documented behavior, but it means the key is visible to the browser; tell the user, and keep the encryption step server-side.
3. **Staging vs live:** live `https://webxpay.com/index.php?route=checkout/billing`, staging `https://stagingxpay.info/index.php?route=checkout/billing` (separate keys/MIDs).
4. **Return URL** is set in Dashboard > Settings > Website Integration (no `return_url` param). WebXPay redirects the browser to it with POST fields `payment`, `signature`, `custom_fields`. Base64-decode `payment` and `signature`; RSA public-decrypt the signature with the same public key (PKCS#1 v1.5, i.e. signature recovery, not `openssl_verify`) and require it to equal the decoded `payment`. Then split `payment` on `|`: `order_id|order_ref|datetime|status_code|comment|gateway_id`. Success = status `0` or `00`; `15` declined (codes vary by gateway).
5. **The return is browser-borne**, so a customer can hit it directly; always check the signature, then check order id/amount against your DB, and consider confirming through the Transaction Retrieval API. No server-to-server webhook is documented for redirect checkout.
6. **Currency and limits:** `process_currency` is LKR/USD/GBP/AUD; amount must be ≥ 1; per-currency maximums exist (errors 410/411).
7. **Gateway pre-selection:** `payment_gateway_id` (one) or `multiple_payment_gateway_ids` (pipe-separated, e.g. `40|44|96`) skips the selection page.
8. **Token V2** (saved cards, MIT) is a different, bearer-token JSON API with hosts and `bankMID`s issued at onboarding; don't mix it with the redirect form.

## Working style
- If the goal is ambiguous (redirect vs saved cards/recurring), state the assumption and proceed.
- Show a full flow: create order > server-side encrypt > POST form > return handler (decode, signature check, DB amount check, idempotent update).
- Flag documented contradictions from `troubleshooting.md`.
- Anything not in the references: say so and suggest WebXPay support.
- Never put real keys/secrets in output; use env vars.

## Bundled files
- `references/`: topic files above
- `scripts/webxpay_crypto.py`: build `payment`, verify response `payment`+`signature` (needs `pip install cryptography`)
