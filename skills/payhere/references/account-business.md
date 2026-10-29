# Account, plans, fees, payouts, refunds, products (non-code knowledge)

Source: support.payhere.lk knowledge base as read Oct 2026. Fees, limits and plans change; for money questions tell the user to confirm on payhere.lk or with support (support@payhere.lk, 24x7 helpdesk 0115 339 339).

## Contents
1. What PayHere is, payment methods, currencies
2. Applying for an account
3. Service plans, limits, fees
4. USD payouts
5. Settlement, refunds, chargebacks (business rules)
6. Feature primers: Recurring, Automated Charging, Hold on Card
7. No-code options: Links, Buttons, logos
8. Policy pages required for approval
9. Terminology

## 1. Basics
- Sri Lanka's Central Bank (CBSL) approved aggregated internet payment gateway, run by PayHere (Pvt) Ltd with licensed partner banks (CBSL PSD Direction No.1 of 2018). Card data handled by PCI DSS Level 1 bank backends; pages over SSL (EV cert).
- Methods: cards (Visa, MasterCard, AMEX, Discover, Diners), bank (HelaPay), wallets (Frimi, Genie, iPay, Q Plus, Sampath Vishwa). Notification `method` codes also include EZCASH, MCASH, VISHWA, PAYAPP, HNB.
- Currencies: LKR, USD, GBP, EUR, AUD (see plan table: LITE is LKR/USD only).
- Customers don't need a PayHere account.
- On payment: merchant gets email, customer gets receipt email, notify_url callback fires, Payments tab updates. Fulfil goods once the verified notification arrives.
- Ways to accept: Payment Links (no website), shopping-cart plugins, Checkout/Recurring APIs, JS SDK (onsite), mobile SDKs, Buttons.

## 2. Applying
- Eligible: any business in Sri Lanka selling goods/services (local or foreign customers). Needs a valid business and a local bank account (savings OK; personal account OK for home-based/freelance; business account required for Pvt Ltd, partnership, sole proprietorship; government bodies need an account owned by the organization).
- Types: Pvt Ltd, sole proprietorship, partnership, clubs & associations, home-based, freelance, government organizations.
- Business registration required for Pvt Ltd / sole prop / partnership; others submit proof of business (social page or site, Fiverr/Upwork profile + certificates, club meeting minute on letterhead, Act/Gazette for government).
- Process: sign up + verify email > complete Activation Form > partner-bank review (1-3 days) > approval email. Free to apply, no setup fee.
- Approval tips: website/app finished with real products (no under-construction or mock content); **Terms & Conditions, Refund/Return Policy, Privacy Policy visible**; contact details (registered name, phone, email, postal address) visible; clear bank proof (statement or "Letter of Account Confirmation"); properly signed merchant agreement (company: stamped signatures of two directors + secretary, etc.).
- Rejections for form errors can be fixed and resubmitted; rejections for business nature by the partner bank cannot be re-applied.
- **Donations are not allowed**: only payments where goods/services are delivered.
- Unsupported categories: gems & jewellery, unauthorized software licences, outbound tour services, dating, astrology. Unsupported models: drop-shipping, print-on-demand, multi-vendor platforms.
- Sandbox is separate and cannot be converted to live.

## 3. Plans (as listed Sep 2026)
| Plan | Monthly fee | Processing fee | Limits | Notes |
|---|---|---|---|---|
| LITE | none | 3.3% | LKR/USD one-time only; Rs.50,000 per payment; Rs.200,000 per month | startups |
| PLUS | Rs.3,990 | 2.99% | Rs.250,000 per payment; Rs.3,000,000 per month | one-time + recurring; LKR/USD/EUR/GBP/AUD |
| PREMIUM | Rs.9,990 | 2.69% | Rs.1,000,000 per payment; unlimited monthly | adds Automated Charging (preapproval/tokenization) |
| EDU | Rs.9,990 | 2.49% | Rs.1,000,000 per payment; unlimited monthly | education payments only |
| GOV | none | 1.99% | Rs.1,000,000 per payment; unlimited monthly | government payments; LKR via Visa/Master/HelaPay |

