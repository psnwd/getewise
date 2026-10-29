# Card on file, recurring and MIT

## Contents
1. Concepts
2. Save a card during a payment (CIT)
3. Save a card without charging
4. List and charge tokens
5. Merchant-initiated recurring (MIT) and scheduler
6. Not documented in the pages we read

## 1. Concepts
- Only `card_payments` supports tokenisation. Wallets don't.
- Every token belongs to one Customer and can only be charged for that customer. You need the Customer module: create a customer first (Create Customer API), or pass `customer{}` inline when creating the transaction (one call).
- Two flavours:
  - **Card on file, customer present** (`paymentType: UNSCHEDULED`): one-click checkout later.
  - **MIT** (`paymentType: RECURRING`): merchant charges without cardholder involvement. **Disabled by default**; ask Genie support to enable it. Genie's scheduler (auto-charge on a fixed interval until expiry) also needs enabling.
- Never store or log full card numbers. You only ever see `paddedCardNumber` (`5444******5118`) and an opaque token string. Treat `token` like a payment credential.

## 2. Save a card during a payment (CIT)
Create Transaction (V2):
```json
{
  "amount": 100,
  "currency": "LKR",
  "tokenizationDetails": {
    "tokenize": true,
    "paymentType": "UNSCHEDULED",
    "recurringFrequency": "UNSCHEDULED"
  },
  "customer": { "name": "A Perera", "email": "a@example.com", "billingEmail": "a@example.com",
                "billingAddress1": "1 Main St", "billingCity": "Colombo",
                "billingCountry": "LK", "billingPostCode": "00100" },
  "webhook": "https://shop.example/webhooks/genie"
}
```
Or pass `"customerId": "<existing id>"` instead of `customer`. After the customer pays, the card is tokenised and a `NOTIFY_TOKENISATION_STATUS` webhook fires. (The docs write `recurringFrequency: "UNSCHEDULED"` here although the field's allowed list says `AD_HOC` for ad-hoc; see `troubleshooting.md`.)

## 3. Save a card without charging
```json
{
  "amount": 30, "currency": "LKR", "customerId": "<id>",
  "addCardToVault": true, "provider": "card_payments",
  "paymentPortalExperience": {
    "externalWebsiteTermsAccepted": true,
    "externalWebsiteTermsUrl": "https://shop.example/terms",
    "skipCustomerForm": true, "skipProviderSelection": true, "hideTermsAndConditions": true
  }
}
```
The card is validated and vaulted without an authorisation. The first charge with that token triggers 3DS; later ones depend on threshold settings.

## 4. List and charge tokens
List: `GET {base}/public-customers/{customerId}/tokens` (Authorization header) returns `{ items: [...], count }`. Each item has `id` (tokenId), `token`, `tokenType` (CARD), `brand`, `paddedCardNumber`, `tokenExpiryMonth/Year`, `defaultToken`, `tokenAgreementType`, `customerId`. Show brand + padded number if you let the customer choose.

Charge = two steps:
1. Create Transaction V2 for the customer with `tokenizationDetails: { "tokenize": false, "paymentType": "UNSCHEDULED" }`.
2. Call **Charge Stored Token** with one of:
```json
{ "customerId": "...", "transactionId": "...", "tokenId": "..." }
{ "customerId": "...", "transactionId": "...", "token": "..." }
{ "customerId": "...", "transactionId": "..." }
```
The last form uses the default token. Then confirm via `NOTIFY_TRANSACTION_CHANGE` or Get Transaction until `CONFIRMED`. The Charge Stored Token path isn't in the pages we read, see section 6. A November 2024 change-log entry says this API gained new fields for a new 3DS provider; check the Stoplight page for them.

## 5. MIT recurring and scheduler
First (customer-initiated) payment:
```json
{ "amount": 200, "currency": "LKR", "customerId": "<id>",
  "tokenizationDetails": { "tokenize": true, "paymentType": "RECURRING",
                           "recurringFrequency": "WEEKLY", "expiryDate": "12-07-2025" } }
```
- `recurringFrequency`: `DAILY`, `WEEKLY`, `BIWEEKLY`, `FORTNIGHTLY`, `MONTHLY`, `QUARTERLY`, `YEARLY`, `TWICE_YEARLY`, `AD_HOC`, `OTHER`. Use `AD_HOC` for any amount at any interval.
- `expiryDate` is required when `RECURRING`, and the doc examples and the pattern use `dd-mm-yyyy` (`12-07-2025`) even though the field text says `yyyy-mm-dd`. Follow the examples and test on UAT. It must be in the future.
- **Genie scheduler** (if enabled): after the first payment Genie charges automatically on the frequency until expiry.
- **Your own scheduler**: on each due date create a transaction with `tokenize: false`, the same `paymentType`/`recurringFrequency`, then call Charge Stored Token.
- Build for failures: the card can expire or decline; notify the customer, retry on a policy you choose, and stop at `expiryDate`.

## 6. Not documented in the pages we read
Paths and bodies for Create Customer, Charge Stored Token, Create Webhook, FX, SMS/email share. Open the matching item under Connect API in https://geniebusiness.stoplight.io/docs/genie-business-connect (Customers, Tokenization, Webhooks, FX, Transactions). Don't invent them; if the user pastes the page, use it.
