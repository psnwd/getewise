# Code: build `payment`, verify the return (7 languages)

Two operations, same everywhere (keys: WebXPay PEM public key from the dashboard, env `WEBXPAY_PUBLIC_KEY`, `WEBXPAY_SECRET_KEY`):
1. **Build:** `base64( RSA-PKCS1v15-encrypt( pubkey, "order_id|2567.50" ) )` — v1.5 is the safe default; if the gateway rejects the value, retry with OAEP-SHA1 (the official Node/.NET samples use OAEP).
2. **Verify:** keep the base64-decoded `payment` bytes, then check the decoded `signature` with **RSA-PSS / SHA-1, 20-byte salt** (`s` in `payment` is not a hash). Only if that fails, try the legacy PKCS#1 v1.5 type-1 recovery (`s^e mod n`, strip `00 01 FF.. 00`, compare). Then split on `|`.

The PSS verification snippets below were run against a real captured staging response (official Node sample vector: `24.6367…|T315972024I13|2024-02-13 10:16:28|0|00 - APPROVED|93|100.00|100.00`) in Node, Python, Go, Java, C# and Rust on 13 Nov 2026; each accepted the real pair and rejected a tampered copy. **PHP was not run** (no PHP here) — the phpseclib path is documented, the legacy `openssl_public_decrypt` path is what the old sample does. The build half is unchanged from the earlier run against an OpenSSL reference.

After verifying, always load your order by `order_id`, check it is unpaid and the amount matches your DB, then act on `status_code` (`0`/`00` = approved), idempotently.

## PHP / Laravel
```php
// composer require phpseclib/phpseclib:^3.0
use phpseclib3\Crypt\PublicKeyLoader;
use phpseclib3\Crypt\RSA;

function wx_payment(string $orderId, float $amount, string $pubPem): string {
    openssl_public_encrypt($orderId.'|'.number_format($amount, 2, '.', ''), $enc, $pubPem, OPENSSL_PKCS1_PADDING);
    return base64_encode($enc);
}
function wx_verify(string $payment, string $signature, string $pubPem): ?array {
    $pay = base64_decode($payment, true); $sig = base64_decode($signature, true);
    if ($pay === false || $sig === false) return null;
    $rsa = PublicKeyLoader::load($pubPem)
        ->withPadding(RSA::SIGNATURE_PSS)->withHash('sha1')->withMGFHash('sha1')->withSaltLength(20);
    if (!$rsa->verify($pay, $sig)) {
        // Legacy only: PKCS#1 v1.5 type-1 recovery, what the old sample does.
        if (!openssl_public_decrypt($sig, $rec, $pubPem) || !hash_equals($rec, $pay)) return null;
    }
    $names = ['orderId','ref','dt','status','comment','gateway','requestedAmount','transactionAmount'];
    $parts = array_map('trim', explode('|', $pay));
    return array_combine(array_slice($names, 0, count($parts)), $parts);
}
// Laravel: exempt the return route from CSRF (it's a cross-site POST), then Route::post('/webxpay/return', ...).
```

## Node / TypeScript
```ts
import { constants, publicEncrypt, verify as cryptoVerify } from 'node:crypto';
const PUB = process.env.WEBXPAY_PUBLIC_KEY!;                  // PEM
export const wxPayment = (orderId: string, amount: number) =>
  publicEncrypt({ key: PUB, padding: constants.RSA_PKCS1_PADDING }, Buffer.from(`${orderId}|${amount.toFixed(2)}`)).toString('base64');
// NOTE: without `padding` Node uses OAEP; v1.5 is what the plugins use, OAEP is what WebXPay's own Node sample uses.
export function wxVerify(payment: string, signature: string) {
  const pay = Buffer.from(payment, 'base64');
  const ok = cryptoVerify(
    'sha1', pay,
    { key: PUB, padding: constants.RSA_PKCS1_PSS_PADDING, saltLength: 20 },
    Buffer.from(signature, 'base64'),
  );
  if (!ok) return null;
  const [orderId, ref, dt, status, comment, gateway, requestedAmount, transactionAmount] =
    pay.toString().split('|').map(s => s.trim());
  return { orderId, ref, dt, status, comment, gateway, requestedAmount, transactionAmount };
}
// Express: app.post('/webxpay/return', express.urlencoded({ extended: false }), (req, res) => { ... })
```