- Over a limit: customer sees an "Over Limit" error on the payment page (monthly limit until the billing cycle ends). Upgrade plan to raise limits.
- Upgrade/downgrade in Settings; paid plan fee charged monthly to a Visa/Master card; downgrade gives no partial refund of the month's fee.
- Practical implication: Recurring API needs PLUS+; preapproval/Charging API needs PREMIUM; Hold on Card is card-only (check plan availability with PayHere).

## 4. USD payouts
- Receive foreign payments directly in a USD account, no LKR conversion. Requires a registered business entity and a **Seylan Bank** USD (BFC) account; PLUS or PREMIUM only; set "Payout Currency = USD" in the Activation Form of a **new** USD PayHere account (existing LKR account can't be switched).
- USD plan numbers (docs): PLUS Rs.3,990/mo, 3.99%, USD 1,000 per payment, USD 10,000 per month; PREMIUM Rs.9,990/mo, 3.69%, USD 5,000 per payment, unlimited monthly. No setup fee.

## 5. Settlement, refunds, chargebacks
- Payouts to your bank daily at day-end on a **T+2** cycle.
- Refund from dashboard: Payments tab > open payment > Request Refund. No refund fee; the processing fee is returned to the customer too.
- **Instant refund**: same-day, before day-end, processed as a void in real time.
- **Delayed refund**: after payout; PayHere recovers funds from your bank balance/future payouts at day-end (retries daily until funds exist), then 5-10+ days to reach customer's card. Statuses: Waiting funds > Refund processing > Refund processed.
- Only **card** payments can be refunded through PayHere (Visa, Mastercard, AMEX, Discover, Diners). Frimi, Genie, eZcash, mCash, Vishwa: refund manually via bank transfer.
- The KB says partial refunds are not supported, but the Refund API accepts an optional `amount` for partial refunds (see `merchant-api.md`). When this matters, tell the user about the conflict and suggest confirming with support@payhere.lk before building around partial refunds.
- Chargeback = automatic reversal demanded by card/wallet provider (`status_code -3`, Retrieval status `CHARGEBACKED`). Dispute = cardholder queries a transaction.

## 6. Feature primers
**Recurring billing**: customer authorizes once; PayHere charges per schedule. Store `subscription_id`. Only the merchant can cancel (dashboard subscription section or Subscription Manager API); customers must ask you. Fixed-duration subs complete on their own; "Forever" ones run until cancelled. Failure handling/retries: see `recurring-preapproval.md`.

**Automated Charging (tokenization)**: customer preapproves once (Rs.1 is charged then instantly refunded), you receive an encrypted `customer_token` on notify, store it, and charge any amount on demand via Charging API. Visa/Mastercard only. Merchant cancels a preapproval in Payments > Preapprovals > Cancel Preapproval (irreversible); customers can't cancel themselves.

**Hold on Card (auth & capture)**: authorize now via Authorize API, capture the same or lesser amount later via Capture API **within 7 days**; uncaptured holds auto-release after 7 days. Avoids refunds for partial fulfilment. Settles to the bank 2 days after capture. Visa/Mastercard credit cards only. Remaining uncaptured balance is released after 7 days.

## 7. No-code options
- **PayHere Links**: Dashboard > Payment Links > Create Link (item name + amount) > copy and share via post, email, chat, SMS. PayHere also collects customer, delivery and item details, so it doubles as order capture.
- **PayHere Buttons**: same Payment Links screen > "Get code" > paste the button HTML on your site (customizable styling).
- **Logos**: banners at `https://www.payhere.lk/downloads/images/payhere_{long,short,square}_banner[_dark].png` (widths 400 / 250 / 150), linked to `https://www.payhere.lk`.

## 8. Policy pages
Refund Policy, Privacy Policy and Terms & Conditions must be on the site/app (linked from the landing page) or activation is rejected. PayHere offers sample documents as general guidelines to adapt. Offer to draft them for the user's business when asked.

## 9. Terminology
Merchant, Customer, Payment, Payout (PayHere balance to your bank), PayHere Account/Balance, Fee, Payout Cycle, Release Level (amount held back from payout), Eligible Payments (past holding time), Holding Time (during which you can refund), Refund, Chargeback, Dispute.
