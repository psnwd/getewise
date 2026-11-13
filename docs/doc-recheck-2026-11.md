# Doc re-check, November 2026

Every gateway skill was re-read against its vendor's live documentation on **13 November 2026**. This page records what changed, what was resolved, and what is still genuinely unpublished — so the next pass knows where to start. It is not part of any installed skill.

Method: the public docs plus, where the docs are thin, official sample projects and plugin source (WebXPay and Koko), the Stoplight spec mock and the official PHP SDK (Genie), and the archived `developer.onepay.lk` site plus the npm/Laravel SDKs (OnePay). No merchant account was used and no live payment was made.

## What the pass fixed

| Skill | Notable corrections |
|---|---|
| [PayHere](../skills/payhere/SKILL.md) | Authorize success is `3` and the same page's PHP sample still tests `== 2`; PayHere sends `notify_url` **once** and never retries (so reconciliation is mandatory, not optional); the permission split (`Settings > API Keys` + Automated Charging vs `Settings > Business Apps` + Payment Capture); partial refunds remain contradictory; add-on fees (premium brands +0.5%, cross-border +1.0%, HelaPay 1.99%) |
| [OnePay](../skills/onepay/SKILL.md) | **There is no sandbox host** — sandbox is an app mode on `api.onepay.lk`; the create response is `data.gateway.redirect_url` + `data.ipg_transaction_id`; hash is lowercase hex over `toFixed(2)`; auth is a raw `AppToken`, not Bearer; a full subscription API exists in the archived docs |
| [WebXPay](../skills/webxpay/SKILL.md) | **The return signature is RSA-PSS/SHA-1, not PKCS#1 v1.5 recovery** — the old PHP sample is wrong and every real response fails it; the response has eight fields including two amounts; no public refund API (six independent checks); published test cards and staging MIDs |
| [Genie Business](../skills/genie/SKILL.md) | Get Transaction is `/public/transactions/{id}` (the webhook sample's `/public/v2/...` is a typo); `expiryDate` is unsatisfiable in the spec; `paymentType`/`recurringFrequency` enumerations; customer, token and webhook endpoints documented; fees and settlement are now public |
| [Koko](../skills/koko/SKILL.md) | Callback is **RSA-SHA256/PKCS#1 v1.5** over `orderId+trnId+status` (no `desc`), and may arrive as JSON or form; no auth header and `api_key` is plaintext; error envelope and observed codes; refunds are portal-only and full-only; ~12% commission |

Code changes: `skills/webxpay/scripts/webxpay_crypto.py` now verifies PSS first with the legacy recovery path as a fallback, and `scripts/verify.py` checks both (PSS accepted, legacy accepted, forged rejected). The WebXPay verification snippets in `skills/webxpay/references/code-examples.md` were run against a real captured staging response in Node, Python, Go, Java, C# and Rust.

## Still unpublished (do not guess these)

- **PayHere**: whether partial refunds actually work; the exact dashboard label today; chargeback contest SLA; notify source IPs; plan gating for Hold on Card; 3DS/SCA policy. Notify-retry behaviour rests on a PayHere FAQ answer relayed through a community issue, not the KB.
- **OnePay**: payment-link create body; how the Callback Token is transmitted; numeric rate limits and 429 body; callback status values beyond `1`; callback retry policy; min/max amount; which test card approves or declines; 5xx behaviour.
- **WebXPay**: which RSA padding the gateway accepts for `payment` (docs/samples split v1.5 vs OAEP); any refund API; gateway id `93`; per-gateway return codes; amount ceilings; `enc_method` semantics.
- **Genie**: the `expiryDate` value the server actually accepts; webhook timestamp format/tolerance/retry policy; refund amount unit; Create Customer body; Charge Stored Token absolute URL; capture and FX endpoints; test cards.
- **Koko**: `orderView` signed string; whether `_mobileNo` is required; checkout expiry, min/max, partial capture, cancel API, callback retry schedule; no public docs site or changelog exists.

## Sources

PayHere: support.payhere.lk KB (Authorize/Refund/Capture/Recurring/Retrieval pages), payhere.lk fees and legal pages, PayHere API FAQ relayed in laravel-payhere issue #29.
OnePay: docs.onepay.lk (payment API, payment link, items, errors, user guide, test cards), archived developer.onepay.lk, `onepay-sdk` 1.0.3, `onepay-srilanka/onepay-laravel`, `onepayjs/onepayv2.js`.
WebXPay: developers.webxpay.com, integration.webxpay.com (Token v2.2 guide, MIDs, test cards), official sample zips (PHP/Node/.NET/JS), WooCommerce/Magento/WHMCS plugins.
Genie: geniebusiness.stoplight.io docs + Prism mock, `geniebusiness/geniebiz-connect-php`, PomeloPay Node SDK, geniebusiness.lk pricing and developer pages.
Koko: Koko WooCommerce plugin 3.0.4 source, kokolk.freshdesk.com KB, paykoko.com/business, read-only QA API probes.
