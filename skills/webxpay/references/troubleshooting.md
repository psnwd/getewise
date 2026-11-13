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
- Return handler says signature invalid: you used `openssl_verify` with PKCS#1 v1.5 and SHA-256. The current scheme is **RSA-PSS / SHA-1, 20-byte salt**, verified against the raw `payment` bytes; the old PHP sample's public-decrypt + compare does not work on current responses. Also decode base64 on both fields first, and don't verify the base64 text instead of the decoded bytes.
- Decryption of your own `payment` fails at the checkout page / 401 / 403: wrong padding — PKCS#1 v1.5 is the safe default (`openssl_public_encrypt`), but the official Node and .NET samples use OAEP-SHA1, so retry with OAEP if v1.5 is rejected. Also wrong key (staging key on live), plaintext too long for the key, plaintext not exactly `order|amount`, missing `secret_key`.
- Customer returns but nothing arrives: return URL not set in the portal; or your handler only accepts GET (it's a POST).
- Order marked paid from the return alone: forged POST. Check the signature and DB amount.
- Gateway doesn't show: not enabled for the merchant, currency mismatch (LKR-only gateways with `process_currency=USD`).

## Gaps and contradictions in the official docs (re-checked 13 Nov 2026)
- RSA padding for the request is never named. The guide and the PHP/JS samples and plugins imply PKCS#1 v1.5 (`openssl_public_encrypt`); the official Node (`node-rsa`, default OAEP-SHA1) and .NET (`rsa.Encrypt(..., true)`) samples use OAEP-SHA1. Try v1.5, then OAEP.
- The return-signature scheme is described three ways: "checksum", `openssl_public_decrypt` + compare (PHP sample, legacy), and RSA-PSS/SHA-1 (Node and .NET samples, and the only scheme a captured 2024 response verifies under). Trust PSS first, keep recovery as a fallback.
- Response field count: the 2016 doc example has six fields and says the response carries no amount; a 2024 capture and the WooCommerce plugin have eight, ending `|gateway_id|requested_amount|transaction_amount`. Parse defensively.
- `custom_feilds` (table) vs `custom_fields` (everywhere else); `multiple_payment_gateway_ids` and `enc_method` appear only in the sample form / §2.5.1, not the parameter table. `enc_method` is a fixed literal, not a selector.
- Staging is `stagingxpay.info` and is called "Sandbox" only in the Token v2.2 guide. Test cards, staging MIDs and sample staging `secret_key`s **are** published there; the redirect guide just doesn't mention them.
- The sample PHP form puts `secret_key` in a hidden HTML field (visible to users).
- The sample's signature script lacks input checks and constant-time compare.
- **Refunds: no public API.** The nav "Refund API" entry is a dead button (no href), four probed paths 404, the pack it references (`webxpay.com/Webxpay-Tokenization/Files.zip`) 302s to the homepage, the Magento module sets `$_canRefund = false`, the WHMCS refund function is an empty stub, and the WooCommerce plugin contains no refund code. Refund through the merchant portal or ask WebXPay; `refundStatus: true` on a card-save response is a capability flag, not an endpoint.
- Retrieval API: methods and fields were screenshots in the old page; the downloadable Postman collections give the real paths and the response screenshot is legible. Fields are listed in `merchant-retrieval-api.md`. There is no card mask and no signature.
- Gateway id `93` appears in a real response but is absent from the published 2-102 list.
- Return status codes depend on the gateway and only `0`/`00` approved and `15` declined are published; a real payload puts `0` in the status slot and `00 - APPROVED` in the comment slot. There is no per-gateway table.
- Amount ceilings behind errors 410/411 are never published; minimum is 1 LKR / 1 USD (error 409).
- No server-to-server webhook exists in either product: redirect posts to the configured Return URL, Token V2 returns to `secure3dResponseURL?result3ds=<base64>`.
- Idempotency: no `Idempotency-Key` anywhere. Token V2's only guard is `orderNumber` uniqueness (`ORDER_NUMBER_DUPLICATE`, 409); redirect checkout has none.
