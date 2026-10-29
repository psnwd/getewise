# Create and read transactions

## Contents
1. Environments and auth
2. Create Transaction (V2)
3. Request fields
4. Response fields that matter
5. Get Transaction
6. Hosted-page behaviour

## 1. Environments and auth
| Env | Base URL |
|---|---|
| Production | `https://api.geniebiz.lk` |
| UAT / development testing | `https://api.uat.geniebiz.lk` |
| Stoplight mock | `https://stoplight.io/mocks/geniebusiness/genie-business-connect/68676462` (fake data) |

Header on every call: `Authorization: <API key>` (the docs' example is `Authorization: 123`, no scheme prefix) and `Content-Type: application/json`. Production key: merchant dashboard (https://dashboard.geniebiz.lk/) under Connect. Sandbox key: see `environments-account.md`.

## 2. Create Transaction (V2)
`POST {base}/public/v2/transactions`. Returns 201 with the transaction object. The body schema is "one of" three variants; the docs recommend the third (plain amount and currency), which is what most integrations need.

```json
{ "amount": 500, "currency": "LKR" }
```
Amount is an integer in minor units, so this is LKR 5.00. A fuller example:
```json
{
  "amount": 250050,
  "currency": "LKR",
  "localId": "ORDER-1042",
  "customerReference": "cust-77",
  "redirectUrl": "https://shop.example/pay/return",
  "webhook": "https://shop.example/webhooks/genie",
  "paymentAttemptFailureUrl": "https://shop.example/pay/failed",
  "expires": "2026-11-05T10:00:00.000Z",
  "customer": {
    "name": "A Perera", "email": "a@example.com", "billingEmail": "a@example.com",
    "billingAddress1": "1 Main St", "billingCity": "Colombo",
    "billingCountry": "LK", "billingPostCode": "00100"
  }
}
```

## 3. Request fields
| Field | Notes |
|---|---|
| `amount` | integer, minor units; required for the amount variant |
| `currency` | 3 letters; "will be similar to merchant currency" (foreign currencies depend on your account) |
| `redirectUrl` | max 200 chars; where the customer returns, used for final states (CONFIRMED, CANCELLED) |
| `webhook` | max 200 chars; per-transaction webhook for transaction and token updates |
| `localId` | max 100; your own reference, echoed back and in reports. Use your order ID |
| `customerReference` | max 100 |
| `paymentAttemptFailureUrl` | http(s), max 200; redirects on a failed attempt even while still pending, so the customer skips the hosted retry page. Does not replace `redirectUrl` |
| `expires` | ISO 8601 string; payment link expiry (default in samples is about 7 days) |
| `customer{}` | optional; if sent, a customer is created and `customerId` is returned. Required inside it: `name`, `email`, `billingEmail`, `billingAddress1`, `billingCity`, `billingCountry`, `billingPostCode`. Optional: `billingAddress2`, `customerGroup`, `externalId` |
| `customerId` | reuse an existing customer (card on file) |
| `customerAsPayer` | with stored credentials, marks the customer as payer so the transaction isn't flagged for missing billing details |
| `sendCustomerEmailReceipt` | default true |
| `tokenizationDetails{}` | see `tokenization-recurring.md` |
| `paymentPortalExperience{}` | `externalWebsiteTermsAccepted`, `externalWebsiteTermsUrl`, `skipCustomerForm`, `skipProviderSelection` (then `provider` is required), `hideTermsAndConditions`, `addCardToVault`, `allowRetry` |
| `preferredSubscriptionPlan` | plan code, if your company has multiple plans, to apply the right MDR |
| `locationId` | shop/location ID to use a different MCC or link a shop |
| `order{shopId, products[], orderFields[]}` | first/second request variants: create an order with the transaction (shop ID and products required) |
| `invoicePrefix`, `paymentDue`, `taxInformation`, `taxId` | invoicing module |

## 4. Response fields that matter
| Field | Meaning |
|---|---|
| `id` | transaction ID (24-char); store it |
| `state` | see `states-refunds.md`; CONFIRMED = paid |
| `url` | hosted payment page; redirect the customer here (UAT: `https://transaction.uat.geniebiz.lk/<id>`) |
| `shortUrl` | short payment link (UAT: `https://uat.paylink.geniebiz.lk/<hash>`) |
| `amount`, `currency`, `payAmount`, `payCurrency` | minor units; pay values are in the payer's currency |
| `amountAsDecimal`, `amountFormatted` | `"4.00"`, `"LKR 4.00"` |
| `localId`, `customerReference`, `customerId` | your references back |
| `expires` | when it auto-cancels |
| `provider`, `providerBrandName`, `paddedCardNumber`, `cardFunding`, `cardCountry`, `cardExpMonth/Year` | filled after payment |
| `paymentToken` | auth code of a confirmed transaction |
| `securityWord` | shown to the payer after success (also in webhook) |
| `history[]` | state changes with timestamps |
| `refundExpiryDate`, `refundTransactions[]` | refund window and children |
| `isTest` | test-provider transactions |

Many other fields are marked "internal logic" in the docs; ignore them.

## 5. Get Transaction
`GET {base}/public/transactions/{transactionId}` with the same `Authorization` header. Returns the same object. The docs call this check mandatory before you treat a payment as done. Note the path: the Stoplight page shows `/public/transactions/{id}` while the webhook guide's sample calls `/public/v2/transactions/{id}`. See `troubleshooting.md`; try the documented one, fall back to the other, or confirm with support.

## 6. Hosted-page behaviour
- Customer opens `url`, picks a method (unless `skipProviderSelection`), pays, and is sent to `redirectUrl`.
- A pending transaction sits in `QR_CODE_GENERATED` even for cards and redirect wallets.
- Failed attempts: with `allowRetry` the transaction is cancelled on failure and a webhook is sent; otherwise the hosted page offers a retry.
- Payment links can also be shared by SMS or email through two dedicated endpoints (see the Transactions group in Stoplight).
