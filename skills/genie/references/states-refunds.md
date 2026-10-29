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
| `AUTHORIZED` | pre-authorised (if supported on your account) | can be captured within 7 days; `capturedAmount`, `preauthorizedAmount` and `preauthorizedExpiryDate` exist on the object. The public docs show no capture endpoint in the pages we read; ask support |

Model order status as: pending (INITIATED/QR_CODE_GENERATED), paid (CONFIRMED), closed-unpaid (CANCELLED/FAILED), reversed (VOIDED/REFUND_*).

## Refund
`POST {base}/public/transactions/{transactionId}/refunds`, `Authorization` header, JSON:
```json
{ "refundAmount": 500, "refundReason": "Customer returned item" }
```
- `refundAmount`: number, required. The docs don't state the unit. Everything else in the API is minor units, so assume minor units, test on UAT with a small amount and confirm with Genie support before refunding real money.
- `refundReason`: string, required, max 255.
- Response: a transaction object. Check `refundTransactions[]`, `refundExpiryDate`, and the object's `canRefundIfConfirmed`, `canPartialRefundIfConfirmed`, `canIncrementalPartialRefundIfConfirmed` flags before calling.
- Refunds are reviewed, so the state goes `REFUND_REQUESTED` before `REFUNDED`. Track it through webhooks or Get Transaction.
- Refund window: see `refundExpiryDate`; policy details (fees on refunds, time limits) aren't public, ask support.
- Guard your own endpoint: only staff, check the order was CONFIRMED, cap total refunded at the paid amount, record the reason.
