# Redirect integration (HTML form POST)

## URLs
- Live: `https://webxpay.com/index.php?route=checkout/billing`
- Staging: `https://stagingxpay.info/index.php?route=checkout/billing` (the page never says "sandbox"; no test cards are published, ask WebXPay)

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
| `custom_fields` | no | base64 of up to 4 pipe-separated values (the table spells it `custom_feilds`; the PHP sample uses `custom_fields`) |
| `payment_gateway_id` | no | one gateway ID, skips the selection page |
| `multiple_payment_gateway_ids` | no | pipe-separated IDs, e.g. `40|44|96` (in the sample form and Gateway-ID page, not the param table) |
| `enc_method` | sample only | the official PHP sample form posts `enc_method` with a fixed base64 value; the guide never explains it. Mirror the sample if WebXPay requires it, and ask support what it does |

## Building `payment`
1. Plain text: `unique_order_id|total_amount`, e.g. `12001|2567.50` (the sample also uses `525|1000`; use 2 decimals).
2. Encrypt with WebXPay's **public key** (PEM, Dashboard > Settings > Integration Information) using RSA with **PKCS#1 v1.5** padding (PHP `openssl_public_encrypt` default; the docs never name the padding, so this is inferred from that function).
3. Base64-encode the ciphertext. Max plaintext for a 1024-bit key is 117 bytes: keep order ids short. For larger keys it is `keybytes - 11`.

## Return / response
Set the return URL in Dashboard > Settings > Website Integration. The browser is redirected there and POST fields arrive:
- `payment` (base64), `signature` (base64), `custom_fields` (base64).
Steps:
1. `payment_plain = base64_decode(payment)`. In the official sample this is **not encrypted**; it is the pipe string. (The guide text says to "decrypt" it too; the sample code and the signature check only decrypt `signature`. Handle both: if it contains `|` after decoding, use it as is.)
2. `sig_plain = RSA public-decrypt(base64_decode(signature), public_key)` (PKCS#1 v1.5 type-1 signature recovery). PHP: `openssl_public_decrypt`. Node: `crypto.publicDecrypt`. Java: `Cipher RSA/ECB/PKCS1Padding` in DECRYPT_MODE with the public key. Go/Python/Rust: modular exponentiation `s^e mod n`, strip the `00 01 FF.. 00` padding (see `code-examples.md`).
3. Authentic if `sig_plain == payment_plain` (use a constant-time compare).
4. Parse `payment_plain` = `order_id|order_reference_number|date_time_transaction|status_code|comment|payment_gateway_used`, e.g. `12001|T372016I24522| 2016-04-20 09:57:52|15| No such issuer|1`. Trim whitespace.
5. `custom_fields`: base64-decode, split on `|`.

Status codes (gateway dependent): `0` / `00` approved, `15` declined (others come from the bank/gateway; see `troubleshooting.md`).
Your DB must supply the amount: the response string does not include it. Check order id exists and is unpaid, and confirm the amount via Transaction Retrieval if the stakes are high.

## Validation errors (returned on the WebXPay page)
401-424, see `troubleshooting.md`. Show customers clear success / incomplete messages.
