# Troubleshooting and doc gaps

## WebXPay checkout error codes (redirect)
| Code | Meaning |
|---|---|
| 401 | Invalid access |
| 402 | Can't identify product |
| 403 | Invalid secret key (wrong env, wrong key, stray whitespace) |
| 405 / 406 / 407 / 408 | first name / last name / email / contact number required |
| 409 | Amount below 1 USD / 1 LKR |
| 410 / 411 | LKR / USD amount exceeds the limit |
| 412 / 417 | Unsupported / undefined currency code |
| 413 | Gateways not found |
| 414 / 415 | Selected gateway not found / invalid gateway ID |
| 416 | No bank response |
| 418 | Return URL missing (set it in Settings > Website Integration) |
| 419 / 420 / 421 | Transaction blocked for this IP / email / merchant |
| 423 | Generic processing error |
| 424 | Invalid request URL |
The error page also lists Mastercard HTTP-style codes (200/201/202, 400-405, 409, 429, 500/5XX; 402 = declined) and a long Visa/CyberSource reason-code table (100 ok, 101 missing fields, 204 insufficient funds, 205 lost/stolen, 209 CVN mismatch, 210 limit, 220 generic decline, 400 fraud score, 465 payer-auth failed, 478 SCA required, 481 Decision Manager reject, ...). Return-status codes depend on the gateway; `0`/`00` approved, `15` declined.

## Common problems
- Decryption fails at WebXPay / 401 / 403: wrong padding (use PKCS#1 v1.5, not OAEP: Node's `publicEncrypt` defaults to OAEP!), wrong key (staging key on live), plaintext too long for the key, plaintext not exactly `order|amount`, missing `secret_key`.
- Return handler says signature invalid: you used `openssl_verify`/RSA-SHA256 verify. The scheme is raw public-decrypt compared with the `payment` string. Also decode base64 on both fields first.
- Customer returns but nothing arrives: return URL not set in the portal; or your handler only accepts GET (it's a POST).
- Order marked paid from the return alone: forged POST. Check the signature and DB amount.
- Gateway doesn't show: not enabled for the merchant, currency mismatch (LKR-only gateways with `process_currency=USD`).

## Gaps and contradictions in the official docs (flag these)
- RSA padding is never named; decryption of the response "with the public key" sounds odd but is correct for RSA signature recovery. The guide text says to decrypt `payment`, but the official sample only decrypts `signature` and compares it with the base64-decoded `payment`.
- `custom_feilds` (table) vs `custom_fields` (sample); `multiple_payment_gateway_ids` and `enc_method` appear only in the sample form / Gateway-ID page, not the parameter table.
- Staging is `stagingxpay.info` but is never called sandbox; no test cards or test keys are published.
- The sample PHP form puts `secret_key` in a hidden HTML field (visible to users).
- The sample's signature script lacks input checks and constant-time compare.
- Nav lists Pay From Session, Card Saving, Get Cards, Pay From Token, Card Deletion and Refund APIs, but the Merchant API page only documents login; Token V2 covers saved cards and MIT but no refund endpoint is described.
- Retrieval page: HTTP methods and response fields are in images; second endpoint text says it returns an "auth token".
- The only documented refund route is not on the public site: ask WebXPay (or use the merchant portal).
