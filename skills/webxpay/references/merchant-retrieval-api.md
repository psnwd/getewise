# Merchant login and Transaction Retrieval (redirect-integration merchants)

Form-data calls on `https://webxpay.com/index.php?route=api/merchant_api/...` (HTTP method not stated; use POST form-data, verify).

## Login (get an auth token)
- Email + password: `route=api/merchant_api/loginRequest`
- API credentials: `route=api/merchant_api/apiLogin` with API username, API password, Merchant MID.
Token format, header name and expiry are not documented (screenshots only). A `Merchant-login-api.json` spec is linked on the page: ask WebXPay for it.

## Transaction retrieval (needs the token)
- By WebXPay order reference: `route=api/merchant_api/getTransactionData` (param: order reference number)
- By your store reference / order id: `route=api/merchant_api/getTransactionByMerchantReference`
Response field names are in screenshots; spec file `get-trans-data-API.json` is linked as "Download API". The page text says the second call "returns an auth token", which looks like a copy-paste error.
Use these to confirm payment status server-side after a return-URL hit.
