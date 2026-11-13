# Card on file, recurring and MIT

## Contents
1. Concepts
2. Save a card during a payment (CIT)
3. Save a card without charging
4. List and charge tokens
5. Merchant-initiated recurring (MIT) and scheduler
6. Endpoints, and what is still undocumented

## 1. Concepts
- Only `card_payments` supports tokenisation. Wallets don't.
- Every token belongs to one Customer and can only be charged for that customer. You need the Customer module: create a customer first (Create Customer API), or pass `customer{}` inline when creating the transaction (one call).
- Two flavours:
  - **Card on file, customer present** (`paymentType: UNSCHEDULED`): one-click checkout later.
  - **MIT** (`paymentType: RECURRING`): merchant charges without cardholder involvement. **Disabled by default**; ask Genie support to enable it. Genie's scheduler (auto-charge on a fixed interval until expiry) also needs enabling.
- Never store or log full card numbers. You only ever see `paddedCardNumber` (`5444******5118`) and an opaque token string. Treat `token` like a payment credential.
- `tokenizationDetails` takes more than `tokenize`/`paymentType`/`recurringFrequency`: also `customerInitiated` (boolean, "set true if customer initiated") and `expires` (token expiry, ISO `1996-10-15T00:05:32.000Z`, max 24). In the returned transaction object it also carries `numberOfInstallments`, `paymentNumber`, `initiationMethod` (example `CARD_HOLDER_INITIATED`), `tokenId`, `tokenAgreementId` and `tokenAgreementType` (`UNSCHEDULED`).

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
Or pass `"customerId": "<existing id>"` instead of `customer`. After the customer pays, the card is tokenised and a `NOTIFY_TOKENISATION_STATUS` webhook fires. `paymentType` is exactly `UNSCHEDULED` or `RECURRING`; the card-on-file examples send `recurringFrequency: "UNSCHEDULED"`, which only exists in the UNSCHEDULED branch of the spec (spec-mock). `AD_HOC` is valid in every branch if you want one value for all cases.

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
The last form uses the default token. Then confirm via `NOTIFY_TRANSACTION_CHANGE` or Get Transaction until `CONFIRMED`. The endpoint is documented only as relative `POST /charge-stored-token` (absolute URL unverified; see section 6). A November 2024 change-log entry says this API gained new fields for a new 3DS provider; check the Stoplight page for them.

## 5. MIT recurring and scheduler
First (customer-initiated) payment:
```json
{ "amount": 200, "currency": "LKR", "customerId": "<id>",
  "tokenizationDetails": { "tokenize": true, "paymentType": "RECURRING",
                           "recurringFrequency": "WEEKLY", "expiryDate": "12-07-2025" } }
```
- `recurringFrequency`: `DAILY`, `WEEKLY`, `BIWEEKLY`, `FORTNIGHTLY`, `MONTHLY`, `QUARTERLY`, `TWICE_YEARLY`, `YEARLY`, `AD_HOC`, `OTHER` — all ten appear in every branch, and `UNSCHEDULED` appears only in the UNSCHEDULED branch (spec-mock). Use `AD_HOC` for any amount at any interval; it is always valid.
- `expiryDate` is required when `RECURRING`. The field doc says, in one sentence: "Format: yyyy-mm-dd, must be future date (maximum 8 characters, pattern: dd-mm-yyyy)". The spec is **unsatisfiable**: a `dd-mm-yyyy` value (`12-07-2025`) breaks the 8-character cap and an 8-character value breaks the pattern (spec-mock). The Create Transaction V2 example uses `2025-12-31`, the card-on-file page `12-07-2025`. Only UAT settles it; must be in the future either way.
- **Genie scheduler** (if enabled): after the first payment Genie charges automatically on the frequency until expiry.
- **Your own scheduler**: on each due date create a transaction with `tokenize: false`, the same `paymentType`/`recurringFrequency`, then call Charge Stored Token.
- Build for failures: the card can expire or decline; notify the customer, retry on a policy you choose, and stop at `expiryDate`.

## 6. Endpoints, and what is still undocumented
| Capability | Request |
|---|---|
| Create webhook | `POST {base}/public/webhooks` with `{"hookUrl": "..."}` → 200 `{created, updated, companyId, hookUrl, id}`; `hookUrl` is required (spec-mock) |
| Delete webhook | `DELETE {base}/public/webhooks` with `{"hookUrl": "..."}` → 204 (400 if not found) |
| List customers | `GET {base}/public-customers/`, query `email, name, from, to, limit, page` → `{items[], count}` |
| Get / update / delete customer | `GET` / `PATCH` / `DELETE {base}/public-customers/{customerId}` (delete → 204) |
| List tokens | `GET {base}/public-customers/{customerId}/tokens` → `{items[], count}` |
| Get / delete token | `GET` / `DELETE {base}/public-customers/{customerId}/tokens/{tokenId}` |
| Charge stored token | relative `POST /charge-stored-token` only; body `{customerId, transactionId, tokenId \| token \| neither}`. Probably `https://api.geniebiz.lk/public/charge-stored-token` — unverified |

Still unresolved:
- **Create Customer**: the page exists but only its GET content is recoverable, the mock does not implement `POST /public-customers`, and the mirrored request body contradicts Genie's customer schema. Working assumption only: `POST {base}/public-customers` with the same `customer{}` fields as Create Transaction.
- **Capture of `AUTHORIZED`**: no capture endpoint in the docs, mock or SDKs. `AUTHORIZED` exists only as a state with `capturedAmount`, `preauthorizedAmount`, `preauthorizedExpiryDate`, `isPreAuthorization`. Ask support.
- **FX**: only a change-log line ("19th Jun 2025 - Add FX API") and the `fxOrder` field; no path, body or page.

Don't invent the rest; if the user pastes a page, use it.
