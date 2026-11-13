# OnePay JS (script tag) and npm SDK

## OnePay JS (overlay checkout)
Script: `https://storage.googleapis.com/onepayjs/onepayv2.js` (near `</body>`).
1. Define `window.onePayData` before the script runs.
2. Add `<div id="onepay-btn"></div>`; a Pay Now button renders there.

`window.onePayData` fields (all required except `additionalData`): `appid`, `hashToken`, `apptoken`, `amount` (number), `currency`, `orderReference`, `customerFirstName`, `customerLastName`, `customerPhoneNumber` (E.164), `customerEmail`, `transactionRedirectUrl` (required even though the overlay doesn't navigate), `additionalData`.

`hashToken`: **the raw Hash Salt**, not a pre-computed hash. The docs table says "used by the script to sign the request", and the shipped script concatenates `app_id + currency + amount.toFixed(2) + hashToken` and SHA-256s it in the browser. The docs' advice to pre-compute it server-side is therefore unachievable — a pre-computed hash would be hashed again. Client-side salt exposure is inherent to OnePay JS; `processDirectPayment` on a server-created transaction is the only way to keep the salt (and `apptoken`) off the client.
`apptoken` is placed in client JS by this design; that is OnePay's documented behavior. Say so to the user as a risk and recommend `processDirectPayment` / server-created transactions if they want the token off the client.

Events on `window` (data in `e.detail`): `onePaySuccess` (`code`, `transaction_id`, `status` = "SUCCESS"), `onePayFail` (same fields, "FAIL"; also cancelled/declined). The docs table gives `code` as `"SUCCESS"`/`"FAIL"` but the shipped script dispatches `code:"201"` on success and `code:"400"` on failure — **branch on `status`, never on `code`**. The overlay closes before the success event. Browser events are UI signals only: confirm with the status API / server callback.

## npm SDK `@onepaynpm/onepay-sdk` (v1.0.3, MIT, no deps)
```ts
import { OnePaySDK } from '@onepaynpm/onepay-sdk';
const sdk = new OnePaySDK({ debug: true });   // options: debug, apiBaseUrl, firebaseConfig
await sdk.initialize();                       // once, before any payment
sdk.addEventListener({ onSuccess, onFail, onClose });  // on the instance, NOT a ref's .current
```
Methods: `initialize`, `isInitialized`, `addEventListener`, `removeEventListener`, `processPayment`, `processSubscription`, `processDirectPayment`, `closePaymentGateway`.
- `processPayment`: same fields as `onePayData` (`appid, hashToken, apptoken, amount, currency, orderReference, customer*, transactionRedirectUrl`).
- `processSubscription`: `currency, amount, appid, name, interval ('month'), interval_count, days_until_due, trial_period_days, customer_details{first_name,last_name,email,phone}, apptoken`. This is the only documented client-side way to do subscriptions; the server-side API is in `subscriptions.md`.
- `processDirectPayment({directGatewayURL, directTransactionId})`: open the overlay for a transaction you created server-side.
- The SDK also emits **`onePayClose`** (`document.addEventListener('onePayClose', …)`), which the docs' "two events" description omits.
Troubleshooting: listeners never fire → attached to a ref; events never arrive → check `firebaseConfig` and that `initialize()` resolved first.
