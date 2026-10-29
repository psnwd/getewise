# Code: build `payment`, verify the return (7 languages)

Two operations, same everywhere (keys: WebXPay PEM public key from the dashboard, env `WEBXPAY_PUBLIC_KEY`, `WEBXPAY_SECRET_KEY`):
1. **Build:** `base64( RSA-PKCS1v15-encrypt( pubkey, "order_id|2567.50" ) )`
2. **Verify:** `base64decode(signature)` → RSA public-decrypt (PKCS#1 v1.5 type-1 recovery) → must equal `base64decode(payment)`; then split on `|`.

Run and verified against a PHP (OpenSSL) reference with a throwaway 1024-bit key: PHP, Node, Python, Go, Java, Rust (encrypt output decrypted by PHP with the private key; signature made by PHP `openssl_private_encrypt` recovered by each language). **C# was not compiled** (no dotnet here).
After verifying, always load your order by `order_id`, check it is unpaid and the amount matches your DB, then act on `status_code` (`0`/`00` = approved), idempotently.

## PHP / Laravel
```php
function wx_payment(string $orderId, float $amount, string $pubPem): string {
    openssl_public_encrypt($orderId.'|'.number_format($amount, 2, '.', ''), $enc, $pubPem, OPENSSL_PKCS1_PADDING);
    return base64_encode($enc);
}
function wx_verify(string $payment, string $signature, string $pubPem): ?array {
    $pay = base64_decode($payment, true); $sig = base64_decode($signature, true);
    if ($pay === false || $sig === false || !openssl_public_decrypt($sig, $rec, $pubPem)) return null;
    if (!hash_equals($rec, $pay)) return null;
    [$orderId, $ref, $dt, $status, $comment, $gw] = array_map('trim', explode('|', $pay) + array_fill(0, 6, ''));
    return compact('orderId', 'ref', 'dt', 'status', 'comment', 'gw');
}
// Laravel: exempt the return route from CSRF (it's a cross-site POST), then Route::post('/webxpay/return', ...).
```

## Node / TypeScript
```ts
import { constants, publicEncrypt, publicDecrypt, timingSafeEqual } from 'node:crypto';
const PUB = process.env.WEBXPAY_PUBLIC_KEY!;                  // PEM
export const wxPayment = (orderId: string, amount: number) =>
  publicEncrypt({ key: PUB, padding: constants.RSA_PKCS1_PADDING }, Buffer.from(`${orderId}|${amount.toFixed(2)}`)).toString('base64');
// NOTE: without `padding` Node uses OAEP, which WebXPay will reject.
export function wxVerify(payment: string, signature: string) {
  const pay = Buffer.from(payment, 'base64');
  let rec: Buffer;
  try { rec = publicDecrypt({ key: PUB, padding: constants.RSA_PKCS1_PADDING }, Buffer.from(signature, 'base64')); } catch { return null; }
  if (rec.length !== pay.length || !timingSafeEqual(rec, pay)) return null;
  const [orderId, ref, dt, status, comment, gw] = pay.toString().split('|').map(s => s.trim());
  return { orderId, ref, dt, status, comment, gw };
}
// Express: app.post('/webxpay/return', express.urlencoded({ extended: false }), (req, res) => { ... })
```

## Python
```python
import base64, hmac, os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
PUB = serialization.load_pem_public_key(os.environ["WEBXPAY_PUBLIC_KEY"].encode())

def wx_payment(order_id: str, amount: float) -> str:
    return base64.b64encode(PUB.encrypt(f"{order_id}|{amount:.2f}".encode(), padding.PKCS1v15())).decode()

def _public_decrypt(sig: bytes) -> bytes:
    n = PUB.public_numbers(); k = (n.n.bit_length() + 7) // 8
    em = pow(int.from_bytes(sig, "big"), n.e, n.n).to_bytes(k, "big")
    if em[:2] != b"\x00\x01": raise ValueError("bad padding")
    return em[em.index(b"\x00", 2) + 1:]

def wx_verify(payment_b64: str, signature_b64: str):
    pay = base64.b64decode(payment_b64)
    try: rec = _public_decrypt(base64.b64decode(signature_b64))
    except Exception: return None
    if not hmac.compare_digest(rec, pay): return None
    f = [p.strip() for p in pay.decode().split("|")]
    return dict(zip(["order_id", "ref", "datetime", "status", "comment", "gateway"], f))
```

## Go
```go
func wxPayment(pub *rsa.PublicKey, orderID string, amount float64) (string, error) {
	ct, err := rsa.EncryptPKCS1v15(rand.Reader, pub, []byte(fmt.Sprintf("%s|%.2f", orderID, amount)))
	return base64.StdEncoding.EncodeToString(ct), err
}
// Go has no public-decrypt: do s^e mod n and strip the PKCS#1 type-1 padding.
func wxVerify(pub *rsa.PublicKey, paymentB64, sigB64 string) ([]string, bool) {
	pay, e1 := base64.StdEncoding.DecodeString(paymentB64)
	sig, e2 := base64.StdEncoding.DecodeString(sigB64)
	if e1 != nil || e2 != nil { return nil, false }
	m := new(big.Int).Exp(new(big.Int).SetBytes(sig), big.NewInt(int64(pub.E)), pub.N)
	em := make([]byte, (pub.N.BitLen()+7)/8)
	m.FillBytes(em)
	if em[0] != 0 || em[1] != 1 { return nil, false }
	i := bytes.IndexByte(em[2:], 0) + 2
	if subtle.ConstantTimeCompare(em[i+1:], pay) != 1 { return nil, false }
	parts := strings.Split(string(pay), "|")
	for j := range parts { parts[j] = strings.TrimSpace(parts[j]) }
	return parts, true // order_id, ref, datetime, status, comment, gateway
}
// load key: blk, _ := pem.Decode(pemBytes); k, _ := x509.ParsePKIXPublicKey(blk.Bytes); pub := k.(*rsa.PublicKey)
```

## Java
```java
static String wxPayment(PublicKey pub, String orderId, BigDecimal amount) throws Exception {
    Cipher c = Cipher.getInstance("RSA/ECB/PKCS1Padding"); c.init(Cipher.ENCRYPT_MODE, pub);
    String plain = orderId + "|" + amount.setScale(2, RoundingMode.HALF_UP).toPlainString();
    return Base64.getEncoder().encodeToString(c.doFinal(plain.getBytes(StandardCharsets.UTF_8)));
}
static String[] wxVerify(PublicKey pub, String paymentB64, String sigB64) throws Exception {
    byte[] pay = Base64.getDecoder().decode(paymentB64);
    Cipher d = Cipher.getInstance("RSA/ECB/PKCS1Padding"); d.init(Cipher.DECRYPT_MODE, pub);  // public-key "decrypt" = signature recovery
    byte[] rec = d.doFinal(Base64.getDecoder().decode(sigB64));
    return MessageDigest.isEqual(rec, pay) ? new String(pay, StandardCharsets.UTF_8).split("\\|") : null;
}
// key: KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der))  (strip PEM header/footer, base64-decode)
```

## Rust (`rsa` 0.9 with `pem`, `base64`, `rand` 0.8)
```rust
use base64::{engine::general_purpose::STANDARD as B64, Engine};
use rsa::{pkcs8::DecodePublicKey, traits::PublicKeyParts, BigUint, Pkcs1v15Encrypt, RsaPublicKey};

fn wx_payment(pem: &str, order_id: &str, amount: f64) -> String {
    let key = RsaPublicKey::from_public_key_pem(pem).unwrap();
    let ct = key.encrypt(&mut rand::thread_rng(), Pkcs1v15Encrypt, format!("{order_id}|{amount:.2}").as_bytes()).unwrap();
    B64.encode(ct)
}
fn wx_public_decrypt(pem: &str, sig_b64: &str) -> Option<Vec<u8>> {
    let key = RsaPublicKey::from_public_key_pem(pem).ok()?;
    let s = BigUint::from_bytes_be(&B64.decode(sig_b64.trim()).ok()?);
    let k = ((key.n().bits() + 7) / 8) as usize;
    let em = s.modpow(key.e(), key.n()).to_bytes_be();
    let mut p = vec![0u8; k - em.len()]; p.extend(em);
    if p.get(0..2)? != [0x00, 0x01] { return None; }
    let i = p[2..].iter().position(|&b| b == 0)? + 2;
    Some(p[i + 1..].to_vec())            // compare with base64-decoded `payment` in constant time
}
```

## C# (not compiled)
```csharp
static string WxPayment(RSA pub, string orderId, decimal amount) =>
    Convert.ToBase64String(pub.Encrypt(
        Encoding.UTF8.GetBytes($"{orderId}|{amount.ToString("0.00", CultureInfo.InvariantCulture)}"),
        RSAEncryptionPadding.Pkcs1));
// .NET has no public-decrypt either: do BigInteger.ModPow(sig, e, n) using pub.ExportParameters(false)
// (Modulus, Exponent are big-endian: Array.Reverse before `new BigInteger(..., isUnsigned: true)` or use isBigEndian: true),
// left-pad to key size, require 00 01 FF..FF 00, then CryptographicOperations.FixedTimeEquals(rest, payBytes).
// Load key: var pub = RSA.Create(); pub.ImportFromPem(pem);
```

## HTML form
```html
<form method="POST" action="https://webxpay.com/index.php?route=checkout/billing">  <!-- staging: https://stagingxpay.info/... -->
  <input name="first_name"><input name="last_name"><input name="email"><input name="contact_number">
  <input name="address_line_one">
  <input type="hidden" name="process_currency" value="LKR">
  <input type="hidden" name="cms" value="PHP">
  <input type="hidden" name="secret_key" value="…server-rendered…">
  <input type="hidden" name="payment" value="…server-built…">
  <button>Pay</button>
</form>
```
Render `payment` per order on the server; never expose the plaintext builder to the browser.
