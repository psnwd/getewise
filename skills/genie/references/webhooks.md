# Webhooks

## Contents
1. How to register
2. What arrives
3. Verifying the signature
4. Processing rules
5. Deprecated signature

## 1. How to register
| Way | How |
|---|---|
| Global webhook | Merchant dashboard, Connect > Webhooks. Receives every event for every transaction |
| Single transaction | `webhook` field on Create Transaction |
| Webhook Apps | create/delete programmatically via the Create Webhook API (Stoplight "Webhooks" group); useful for Zapier/IFTTT and for segmenting events. A new webhook app also receives updates for existing transactions |

If several are configured, the event is POSTed to all active ones, so your handler can see the same event twice. Make it idempotent.

## 2. What arrives
HTTP `POST`, JSON body, header `X-Originator: PomeloPay-Webhooks` (the platform's former name), plus the signature headers below. Respond `200` quickly.

`NOTIFY_TRANSACTION_CHANGE` body (fields from the docs' sample):
```json
{
  "eventType": "NOTIFY_TRANSACTION_CHANGE",
  "companyId": "64646727335b730008db10f8",
  "transactionId": "6482d462ce6c690008e85e42",
  "localId": null,
  "customerReference": null,
  "state": "CONFIRMED",
  "amount": 1400,
  "amountFractional": 14,
  "amountFormatted": "LKR 14.00",
  "currency": "LKR",
  "provider": "card_payments",
  "securityWord": "EXHILARATING TOAD",
  "signature": "wzczRUp5i/0DqS5LzGVQUw==",
  "originalSignature": "wzczRUp5i/0DqS5LzGVQUw==",
  "qrCode": { "url": "https://qr..." },
  "externalSource": "Genie Business Gateway",
  "id": "6482e6f5bcf6fa0008683c2f"
}
```
Note `amountFractional` is `14` for 1400 minor units in this sample and `53.2` for `5320` in another; it is the decimal amount. `id` is the event ID; `transactionId` is the transaction.

`NOTIFY_TOKENISATION_STATUS` (card on file): has `customerId`, `transactionId`, `provider`, `tokenisationStatus` (e.g. `TOKENISATION_SUCCESS`). Then list the customer's tokens.

## 3. Verifying the signature
Headers sent with the webhook:
- `X-Signature-Nonce`: unique ID for the request
- `X-Signature-Timestamp`: when it was sent
- `X-Signature`: the signature

Algorithm (documented):
```
signString = nonce + timestamp + apiKey      // plain string concatenation
expected   = hex( SHA-256(signString) )
valid      = (expected == X-Signature)       // compare in constant time
```
Header names are case-insensitive in HTTP, so read them case-insensitively (Node lowercases them). Use the API key of the same environment (UAT vs production).

Limits, said plainly: the signature covers only nonce + timestamp + key, not the body. Anyone who captured one valid request's headers could replay them with a different body. So:
1. Verify the headers (stops casual spoofing).
2. Optionally reject old timestamps and remember nonces (our suggestion; the docs don't specify the timestamp format or tolerance).
3. **Always re-query the transaction** and decide from the API response, never from the webhook body. The docs say the same.

`scripts/genie_webhook.py` computes and checks this.

## 4. Processing rules
- Use `transactionId` to call Get Transaction; require `state == CONFIRMED`, and compare `amount`, `currency` and `localId` with your order.
- Idempotency: key on `transactionId` (+ final state). Refund events also arrive as transaction changes.
- Don't ship goods on the redirect or on the webhook body alone.
- The route must be public HTTPS (localhost won't work; tunnel in dev) and exempt from CSRF/auth middleware; parse JSON.
- Docs don't publish source IPs, so don't IP-filter.

## 5. Deprecated signature
The body field `originalSignature` is documented as deprecated: `base64(md5(querystring({amount, currency, apiKey})))`. A sample in the card-on-file page shows a 40-hex value there (sha1-looking), and the main sample a short base64 one, so the field is not consistent across the docs. Don't build on it. Prefer the header signature plus an API re-query.