## Python
```python
import base64, os
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
PUB = serialization.load_pem_public_key(os.environ["WEBXPAY_PUBLIC_KEY"].encode())
FIELDS = ["order_id", "ref", "datetime", "status", "comment",
          "gateway", "requested_amount", "transaction_amount"]

def wx_payment(order_id: str, amount: float) -> str:
    return base64.b64encode(PUB.encrypt(f"{order_id}|{amount:.2f}".encode(), padding.PKCS1v15())).decode()

def wx_verify(payment_b64: str, signature_b64: str):
    pay = base64.b64decode(payment_b64)
    try:
        PUB.verify(base64.b64decode(signature_b64), pay,
                   padding.PSS(mgf=padding.MGF1(hashes.SHA1()), salt_length=20), hashes.SHA1())
    except InvalidSignature:
        return None
    parts = [p.strip() for p in pay.decode().split("|")]
    return dict(zip(FIELDS, parts))
```

## Go
```go
func wxPayment(pub *rsa.PublicKey, orderID string, amount float64) (string, error) {
	ct, err := rsa.EncryptPKCS1v15(rand.Reader, pub, []byte(fmt.Sprintf("%s|%.2f", orderID, amount)))
	return base64.StdEncoding.EncodeToString(ct), err
}
func wxVerify(pub *rsa.PublicKey, paymentB64, sigB64 string) ([]string, bool) {
	pay, e1 := base64.StdEncoding.DecodeString(paymentB64)
	sig, e2 := base64.StdEncoding.DecodeString(sigB64)
	if e1 != nil || e2 != nil { return nil, false }
	h := sha1.Sum(pay)
	if rsa.VerifyPSS(pub, crypto.SHA1, h[:], sig, &rsa.PSSOptions{SaltLength: 20, Hash: crypto.SHA1}) != nil {
		return nil, false
	}
	parts := strings.Split(string(pay), "|")
	for i := range parts { parts[i] = strings.TrimSpace(parts[i]) }
	return parts, true // order_id, ref, datetime, status, comment, gateway, requested, transaction
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
    Signature s = Signature.getInstance("RSASSA-PSS");                       // Java 11+
    s.setParameter(new PSSParameterSpec("SHA-1", "MGF1", MGF1ParameterSpec.SHA1, 20, 1));
    s.initVerify(pub); s.update(pay);
    if (!s.verify(Base64.getDecoder().decode(sigB64))) return null;
    return new String(pay, StandardCharsets.UTF_8).split("\\|");
}
// key: KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der))  (strip PEM header/footer, base64-decode)
```

## Rust (`rsa` 0.9 with `sha1`, `base64` 0.22)
```rust
use base64::{engine::general_purpose::STANDARD as B64, Engine};
use rsa::{pkcs8::DecodePublicKey, pss::{Signature, VerifyingKey},
          signature::Verifier, RsaPublicKey};
use sha1::Sha1;

fn wx_payment(pem: &str, order_id: &str, amount: f64) -> String {
    let key = RsaPublicKey::from_public_key_pem(pem).unwrap();
    let ct = key.encrypt(&mut rand::thread_rng(), rsa::Pkcs1v15Encrypt,
                         format!("{order_id}|{amount:.2}").as_bytes()).unwrap();
    B64.encode(ct)
}
fn wx_verify(pem: &str, payment_b64: &str, sig_b64: &str) -> Option<Vec<String>> {
    let key = RsaPublicKey::from_public_key_pem(pem).ok()?;
    let vk = VerifyingKey::<Sha1>::new(key);          // salt length defaults to the digest size (20)
    let pay = B64.decode(payment_b64).ok()?;
    let sig = Signature::try_from(B64.decode(sig_b64).ok()?.as_slice()).ok()?;
    vk.verify(&pay, &sig).ok()?;
    Some(String::from_utf8(pay).ok()?.split('|').map(|s| s.trim().to_string()).collect())
}
```

## C#
```csharp
static string WxPayment(RSA pub, string orderId, decimal amount) =>
    Convert.ToBase64String(pub.Encrypt(
        Encoding.UTF8.GetBytes($"{orderId}|{amount.ToString("0.00", CultureInfo.InvariantCulture)}"),
        RSAEncryptionPadding.Pkcs1));

static string[]? WxVerify(RSA pub, string paymentB64, string sigB64) {
    var pay = Convert.FromBase64String(paymentB64);
    if (!pub.VerifyData(pay, Convert.FromBase64String(sigB64), HashAlgorithmName.SHA1, RSASignaturePadding.Pss))
        return null;                                   // PSS salt length = hash length (20) by default
    return Encoding.UTF8.GetString(pay).Split('|').Select(s => s.Trim()).ToArray();
}
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
