# Transaction states and refunds

## States
| State | Meaning | What to do |
|---|---|---|
| `INITIATED` | created; ephemeral | customer can pay; moves to `QR_CODE_GENERATED` when the QR asset is ready. Don't wait on it unless you need the QR PNG |
| `QR_CODE_GENERATED` | pending, awaiting the customer | applies to cards and redirect wallets too, not just QR |
| `CONFIRMED` | paid, funds confirmed | the only "paid" state; fulfil the order |
| `CANCELLED` | customer cancelled or it timed out | link is dead; create a new transaction |
| `FAILED` | payment failed, permanently | link/method can't be reused; create a new one |
| `VOIDED` | reversed | won't appear in settlements, no processing fee |
| `REFUND_REQUESTED` | refund asked, under review by the gateway team (merchant balance check) | original still shows CONFIRMED; a new transaction (partial or full amount) references it |
| `REFUNDED` | refund completed, funds returned | |
| `AUTHORIZED` | pre-authorised (if supported on your account) | can be captured within 7 days; `capturedAmount`, `preauthorizedAmount`, `preauthorizedExpiryDate` and `isPreAuthorization` exist on the object. There is no public capture endpoint (not in the docs, spec-mock or SDKs); ask support |

Model order status as: pending (INITIATED/QR_CODE_GENERATED), paid (CONFIRMED), closed-unpaid (CANCELLED/FAILED), reversed (VOIDED/REFUND_*).

## Refund
`POST {base}/public/transactions/{transactionId}/refunds`, `Authorization` header, JSON:
```json
{ "refundAmount": 500, "refundReason": "Customer returned item" }
```
- `refundAmount`: a **number**, required; the schema accepts decimals (spec-mock, `1.5` accepted, `"x"` rejected as "must be number"). The docs state **no unit**, and their examples are decimals: `100.00` and `50.25`. The schema allows decimals and no prose states the unit — refund a small amount on UAT and observe before refunding real money.
- `refundReason`: string, required, max 255.
- Response: a transaction object. Check `refundTransactions[]`, `refundExpiryDate`, and the object's `canRefundIfConfirmed`, `canPartialRefundIfConfirmed`, `canIncrementalPartialRefundIfConfirmed` flags before calling.
- Refunds are reviewed, so the state goes `REFUND_REQUESTED` before `REFUNDED`. Track it through webhooks or Get Transaction.
- Refund window: see `refundExpiryDate`; the time limit isn't published, and the pricing page lists an MCP refund fee of USD 50 (see `environments-account.md`). Ask support for the rest.
- Guard your own endpoint: only staff, check the order was CONFIRMED, cap total refunded at the paid amount, record the reason.
