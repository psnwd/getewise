# Troubleshooting and doc gaps

## Errors (create transaction)
| HTTP | Meaning / fix |
|---|---|
| 200 | Checkout link generated |
| 400 | Invalid body: invalid app ID, invalid amount, invalid app state (app not active), currency not enabled for the app |
| 401 | `Authorization` header missing, invalid App Token, or wrong hash. Recheck: hash formula, amount string identical in hash and body (`100.00`), live vs sandbox credentials |
| 429 | Rate limit per App ID. Back off exponentially; ask support for higher limits |
5xx and transaction status codes are not documented.

## Common problems
- Hash mismatch: concatenation order is app_id, currency, amount, salt; amount formatted differently in hash vs body; wrong environment's salt; locale turning `.` into `,` (Java/C#/Go).
- Customer lands back but order unpaid: you relied on the return URL. Verify via the status API.
- Callback never arrives: URL not set in the portal APP section; not public; endpoint not returning 200; expects JSON, not form data.
- Phone rejected: not E.164. Redirect rejected: not HTTPS.
- Refund fails on test data: sandbox transactions can't be refunded.

## Gaps and contradictions in the official docs (flag these)
- Create-transaction headers are not listed on the Payment API page, but the Errors page says 401 for missing Authorization/invalid app token, and OnePay JS uses `apptoken` as the Authorization header. Send the App Token.
- Hash casing/encoding unspecified; the auth page says "HMAC" in prose but gives a plain SHA-256 concatenation formula. Use the formula.
- Create response schema unpublished (`redirect_url`, `ipg_transaction_id` are the named fields).
- `transaction_id` (callback), `onepay_transaction_id` (status) and `ipg_transaction_id` (create) are never stated to be identical; they are used interchangeably in examples.
- Callback has no signature, and only status `1`/`SUCCESS` is documented.
- OnePay JS `hashToken` described as "Hash Salt" and as server-generated.
- Payment Link: create body undocumented; `app_id` in query vs body conflict.
- Items: metadata/price/app_id shape differences; "permanently removed" vs `is_deleted` flags; currency LKR/USD vs 10 currencies.
- Docs header shows "API v1" / "v2.4.0" while endpoints are `/v3/`.
- Rate limit "per second" in errors page but unspecified numbers elsewhere.
- Sandbox base URL unpublished.
