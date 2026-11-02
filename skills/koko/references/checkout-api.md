# Koko order creation

`POST {host}/api/merchants/orderCreate`, `application/x-www-form-urlencoded`, submitted by the customer's browser (auto-submitting form).

| Env | Host |
|---|---|
| Dev | `https://devapi.paykoko.com` |
| QA | `https://qaapi.paykoko.com` |
| Prod | `https://prodapi.paykoko.com` |

Merchant ID (`_mId`), `api_key` and the key pair exchange (you give Koko your public key; you get Koko's public key) come from Koko onboarding.

## Fields
| Field | Notes |
|---|---|
| `_mId` | Merchant ID |
| `api_key` | Merchant API key (signed, sent in form) |
| `_returnUrl` | Browser redirect after payment: `orderId, trnId, status` |
| `_cancelUrl` | Browser redirect on cancel: status `CANCELED` |
| `_responseUrl` | Server-to-server POST with signed result |
| `_amount` | Decimal string, e.g. `300.00` |
| `_currency` | `LKR` |
| `_reference` | Your reference |
| `_orderId` | Unique per request |
| `_pluginName` | `customapi` |
| `_pluginVersion` | Your version string, e.g. `1.0.1` |
| `_description` | Order description |
| `_firstName`, `_lastName`, `_email` | Customer |
| `_mobileNo` | Used in Koko's PHP samples, not part of `dataString` |
| `dataString` | See below |
| `signature` | base64 RSA-SHA256 of `dataString` |

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
