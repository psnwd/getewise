---
name: gatewise
description: Router for the Gatewise payment gateway skills (PayHere, OnePay, WebXPay, Genie Business, Koko). Use when the user wants to accept payments in Sri Lanka (LKR) but has not named a gateway, asks which gateway or provider to use, compares gateways, wants more than one gateway in the same app, or asks about "Sri Lankan payment gateway", online payments in Sri Lanka, card/Genie/FriMi/eZ Cash/BNPL checkout, or a platform plugin (WooCommerce, Shopify, OpenCart) without picking a provider. Also routes Stripe, PayPal, Paddle and Lemon Squeezy requests to those vendors' own current skills/docs. Picks the right gateway skill from the user's region, features and stack, then hands off to that skill. If the user already named a gateway, use that gateway's own skill instead.
---

# Gatewise router

Pick the gateway, then use that gateway's skill (`payhere`, `onepay`, `webxpay`, `genie`, `koko`). Do not write integration code from this skill; it has no API facts.

## Steps
1. **Region.** All five gateways are Sri Lankan and settle in LKR. If the merchant is outside Sri Lanka or needs other currencies, say none of these fit. If the user names Stripe, PayPal, Paddle or Lemon Squeezy, use the external sources below. Otherwise do not guess another provider.
2. **Features needed**, then **stack** (tables below). Ask at most one question, only if the answer changes the pick. Otherwise recommend and proceed.
3. **Name the pick and why in one or two lines**, then follow that skill. Mention one runner-up only if it is close.
4. **Several gateways in one app:** use each gateway's skill for its own parts and the multi-provider reference bundled in each of those skills for the shared layout, env blocks and idempotent settle.

## Pick by feature
| User needs | Use |
|---|---|
| Plain card checkout, widest docs, mobile SDKs (Android, iOS, React Native, Flutter), most plugins | `payhere` |
| Subscriptions / recurring billing / preapproval | `payhere` (also `genie`, `webxpay` Token V2, `onepay` card on file for merchant-initiated charges) |
| Saved cards, merchant-initiated charges | `genie`, `webxpay` (Token V2), `onepay` (card on file), `payhere` |
| Payment links, no-code invoicing, payouts / settlement | `onepay` |
| Dialog customers, Genie wallet, eZ Cash, UPI, Alipay, JustPay, webhooks | `genie` |
| Many local methods behind one redirect (cards, eZ Cash, mCash, FriMi, Lanka QR, Vishwa, EMI) | `webxpay` |
| Buy-now-pay-later / installments | `koko` |

If two rows fit, prefer the one matching the stack below, then the one with plugins for the user's platform.

## Pick by stack
| Stack | Note |
|---|---|
| Node/TS, Python, PHP/Laravel, Go | all five have code examples |
| Java, Rust, C# | `payhere`, `onepay`, `webxpay`, `genie` only; `koko` has no examples in these (the Koko signing is plain RSA-SHA256, portable but unwritten) |
| WooCommerce | `payhere`, `onepay`, `webxpay`, `genie` |
| Shopify | `payhere`, `onepay`, `webxpay` |
| OpenCart | `payhere`, `genie` |
| Magento, PrestaShop, WHMCS, CS-Cart, Moodle | `payhere` (WHMCS also `onepay`) |
| Mobile app SDKs | `payhere` |

Plugin and stack coverage comes from each skill's description and can lag the vendors; confirm in that skill's `plugins.md` before promising.

## Other providers: fetch, don't embed
Gatewise holds no API facts for these; their docs change often, so use the vendor's own current source and never answer from memory.

| Provider | Source to use |
|---|---|
| Stripe | `npx skills add https://docs.stripe.com` (skills index: https://docs.stripe.com/skills). If Stripe skills/plugin are already installed, use them (e.g. stripe-best-practices, stripe-docs) |
| PayPal | Official https://github.com/paypal/AI-Toolkit. Third party, unvetted: https://mcpmarket.com/tools/skills/paypal-integration-8 |
| Paddle | Official https://github.com/PaddleHQ/paddle-agent-skills |
| Lemon Squeezy | Docs https://docs.lemonsqueezy.com/guides/developer-guide/taking-payments. Third party, unvetted: https://www.skillsdirectory.com/skills/gabrielmoreira-lemon-squeezy and https://github.com/membranedev/application-skills/blob/main/skills/lemon-squeezy/SKILL.md |

Steps: tell the user the provider is outside Gatewise; use an installed official skill if present, else fetch the source above (web fetch) or suggest the install command and let the user run it; read it before writing code. Prefer vendor-owned sources; for third-party ones say they are unvetted and check them against the vendor docs. Shared safety rules (payment-basics, payment-testing, payment-refunds, payment-security-review) still apply.

## Rules
- Never claim fees, limits or approval timelines here; the gateway skill and the vendor decide.
- Do not recommend a gateway the user excluded or already contracted.
- No merchant keys in output; use env vars.
