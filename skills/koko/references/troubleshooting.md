# Koko troubleshooting

Re-checked 13 Nov 2026 against Koko's official WooCommerce plugin, the support KB and read-only QA probes.

## Common failures
| Symptom | Likely cause |
|---|---|
| Signature/invalid request error | `dataString` field order wrong; value posted differs from value signed (e.g. `300` vs `300.00`); wrong private key; Koko has a different public key on file |
| Works in QA, fails in prod | Prod `_mId`, `api_key`, key pair are different from QA |
| Works in QA, fails on `devapi` | `devapi` is a separate merchant registry; QA/prod credentials do not exist there |
| Duplicate order error | `_orderId` reused; must be unique per request |
| `merchantPluginDetail.apiKey.invalid` with a valid key | `_pluginName`/`_pluginVersion` do not match the plugin registration Koko holds for the MID |
| `corruptted entity ID` | `_mId` (or another entity id) is not a 32-char lowercase hex id |
| Callback never arrives | `_responseUrl` not public/HTTPS, behind auth/CSRF middleware, or not 200; fall back to `orderView` |
| Callback signature fails | Wrong Koko public key (env mismatch), or wrong concatenation (`orderId+trnId+status`, no `desc`) |
| Order marked paid on return page | Don't: `_returnUrl` is unsigned; use `_responseUrl`/`orderView` |

## Observed error responses
Errors come back as JSON, not as `desc` strings:
```json
{"status":"CLIENT_ERROR","statusCode":400,"validationFailures":[{"field":"<field>","code":"<code>"}]}
```
```json
{"status":"SYSTEM_ERROR","statusCode":500}
```
Codes observed against `qaapi` (undocumented, from live probes):

| Code | Field | Meaning |
|---|---|---|
| `corruptted entity ID` | any of the entity IDs | Malformed `_mId`/entity id |
| `OnlineOrderView.signature.error` | `onlineOrderView` | Bad signature on `orderView` |
| `OnlineOrderView.merchant.apiKey.invalid` | `onlineOrderView` | Wrong `api_key` |
| `OnlineOrderView.merchantPluginDetail.notExists` | `onlineOrderView` | MID/plugin not registered on that host |
| `OnlineOrder.create.merchantPluginDetail.notExists` | `onlineOrder` | MID not registered on that host |
| `OnlineOrder.create.merchantPluginDetail.apiKey.invalid` | `onlineOrder` | `api_key` or plugin name/version mismatch |

A bad `orderCreate` signature returns bare HTTP `500` `SYSTEM_ERROR` with no detail — the same response as negative amount, USD currency or a 3-decimal amount, because signature validation runs first. Do not read `SYSTEM_ERROR` as a server outage.

## Resolved doc gaps
- Callback hash is **RSA-SHA256, PKCS#1 v1.5**, over `orderId+trnId+status`; proven by Koko's WooCommerce plugin.
- `api_key` is **plaintext**, compared literally; nothing decodes or decrypts it.
- **No auth header** exists; `_mId` + `api_key` form fields are the whole credential.
- `_mobileNo` is **not** part of `dataString` (15-part string); both known integrations post it anyway.
- `desc` is **not signed** and is not part of the verify string.
- Refunds: **portal-only, full refunds only**, no API.

## Still open (flag, don't invent)
- `orderView` response signed string (Koko's plugin never verifies it; `orderId+trnId+status` is an assumption).
- Whether `_mobileNo` is required (signature/plugin checks fail first, so it cannot be isolated).
- Checkout URL expiry, min/max order amount, partial capture, merchant-initiated cancel API, callback retry schedule.
- No `desc` values, no test cards, no API version or changelog.

## Go-live checklist
- Prod `_mId`, `api_key`, key pair, Koko prod public key in env vars
- `_responseUrl` public HTTPS, idempotent, always answers `200`
- Amount from DB, `_orderId` unique
- Reconciliation job using `orderView` for PENDING orders
- Private key not in repo
- There is **no public developer-docs site or changelog** — the merchant PDFs are the contract. Before go-live capture the Koko QA public key and a real signed callback sample, and confirm `_pluginName`/`_pluginVersion` against your registration.
