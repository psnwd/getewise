# Koko callbacks

## `_responseUrl` (server-to-server, authoritative)
Koko POSTs **either** `application/json` **or** `application/x-www-form-urlencoded`: parse both bodies. The official WooCommerce plugin (3.0.4) handles both, reading the raw body and then `orderId/trnId/status/signature`.

| Field | Notes |
|---|---|
| `orderId` | Your `_orderId` |
| `trnId` | Koko transaction ID |
| `status` | `SUCCESS` |
| `desc` | **Not signed**; do not include it in the verify string. Content on failure undocumented |
| `signature` | base64 RSA-SHA256 by Koko's private key |

Signed data: `orderId + trnId + status` (concatenated, no separators). Algorithm: **RSA-SHA256, PKCS#1 v1.5 padding**, verified with **Koko's public key** — `openssl_verify($orderId.$trnId.$status, base64_decode($sig), $koko_public_key, OPENSSL_ALGO_SHA256)`, exactly as Koko's own WooCommerce plugin does. SHA-1 is not used.

The UltimatePOS Koko module verifies `orderId+trnId+status+desc` (4 fields); that is a likely bug — only reconcilable if `desc` is empty, and it diverges on `FAILED`.

Handler:
1. Parse JSON **or** form body, verify signature.
2. Load order by `orderId`; check it exists and is not already paid.
3. Mark paid, store `trnId`. Idempotent: Koko may retry (undocumented at-least-once model).
4. **Always respond `200 OK`**, even when the signature is missing/invalid, the order is unknown, or an exception is thrown. Non-200 makes Koko retry; log and ignore instead of rejecting with 4xx/5xx.

## `_returnUrl` / `_cancelUrl` (browser)
Query/form fields `orderId, trnId, status`. `status`: `SUCCESS`, `FAILURE` on return; `CANCELED` on cancel. **Unsigned** and user-controllable: show a result page, but read the real state from your DB (set by `_responseUrl`) or `orderView`.

`python scripts/koko_sign.py verify ...` checks a callback signature while debugging.
