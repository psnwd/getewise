# Koko callbacks

## `_responseUrl` (server-to-server, authoritative)
Koko POSTs `application/x-www-form-urlencoded` on success:

| Field | Notes |
|---|---|
| `orderId` | Your `_orderId` |
| `trnId` | Koko transaction ID |
| `status` | `SUCCESS` |
| `desc` | Empty on success |
| `signature` | base64 RSA-SHA256 by Koko's private key |

Signed data: `orderId + trnId + status` (concatenated, no separators). Verify with **Koko's public key** (PKCS#1 v1.5, SHA-256).

Handler:
1. Parse form, verify signature; reject (400) if bad.
2. Load order by `orderId`; check it exists and is not already paid.
3. Mark paid, store `trnId`. Idempotent: Koko may retry.
4. Respond 200.

## `_returnUrl` / `_cancelUrl` (browser)
Query/form fields `orderId, trnId, status`. `status`: `SUCCESS`, `FAILURE` on return; `CANCELED` on cancel. **Unsigned** and user-controllable: show a result page, but read the real state from your DB (set by `_responseUrl`) or `orderView`.

`python scripts/koko_sign.py verify ...` checks a callback signature while debugging.
