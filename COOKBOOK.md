# Gatewise cookbook

Selected workflows across the Gatewise skills. Each recipe is what you say to the agent, what the agent does, and the rules it must not get wrong.

Most finish with runnable code. #8 finishes with a report and a test checklist, #10 with a packaged skill. None of them need a live merchant account to start: sandbox or UAT credentials are enough, and the steps that must run live are called out.

**Before you start**

- Install once ([README](README.md#install-in-2-minutes) or [INSTALL_FOR_AGENTS.md](INSTALL_FOR_AGENTS.md)).
- Never paste a real merchant secret, App Secret or private key into chat. Use env vars and placeholders; the skills are written to expect that.
- Facts come from each gateway's public docs (read October 2026, re-checked 13 November 2026). Where the docs are silent or contradict themselves, the agent says so instead of guessing.

---

## Recipe 1 — A PayHere checkout that cannot be fooled

**What it does:** Adds server-side hashing, a verifying `notify_url` handler and a reconciliation job to an existing store, so a browser redirect can never mark an order paid.

**Why this is useful:** This is the exact spot where integrations go wrong. The hash is easy; the hard part is refusing to trust the return page, and making "mark paid" safe to run twice.

**What you say:**

```
Add PayHere checkout to my Express app. Orders live in Postgres, prices in LKR.
Nothing may be marked paid from the return page — only from the notification.
```

**What the agent does:**

1. **Reads the right notes** ([payhere skill](skills/payhere/SKILL.md)): `references/checkout-api.md`, `references/code-examples.md`, `references/merchant-api.md`, plus `payment-basics` for the callback order of operations.
2. **Builds the request hash on the server** (`UPPER(md5(merchant_id + order_id + amount + currency + UPPER(md5(secret))))`, amount `4500.00`):

   ```bash
   python skills/payhere/scripts/payhere_sign.py hash \
     --merchant-id 1211149 --order-id ORDER-1042 --amount 4500 --currency LKR
   ```

   It reads `PAYHERE_SECRET` from the environment, not the command line.
3. **Writes the checkout form** to `https://sandbox.payhere.lk/pay/checkout` (sandbox) or `https://www.payhere.lk/pay/checkout` (live), with `notify_url`, `return_url` and `cancel_url`.
4. **Writes the notify handler** in this order: raw form body → recompute `md5sig` → constant-time compare (`crypto.timingSafeEqual`) → load the order by *your* id → check amount, currency and merchant id against the DB → insert `(provider, gateway_ref)` under a unique constraint → fulfil only if the insert was new → 200.
5. **Adds a reconciliation job** that pulls `pending` orders older than N minutes through the Retrieval API and settles them through the same function.
6. **Replays the failure cases:** duplicate notify, notify before return, one flipped byte in `md5sig` (expect 400 and no state change).

**Tips:**

- `notify_url` must be public HTTPS. `localhost` never works; use cloudflared or ngrok and re-register the URL when the tunnel changes.
- Sandbox and live are separate accounts with separate credentials. They cannot be converted, so keep two env blocks.
- Keep `www` in the live checkout URL. Dropping it returns PH-0022.
- Recurring needs a PLUS plan, automated charging needs PREMIUM. The agent checks `account-business.md` before designing around either.

---

## Recipe 2 — Koko BNPL with a signed form and a checked callback

**What it does:** Lets Sri Lankan customers pay in installments through Koko, with the `dataString`/`signature` form built server-side and `_responseUrl` verified before the order is marked paid.

**Why this is useful:** Koko signs a plain concatenation in a fixed, non-alphabetical field order with RSA-SHA256. Get the order wrong and the request is rejected with no useful error; get the callback wrong and you ship goods on an unsigned redirect.

**What you say:**

```
Let customers pay in installments with Koko on my Laravel store.
Order 53, LKR 12,500, two products. Build the form on the server.
```

**What the agent does:**

1. Reads [koko skill](skills/koko/SKILL.md) → `references/checkout-api.md`, `references/callbacks.md`, `references/order-view-api.md`, `references/code-examples.md`.
2. **Signs the order** with the merchant private key over the documented field order (`_mId, _amount, _currency, _pluginName, _pluginVersion, _returnUrl, _cancelUrl, _orderId, _reference, _firstName, _lastName, _email, _description, api_key, _responseUrl`):

   ```bash
   python skills/koko/scripts/koko_sign.py order \
     --key merchant_private.pem --mid "$KOKO_MID" --amount 12500.00 --currency LKR \
     --plugin-name customapi --plugin-version 1.0.0 \
     --return-url https://shop.lk/return --cancel-url https://shop.lk/cancel \
     --order-id 53 --reference 53 --first-name John --last-name Doe \
     --email j@shop.lk --description "2 products" \
     --api-key "$KOKO_API_KEY" --response-url https://shop.lk/koko/response
   ```

3. **Renders an auto-submitting form** (POST, `application/x-www-form-urlencoded`) to `https://qaapi.paykoko.com/api/merchants/orderCreate` or `https://prodapi.paykoko.com/...`, containing `dataString` and `signature`.
4. **Writes the `_responseUrl` handler:** verify `signature` over `orderId + trnId + status` with Koko's public key, check `orderId` and amount against the DB, then settle idempotently.
5. **Treats `_returnUrl` / `_cancelUrl` as UX only.** They are unsigned browser redirects.
6. **Adds an `orderView` reconciliation job** for missing callbacks, and a test that flips `SUCCESS` to `FAILED` in the callback (expect rejection).

**Tips:**

- `_pluginName` is `customapi` for custom integrations. `_pluginVersion` is your own string and it is part of the signed data, so never change it between signing and posting.
- `_orderId` must be unique per request. Reusing it is the usual cause of "duplicate order" in Koko.
- The private key never leaves the server. Koko holds the public half.
- QA and production use different `_mId`/`api_key` **and** different Koko public keys. "Works in QA, fails in prod" is almost always one of those three.

---

## Recipe 3 — One WebXPay redirect for many payment methods

**What it does:** Adds WebXPay so customers can pick card, eZ Cash, mCash, FriMi, Genie, Lanka QR, Vishwa or EMI from one encrypted checkout, with the browser-borne return properly verified.

**Why this is useful:** WebXPay has no request hash at all. It RSA-encrypts `order|amount` into a `payment` field, and verifying the return means checking an **RSA-PSS/SHA-1 signature** over the decoded `payment` bytes — not the `openssl_verify` call you would reach for on a hash, and not the old PHP sample's public-decrypt recovery, which fails on current responses.

**What you say:**

```
Add WebXPay checkout to my Go store. Show Lanka QR and FriMi only.
Check the response properly — the return is a plain browser POST.
```

**What the agent does:**

1. Reads [webxpay skill](skills/webxpay/SKILL.md) → `references/redirect-integration.md`, `references/gateways-mids.md`, `references/code-examples.md`.
2. **Builds `payment` server-side** with the public key from Dashboard → Settings → Integration Information:

   ```bash
   python skills/webxpay/scripts/webxpay_crypto.py build \
     --key webxpay_public.pem --order 12001 --amount 2567.5
   ```

3. **Restricts the methods** with `payment_gateway_id` (one) or `multiple_payment_gateway_ids` (pipe-separated, e.g. `40|44|96`), which skips the selection page.
4. **Writes the return handler:** base64-decode `payment` and `signature`, verify the signature as RSA-PSS/SHA-1 over the decoded `payment` bytes (constant-time, PKCS#1 v1.5 recovery only as a legacy fallback), then split on `|` into `order_id|order_ref|datetime|status_code|comment|gateway_id` — plus `requested_amount|transaction_amount` when the response carries them. Success is `0` or `00`; `15` is declined and codes vary by gateway.
5. **Checks the order against the DB** and confirms through the Transaction Retrieval API, because the customer can POST to that return URL directly.
6. **Tests:** forged `payment`, wrong key, and a declined status that must not mark anything paid.

**Tips:**

- There is no documented server-to-server webhook for redirect checkout. Retrieval API or reconciliation is the safety net.
- `secret_key` in the form is documented behavior, but it means the key is visible in the browser. Say so before shipping, and keep the encryption step on the server.
- Error 414/415 usually means the gateway ID is not enabled for *your* merchant. Error 410/411 is the per-currency maximum.
- Staging is `stagingxpay.info`, never called sandbox, with separate keys and bank MIDs.
- Token V2 (saved cards, merchant-initiated charges) is a different bearer-token JSON API. Do not mix it into the redirect form.

---

## Recipe 4 — A Genie Business webhook you can trust

**What it does:** Hosted page for cards, Genie wallet, eZ Cash, UPI, Alipay and JustPay, with `X-Signature` verification and a mandatory Get Transaction check before fulfilment.

**Why this is useful:** Genie's webhook signature covers a nonce, a timestamp and your API key — **not the body**. Most integrations verify the header and then trust the JSON, which is the wrong conclusion.

**What you say:**

```
Add Genie Business hosted checkout to my Next.js app: cards and Genie wallet.
I want a webhook handler I can actually trust before shipping the order.
```

**What the agent does:**

1. Reads [genie skill](skills/genie/SKILL.md) → `references/transaction-api.md`, `references/webhooks.md`, `references/states-refunds.md`, `references/code-examples.md`.
2. **Creates the transaction** with `POST /public/v2/transactions`, amount as an integer in minor units (`125000` = LKR 1,250.00), and stores the returned `id` plus your own `localId`.
3. **Redirects to the returned `url`**, with `shortUrl` as the share link.
4. **Verifies the webhook:** `X-Signature = SHA256(X-Signature-Nonce + X-Signature-Timestamp + apiKey)`, hex, constant-time:

   ```bash
   python skills/genie/scripts/genie_webhook.py verify \
     --nonce "$NONCE" --timestamp "$TS" --signature "$SIG"
   ```

5. **Then re-queries the API.** Get Transaction is mandatory: compare `state == "CONFIRMED"`, amount, currency and `localId` before settling. The webhook is a trigger, not proof.
6. **Writes the idempotent settle** and a status page that reads from your DB, not from the callback body.

**Tips:**

- Auth is the raw API key in `Authorization`, no `Bearer`, server-side only. UAT and production keys fail on each other.
- Never send `10.00`. Genie rejects floats; `amountAsDecimal` in the response is for display.
- Card on file needs a Customer and `card_payments`; MIT recurring and the scheduler are off by default and must be enabled by Genie support.
- Refunds create a *new* transaction (`REFUND_REQUESTED` → `REFUNDED`); the original stays `CONFIRMED`.

---

## Recipe 5 — OnePay checkout, verified through the status API

**What it does:** Redirect checkout with the SHA-256 body hash, then confirmation through the status API, because OnePay callbacks are unsigned.

**Why this is useful:** OnePay's callback is a JSON POST with no documented signature. Teams that treat it as proof of payment are one forged request away from free goods.

**What you say:**

```
Add OnePay checkout to my Rust/Axum service. Cards and Google Pay.
Verify the payment server-side — don't trust the callback.
```

**What the agent does:**

1. Reads [onepay skill](skills/onepay/SKILL.md) → `references/payment-api.md`, `references/js-sdk.md`, `references/sandbox-currencies.md`, `references/code-examples.md`.
2. **Computes the body hash** `SHA256(app_id + currency + amount + HASH_SALT)`, lowercase hex, amount normalised to two decimals:

   ```bash
   ONEPAY_SALT="$ONEPAY_SALT" python skills/onepay/scripts/onepay_sign.py hash \
     --app-id "$ONEPAY_APP_ID" --currency LKR --amount 1500
   ```

3. **Creates the transaction** with `POST /v3/checkout/link/`, sending the App Token in `Authorization`, then redirects in the same window to `redirect_url`.
4. **Confirms with `POST /v3/transaction/status/`** (`app_id` + `onepay_transaction_id`) and requires `status == true` plus matching amount and currency before settling.
5. **Stores the transaction id once** and maps the three names: `ipg_transaction_id` on create, `onepay_transaction_id` on status/refund, `transaction_id` in callbacks.
6. **Handles 429** with exponential backoff, and E.164 phone numbers (`+94771234567`).

**Tips:**

- Refunds work only on live transactions. Plan one small supervised live test; sandbox refunds are rejected.
- `transaction_redirect_url` must be HTTPS.
- The callback is still useful as a fast trigger — just never as proof.
- For popup checkout instead of redirect, the agent switches to the JS SDK (`onePayData`, npm SDK) and keeps the same status check.

---

## Recipe 6 — Saved cards and recurring, with the gateway chosen for you

**What it does:** Picks the right gateway for tokenized recurring billing or merchant-initiated charges, then implements it. Plan gates and enablement differ enough that guessing costs a week.

**What you say:**

```
I need monthly billing on saved cards without asking the customer again.
I'm on WooCommerce and already have a PayHere account.
```

**What the agent does:**

1. **Routes first.** Either the [gatewise router](skills/gatewise/SKILL.md) or the gateway skill's own recurring reference. PayHere recurring needs PLUS; automated charging (preapproval + Charging API) needs PREMIUM. Genie needs `card_payments` plus MIT enabled by support. WebXPay uses Token V2 with `bankMID`s issued at onboarding. OnePay has card on file for merchant-initiated charges.
2. **Implements the flow for that gateway:** save the token at first payment, store the token (never the PAN), then charge later with your own idempotency key.
3. **Reads the plan/policy notes** (`account-business.md`, `environments-account.md`, `refund-payouts.md`) and tells you which tier or enablement you need *before* you build on it.
4. **Adds safe charge semantics:** look up before retrying, never blind-retry a charge, forward-only subscription states, cancel on refund where the gateway supports it.
5. **Bonus:** if you asked for PayHere preapproval with no amount, the agent uses the documented `10.00` (LKR) hash placeholder instead of zero.

**Tips:**

- Don't design around a feature your plan excludes. That check is cheap now and expensive after launch.
- The scheduler/webhook that triggers the charge is your job; the gateway charges a token, it doesn't run your billing calendar.
- Trial or future-dated recurring changes the *hashed* amount while the submitted amount stays real. PayHere documents this; the sign helper has `--future-start` and `--preapproval` for exactly that.
- Store tokens encrypted and per-customer. A token charged for the wrong customer is a breach, not a bug.

---

## Recipe 7 — Two gateways, one `settle()`

**What it does:** PayHere primary, Genie fallback, both writing through a single idempotent settle function, so a customer can still pay when one provider is down.

**What you say:**

```
Add PayHere as primary and Genie as fallback. If one is down the customer
should still be able to pay, and I don't want two ways of marking an order paid.
```

**What the agent does:**

1. **Reads `references/multi-provider.md`** from both gateway skills: shared `Gateway` interface, per-provider callbacks, one `settle()`.
2. **Lays out `.env`** with one banner-headed block per provider, prefixed variables, host first, two blank lines between blocks. No real keys.
3. **Records which provider created the order** and refuses a callback from provider B for an order created with provider A.
4. **Keeps exactly one settle path:** unique `(provider, gateway_ref)`, insert first, fulfil once, forward-only states.
5. **Adds selection or failover logic** with a short pending-expiry so a stuck provider doesn't hold stock forever.
6. **Tests the cross-provider cases:** valid Genie callback for a PayHere order (reject), duplicate across both (idempotent), and an expired pending order.

**Tips:**

- The settle function is the only place that writes `paid`. Two implementations means two chances to double-fulfil.
- Each provider keeps its own callback route; do not normalise them into one handler that guesses the provider from the body.
- Failover changes which gateway holds the money. Say so in your support notes before launch.

---

## Recipe 8 — Pre-launch review and a test plan

**What it does:** An evidence-based security pass over the payment code, then a go-live test checklist with the gateway-specific gaps marked.

**What you say:**

```
Review my payment code before I go live, then give me a test plan.
PayHere for cards, Koko for installments.
```

**What the agent does:**

1. **Runs the [payment-security-review](skills/payment-security-review/SKILL.md) method:** map the payment files, hunt one pass per flaw class, try to disprove each candidate, then report.
2. **Reports only traceable findings:** `confirmed`, `needs-validation`, `rejected`. Every finding has `file:line` where the input enters, where the check is missing, and the concrete outcome. No padding with theory.
3. **Redacts secrets** to the first four characters and never calls live endpoints.
4. **Switches to [payment-testing](skills/payment-testing/SKILL.md)** for the checklist: success, failure, cancel, duplicate callback, out-of-order callback, bad signature, tampered amount, return-without-callback, callback never arrives, timeout on outbound call, refund, go-live swap.
5. **Fakes callbacks with the gateway's own sign helper** rather than hand-rolling a second signing path, and flips one field for the negative case.
6. **States what could not be tested** — for example OnePay refunds, which are live-only.

**Tips:**

- "No trace, no finding" is the rule that keeps the report useful. A list of theoretical risks gets ignored.
- Test with the same code path as production. A "skip signature in dev" flag is how forged callbacks ship.
- Callback routes must be exempt from CSRF and session auth, POST only, and always 200 once handled.
- One supervised live payment at the end, then confirm it settles in the gateway dashboard.

---

## Recipe 9 — Refunds that cannot pay out twice

**What it does:** A staff-only partial refund endpoint with a cap computed inside a DB transaction, plus per-gateway reality checks (OnePay is live-only, WebXPay and Koko have no public refund API).

**What you say:**

```
Add a partial refund button in my admin for PayHere and Genie.
It must be impossible to refund more than was paid.
```

**What the agent does:**

1. **Reads [payment-refunds](skills/payment-refunds/SKILL.md)** for the matrix, plus the gateway's own refund reference for the exact request shape.
2. **Builds the endpoint:** authenticated and audited, order loaded by your id, cap `sum(refunds) + requested <= paid` inside a row lock, amount in the gateway's expected unit.
3. **Writes the refund row first** (`order, amount, reason, status=requested`) so a retry or double-click reuses it.
4. **Calls the gateway:** PayHere `POST /merchant/v1/payment/refund` with `payment_id` **or** `authorization_token` (one only) plus optional `amount`; Genie `POST /public/transactions/{id}/refunds` with `refundAmount` and `refundReason`, after checking `canPartialRefundIfConfirmed`.
5. **Settles forward-only:** `paid -> refund_requested -> refunded`, only from a verified state change, never from the API's "requested" response alone.
6. **Does the business side once**, after the refund is accepted: restock, revoke licence, cancel subscription.

**Tips:**

- Genie's `refundAmount` unit is not documented. Test small on UAT and confirm with Genie before writing the cap logic.
- OnePay allows one active refund per transaction and rejects sandbox refunds. WebXPay and Koko have no public refund API — use the portal and record it manually.
- A disputed payment should not also be refunded. Ask the gateway for the chargeback status first.
- Never promise refund timing. Banks settle on their own schedule.

---

## Recipe 10 — Add a gateway to Gatewise

**What it does:** Turns a gateway's public docs into a skill with references, a signing helper, three evals and a benchmark, through the same checks CI runs.

**What you say:**

```
Add AcmePay to Gatewise. Docs are at docs.acmepay.lk — build the skill and test it.
```

**What the agent does:**

1. **Copies the template:** `templates/gateway-skill` → `skills/acmepay`, following [docs/adding-a-gateway.md](docs/adding-a-gateway.md).
2. **Writes one reference per topic:** checkout, recurring, server API, SDKs/plugins, sandbox/testing, account/fees, troubleshooting, multi-provider.
3. **Writes a pushy `description`** with gateway name, domains, parameter names and error codes, so routing works without the user saying "AcmePay".
4. **Adds a helper** in `scripts/` and verifies it against a known vector.
5. **Adds three evals** under `evals/acmepay/` — including one support question and one gotcha the model usually misses — then grades with and without the skill.
6. **Packages and verifies:**

   ```bash
   python scripts/package.py acmepay
   python scripts/verify.py
   ```

7. **Records gaps in `references/troubleshooting.md`** instead of inventing an answer, and saves the round to `docs/benchmarks/acmepay-iteration-1.md`.

**Tips:**

- `verify.py` fails if a reference file is unlinked, a helper stops matching its vector. Run it before opening the PR.
- Add the skill to `.claude-plugin/marketplace.json` or the plugin bundle will miss it.
- Docs that contradict themselves are a finding, not a blocker. Write down both readings.
- Third-party or unofficial docs are allowed only if labelled unvetted.

---

## Quick reference — which recipe for what

| Goal | Recipe | Skills used |
|---|---|---|
| Card checkout that verifies its callbacks | #1 PayHere checkout | `payhere` + `payment-basics` |
| Installments / buy now pay later | #2 Koko BNPL | `koko` |
| One redirect across wallets, QR, EMI and cards | #3 WebXPay redirect | `webxpay` |
| Hosted page with wallet + QR methods | #4 Genie webhook | `genie` |
| Cards, Frimi, QPlus, HelaPay, Google Pay | #5 OnePay checkout | `onepay` |
| Subscriptions, saved cards, tokenized charging | #6 Recurring | `gatewise` router → gateway skill |
| Primary + fallback provider in one app | #7 Two gateways | any two gateway skills' `multi-provider.md` |
| Security review or go-live test plan | #8 Pre-launch | `payment-security-review` + `payment-testing` |
| Partial refunds, refund states, chargebacks | #9 Refunds | `payment-refunds` + gateway skill |
| Contribute a new gateway | #10 Add a gateway | `templates/gateway-skill` + `scripts/verify.py` |

Not covered by a recipe? Ask normally. The [router](skills/gatewise/SKILL.md) picks a gateway when you have not named one, and each skill's routing table sends the agent to the right reference file.

## Patterns these recipes share

1. **The browser is never proof of payment.** Redirect pages and JS callbacks are for the customer. Paid comes from a verified server-to-server call, or from a status API call you made yourself.
2. **Amounts come from your database.** Server-side signing only, two decimals or minor units exactly as the gateway expects, never a float and never a number the client sent.
3. **Every settle is idempotent.** Unique `(provider, gateway_ref)`, insert first, fulfil once, forward-only states. Callbacks repeat, race and arrive out of order.
4. **Something must catch the missing callback.** A reconciliation job that reuses the same settle function — not a second implementation, and not a support ticket.
5. **Secrets stay in the environment.** Placeholders in `.env`, never in output, never in a browser bundle, never in a log line. Sandbox and live keys never mix.
6. **Undocumented means unanswered.** Where a gateway's docs are silent or contradict themselves, the skill says so and sends you to the gateway. That is the feature, not a gap.
