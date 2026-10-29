# OnePay JS (script tag) and npm SDK

## OnePay JS (overlay checkout)
Script: `https://storage.googleapis.com/onepayjs/onepayv2.js` (near `</body>`).
1. Define `window.onePayData` before the script runs.
2. Add `<div id="onepay-btn"></div>`; a Pay Now button renders there.

`window.onePayData` fields (all required except `additionalData`): `appid`, `hashToken`, `apptoken`, `amount` (number), `currency`, `orderReference`, `customerFirstName`, `customerLastName`, `customerPhoneNumber` (E.164), `customerEmail`, `transactionRedirectUrl` (required even though the overlay doesn't navigate), `additionalData`.

`hashToken`: the table calls it "Hash Salt" but the warning says generate it server-side. Treat it as the **server-computed hash** (`SHA256(app_id+currency+amount+salt)`) so the salt never reaches the browser; confirm with OnePay.
`apptoken` is placed in client JS by this design; that is OnePay's documented behavior. Say so to the user as a risk and recommend `processDirectPayment` / server-created transactions if they want the token off the client.

Events on `window` (data in `e.detail`): `onePaySuccess` (`code`, `transaction_id`, `status` = "SUCCESS"), `onePayFail` (same fields, "FAIL"; also cancelled/declined). The overlay closes before the success event. Browser events are UI signals only: confirm with the status API / server callback.

## npm SDK `@onepaynpm/onepay-sdk` (v1.0.3, MIT, no deps)
```ts
import { OnePaySDK } from '@onepaynpm/onepay-sdk';
const sdk = new OnePaySDK({ debug: true });   // options: debug, apiBaseUrl, firebaseConfig
await sdk.initialize();                       // once, before any payment
sdk.addEventListener({ onSuccess, onFail, onClose });  // on the instance, NOT a ref's .current
```
Methods: `initialize`, `isInitialized`, `addEventListener`, `removeEventListener`, `processPayment`, `processSubscription`, `processDirectPayment`, `closePaymentGateway`.
- `processPayment`: same fields as `onePayData` (`appid, hashToken, apptoken, amount, currency, orderReference, customer*, transactionRedirectUrl`).
- `processSubscription`: `currency, amount, appid, name, interval ('month'), interval_count, days_until_due, trial_period_days, customer_details{first_name,last_name,email,phone}, apptoken`. This is the only documented client-side way to do subscriptions.
- `processDirectPayment({directGatewayURL, directTransactionId})`: open the overlay for a transaction you created server-side.
Troubleshooting: listeners never fire → attached to a ref; events never arrive → check `firebaseConfig` and that `initialize()` resolved first.
