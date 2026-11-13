---
name: payment-testing
description: How to test a Sri Lankan payment gateway integration before going live - sandbox hosts, test cards, what is and is not simulable, a scenario checklist (success, failure, cancel, duplicate callback, tampered amount, bad signature, lost callback), and tunnelling callbacks to localhost. Use when the user asks "how do I test this", "where are the test cards", "sandbox vs live", "my callback does not arrive locally", "how do I simulate a failed payment or webhook", or wants a go-live test plan for PayHere, OnePay, WebXPay, Genie Business or Koko. For gateway signatures, fields and endpoints use that gateway's own skill alongside this one; for general safety rules see payment-basics.
---

# Payment testing

Per-gateway test facts are below; the gateway skill holds the details. Where a gateway publishes nothing, say so and send the user to the gateway. **Never invent test card numbers or sandbox hosts.**

## What each gateway gives you
| Gateway | Sandbox | Test cards | Gotchas |
|---|---|---|---|
| PayHere | `sandbox.payhere.lk` (checkout, `/merchant/v1/` REST); separate merchant ID and secret, cannot convert to live. No sandbox merchant ID is published; the token response shows `"scope": "SANDBOX"` | Published, with outcomes: success, insufficient funds, limit exceeded, do not honor, network error (Visa/MC/AMEX). Unlisted cards fail. See the payhere skill's sandbox-testing reference | REST "Access denied for the domain": allow `*` on the sandbox key. `notify_url` cannot be localhost. PayHere sends a notify **once** and does not redeliver (PayHere FAQ relayed through a community issue) — so test the reconciliation sweep. Recurring fires ~1 min after authorization; `AUTHORIZE` charge type and some recurring options are live-only |
| OnePay | **No separate sandbox host.** Same `https://api.onepay.lk`; sandbox is an app in `On Development` state with its own App ID/Token/Hash Salt | Four published cards, but the page does not say which approve or decline. See the onepay skill's sandbox-currencies reference | **Refunds do not work on sandbox transactions**; 3DS is mandatory (no 2D); test refunds only with a small live payment |
| WebXPay | Staging `stagingxpay.info`; called "Sandbox" in the Token v2.2 guide | **Yes — six cards**, with and without 3DS, in the Token v2.2 guide. See the webxpay skill's gateways-mids reference | Staging MIDs (`TESTWEBXPATOKLKR`…), staging `secret_key`s and public keys ship in the official samples. Gateway IDs are per merchant (errors 414/415) |
| Genie Business | UAT environment with its own API key; a key from one environment fails on the other | None published; the "Test API Keys" file linked from geniebusiness.lk/developer now 404s — ask genie.integration@dialog.lk | A "test payment provider" can be enabled on production credentials: live account, no payout, `isTest` on the object. Keep those out of real reports |
| Koko | QA environment `qaapi.paykoko.com`, own `_mId`, `api_key` and key pair; `devapi` is a third registry that QA keys do not work on | None from Koko. A third-party demo publishes a QA `_mId`/`api_key` (may rotate) | "Works in QA, fails in prod" is usually prod credentials and Koko's prod public key. `_pluginName`/`_pluginVersion` must match the registration Koko holds for the MID |

## Setup rules
1. One env block per provider with its own host/base URL var, so one can go live while others stay on sandbox (see the multi-provider reference in each gateway skill).
2. Sandbox credentials never in live config and the reverse; never commit either.
3. Callbacks need a **public HTTPS URL**: use a tunnel (cloudflared, ngrok) for local work. Re-register the URL when the tunnel changes.
4. Test with the **same code path** as production. A "skip signature in dev" flag is how forged callbacks ship.

## Scenario checklist
Run each; tick only what you actually saw.
1. **Success:** callback verified, order paid once, fulfilment once.
2. **Failure** (declined card where the gateway has one): order stays unpaid, customer sees a retry path.
3. **Cancel:** return page works, order not paid, no stuck stock.
4. **Duplicate callback:** replay the exact request; nothing changes the second time.
5. **Out of order:** failure callback after success must not undo `paid`.
6. **Bad signature:** flip one byte; expect 400 and no state change.
7. **Tampered amount:** callback with a different amount/currency than your DB; expect rejection.
8. **Return page before callback / without callback:** order is not marked paid from the browser alone.
9. **Callback never arrives:** drop it; the reconciliation job settles the order through the same function.
10. **Timeout on your outbound call:** look up before retrying, never blind-retry a charge.
11. **Refund** (see payment-refunds): only where the gateway allows it in the environment you test in.
12. **Go-live swap:** live host and credentials, one small real payment, confirm it settles.

## Faking a callback
Use the gateway skill's signing helper (`scripts/`) to build a valid signed request against your local endpoint; flip a field to build the bad-signature case. Do not hand-roll a different signing path in tests.

## Rules
- State what could not be tested (no cards, no sandbox refund) rather than implying coverage.
- Keep test amounts small; on a gateway without a published sandbox, "sandbox" may mean live money. Confirm first.
- Live-only features (PayHere `AUTHORIZE`, OnePay refunds) get a single supervised live test, not a skipped one.
