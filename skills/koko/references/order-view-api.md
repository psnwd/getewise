# Merchant Order View API

Server-side status lookup. `POST {host}/api/merchants/orderView`, form-urlencoded, no `Content-Type` needed. Returns `application/json`. Hosts: `qaapi` (QA), `prodapi` (live), `devapi` (a third environment with a **separate merchant registry** — QA/prod credentials are not interchangeable).

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
JSON with a `content` wrapper: `content.orderId`, `content.trnId`, `content.status`, `content.desc`, `content.signature`, plus top-level `status` / `statusCode`. `status` is `PENDING`, `SUCCESS` or `FAILED`.

Koko's own WooCommerce plugin **does not verify the response signature** — it only matches `content.orderId` to the request. A third-party SDK claims the view is RSA-signed, but no source states the exact signed string, so treat verification as optional/assumed: if you verify, assume `orderId+trnId+status` as in `callbacks.md` and flag the assumption. Match `content.orderId` regardless.

Use for: missing callback, reconciliation jobs, double-checking before fulfilment.
