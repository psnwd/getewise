# Koko order creation

`POST {host}/api/merchants/orderCreate`, `application/x-www-form-urlencoded`, submitted by the customer's browser (auto-submitting form).

| Env | Host |
|---|---|
| Dev | `https://devapi.paykoko.com` (separate merchant registry; QA/prod credentials do not work here) |
| QA | `https://qaapi.paykoko.com` |
| Prod | `https://prodapi.paykoko.com` |

Merchant ID (`_mId`), `api_key` and the key pair exchange (you give Koko your public key; you get Koko's public key) come from Koko onboarding.

**Auth is form fields only:** `_mId` + `api_key`. There is no auth header, Basic or otherwise — both `orderCreate` and `orderView` accept unauthenticated HTTP requests and authenticate purely from the signed payload. `api_key` is sent **plaintext** and compared literally.

`_mId` is a 32-char lowercase hex id (e.g. `c8cca514bdfa0582cdc40c9703c71e9d`); a non-hex value returns `corruptted entity ID` (Koko's spelling).

## Fields
| Field | Notes |
|---|---|
| `_mId` | Merchant ID, 32-char lowercase hex |
| `api_key` | Merchant API key, plaintext form field (signed, sent in form) |
| `_returnUrl` | Browser redirect after payment: `orderId, trnId, status` |
| `_cancelUrl` | Browser redirect on cancel: status `CANCELED` |
| `_responseUrl` | Server-to-server POST with signed result |
| `_amount` | Decimal string, e.g. `300.00` |
| `_currency` | `LKR` |
| `_reference` | Your reference (free-form; need not equal `_orderId`) |
| `_orderId` | Unique per request |
| `_pluginName` | `customapi` (custom integrations) |
| `_pluginVersion` | Your version string, e.g. `1.0.1` |
| `_description` | Order description |
| `_firstName`, `_lastName`, `_email` | Customer |
| `_mobileNo` | Posted in the form, **not** part of `dataString`; whether it is required is unresolved |
| `dataString` | See below |
| `signature` | base64 RSA-SHA256 of `dataString` |

`_pluginName` + `_pluginVersion` are matched server-side against the plugin registration Koko holds for your MID. A mismatch fails with `OnlineOrder.create.merchantPluginDetail.apiKey.invalid` even when the key is valid (e.g. sending `woocommerce`/`8.6.0` against a registration of `customapi`/`1.0`). Confirm both values with Koko at onboarding; they are not free-form.

## dataString (exact order, no separators)
```
_mId + _amount + _currency + _pluginName + _pluginVersion + _returnUrl + _cancelUrl
+ _orderId + _reference + _firstName + _lastName + _email + _description + api_key + _responseUrl
```
`signature = base64( RSA_SHA256_PKCS1v15_sign(merchant_private_key, dataString) )`

Sign the same strings you post; any change in whitespace or amount formatting breaks the signature.

## Flow
1. Create order in your DB, amount authoritative.
2. Server builds fields, `dataString`, `signature`.
3. Return an HTML page with a hidden form posting to `orderCreate`, `onload` submit.
4. Wait for `_responseUrl` callback (see `callbacks.md`).
