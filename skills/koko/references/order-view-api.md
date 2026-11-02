# Merchant Order View API

Server-side status lookup. `POST {host}/api/merchants/orderView`, form-urlencoded.

| Field | Notes |
|---|---|
| `_mId` | Merchant ID |
| `api_key` | Merchant API key |
| `_orderId` | Order to look up |
| `_pluginName` | `customapi` |
| `_pluginVersion` | Your version |
| `signature` | base64 RSA-SHA256 over `dataString` |

`dataString = _mId + _pluginName + _pluginVersion + _orderId + api_key` (no separators). Signed with the merchant private key.

## Response
`orderId, trnId, status, desc, signature`; `status` is `PENDING`, `SUCCESS` or `FAILED`. Response `signature` is by Koko; verify it as in `callbacks.md` (the PDF does not spell out the signed string; assume `orderId+trnId+status` and flag that).

Use for: missing callback, reconciliation jobs, double-checking before fulfilment.
