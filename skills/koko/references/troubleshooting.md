# Koko troubleshooting

## Common failures
| Symptom | Likely cause |
|---|---|
| Signature/invalid request error | `dataString` field order wrong; value posted differs from value signed (e.g. `300` vs `300.00`); wrong private key; Koko has a different public key on file |
| Works in QA, fails in prod | Prod `_mId`, `api_key`, key pair are different from QA |
| Duplicate order error | `_orderId` reused; must be unique per request |
| Callback never arrives | `_responseUrl` not public/HTTPS, behind auth/CSRF middleware, or not 200; fall back to `orderView` |
| Callback signature fails | Wrong Koko public key (env mismatch), or wrong concatenation (`orderId+trnId+status`) |
| Order marked paid on return page | Don't: `_returnUrl` is unsigned; use `_responseUrl`/`orderView` |

## Doc gaps (flag, don't invent)
- PDF mentions an auth header, but all samples send credentials as form fields.
- `api_key` is described as encrypted; samples send it plain.
- Hash used for callback signature is unnamed; SHA-256 assumed (matches the request).
- No error-code list, refund API, test cards, or `orderView` response signature definition.
- `_mobileNo` appears in PHP samples but not in `dataString`.
- `desc` on failure is undocumented.

## Go-live checklist
- Prod `_mId`, `api_key`, key pair, Koko prod public key in env vars
- `_responseUrl` public HTTPS, idempotent
- Amount from DB, `_orderId` unique
- Reconciliation job using `orderView` for PENDING orders
- Private key not in repo
