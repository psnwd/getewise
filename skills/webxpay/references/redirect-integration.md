# Redirect integration (HTML form POST)

## URLs
- Live: `https://webxpay.com/index.php?route=checkout/billing`
- Staging: `https://stagingxpay.info/index.php?route=checkout/billing` (the old guide calls it "Sandbox" in places; test cards and staging MIDs are published in the Token v2.2 guide — see `plugins.md`)

## Request: HTTP POST (form)
| Param | Req | Rule |
|---|---|---|
| `first_name`, `last_name` | yes | max 30 |
| `email` | yes | valid email |
| `contact_number` | yes | 9-20 chars, digits and `+` only |
| `address_line_one` | yes | |
| `address_line_two`, `city`, `state`, `postal_code`, `country` | no | |
| `secret_key` | yes | Dashboard > Settings > Integrations |
| `payment` | yes | encrypted order+amount (below) |
| `cms` | yes | platform label: `PHP`, `WooCommerce`, `Magento`, `iOS`... |
| `process_currency` | yes | `LKR`, `USD`, `GBP`, `AUD` |
| `custom_fields` | no | base64 of up to 4 pipe-separated values. `custom_fields` is the real name; `custom_feilds` is a typo that appears only in the request table of the guide |
| `payment_gateway_id` | no | one gateway ID, skips the selection page |
| `multiple_payment_gateway_ids` | no | pipe-separated IDs, e.g. `40|44|96`. Documented in the guide's §2.5.1, just missing from the parameter table |
| `enc_method` | yes (fixed) | every official sample and plugin sends the literal `JCs3J+6oSz4V0LgE0zi/Bg==`. It is not an algorithm selector and its meaning is unpublished — send it verbatim |

## One-click / saved card via redirect (undocumented)
The redirect flow has its own card-saving mechanism, separate from Token V2. The official WooCommerce plugin adds three fields that appear in no parameter table:
| Param | Value |
|---|---|
| `token_parameter` | base64(RSA_encrypt(public key, `userID\|email\|timestamp`)) |
| `is_tokenize` | `true` |
| `version` | `5.2` |
The portal then offers the customer a one-click payment. Treat this as plugin-derived, not contractual.

## Building `payment`
1. Plain text: `unique_order_id|total_amount`, e.g. `12001|2567.50` (the sample also uses `525|1000`; use 2 decimals).
2. Encrypt with WebXPay's **public key** (PEM, Dashboard > Settings > Integration Information) using RSA with **PKCS#1 v1.5** padding (PHP `openssl_public_encrypt` default; the docs never name the padding, so this is inferred from that function).
3. Base64-encode the ciphertext. Max plaintext for a 1024-bit key is 117 bytes: keep order ids short. For larger keys it is `keybytes - 11`.

## Return / response
Set the return URL in Dashboard > Settings > Website Integration. The browser is redirected there and POST fields arrive:
- `payment` (base64), `signature` (base64), `custom_fields` (base64).
Steps:
1. `payment_plain = base64_decode(payment)`. It is **not encrypted**; it is the pipe string. (The guide says to "decrypt" it too; the samples only verify `signature`. If it contains `|` after decoding, use it as is.)
2. Verify `signature` over `payment_plain` as **RSA-PSS / SHA-1, 20-byte salt**. Node: `setOptions({signingScheme:"pss-sha1"})` + `verify()`; .NET: `PssSigner(new RsaEngine(), new Sha1Digest(), 20)`; PHP 8.1+: `openssl_verify($pay, $sig, $pub, OPENSSL_ALGO_SHA1)` will not do it — use a PSS-capable library. Python: `padding.PSS(mgf=MGF1(SHA1()), salt_length=20)` with `hashes.SHA1()` (see `scripts/webxpay_crypto.py`).
3. Legacy fallback only: the old PHP sample `openssl_public_decrypt` + string compare (PKCS#1 v1.5 type-1 recovery, `s^e mod n`, strip `00 01 FF.. 00`). A captured 2024 response has no type-1 padding, so this path cannot validate current traffic — keep it only for old captures.
4. Parse `payment_plain` = `order_id|order_reference_number|date_time_transaction|status_code|comment|payment_gateway_used|requested_amount|transaction_amount`, e.g. `24.6367|T315972024I13|2024-02-13 10:16:28|0|00 - APPROVED|93|100.00|100.00`. The 2016 example stops at `payment_gateway_used`. Trim whitespace, treat index 3 as status and 4 as comment, and read 5-7 only if present.
5. `custom_fields`: base64-decode, split on `|`.

Status codes (gateway dependent): `0` / `00` approved, `15` declined; a real response carries `0` in the code slot and `00 - APPROVED` in the comment slot (others come from the bank/gateway; see `troubleshooting.md`).
Amount: newer responses include `requested_amount` and `transaction_amount` (fields 6 and 7) and the WooCommerce plugin reads them; the 2016 six-field response does not. Never treat either as authoritative — compare against your DB and confirm via Transaction Retrieval when the stakes are high.

## Validation errors (returned on the WebXPay page)
401-424, see `troubleshooting.md`. Show customers clear success / incomplete messages.
