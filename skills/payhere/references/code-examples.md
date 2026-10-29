# Code: request hash + notify verification (7 languages)

Everything here implements two formulas (see `checkout-api.md`):

```
hash   = UPPER(md5(merchant_id + order_id + amount_2dp + currency + UPPER(md5(secret))))
md5sig = UPPER(md5(merchant_id + order_id + payhere_amount + payhere_currency + status_code + UPPER(md5(secret))))
```
Test vector (secret `testsecret`, merchant `1211149`, order `ItemNo12345`, `1000` LKR, status `2`):
`hash = 157365BBAF81B09B3FEC1749C1ED915D`, `md5sig = 5A638B69DFE6FA6427CCE00B06B3EE2B`.
Node, Go, PHP, Java, Rust, Python snippets were run against this vector; C# was written to the same pattern but not compiled here.

## Contents
- Node / TypeScript
- Go
- Python
- PHP / Laravel
- Rust
- Java
- C#
- Which framework detail matters

Money rules: format request amount with exactly 2 decimals (`1000.00`), invariant culture, no thousands separators. Use notification fields **as received** for verification. After verifying the signature, also check `status_code == 2` (or `3` for authorize), and that amount/currency/order_id match your own order.

---
## Node / TypeScript
```ts
import { createHash, timingSafeEqual } from 'node:crypto';

const md5Upper = (s: string) => createHash('md5').update(s, 'utf8').digest('hex').toUpperCase();
export const fmtAmount = (a: number | string) => Number(a).toFixed(2);

export function checkoutHash(p: { merchantId: string; orderId: string; amount: number | string; currency: string; secret: string }) {
  return md5Upper(p.merchantId + p.orderId + fmtAmount(p.amount) + p.currency + md5Upper(p.secret));
}

export function verifyNotification(body: Record<string, string>, secret: string): boolean {
  const local = md5Upper(
    body.merchant_id + body.order_id + body.payhere_amount +
    body.payhere_currency + body.status_code + md5Upper(secret));
  const a = Buffer.from(local), b = Buffer.from(String(body.md5sig ?? '').toUpperCase());
  return a.length === b.length && timingSafeEqual(a, b);
}
```
Express notify route (form-encoded, not JSON):
```ts
app.post('/payhere/notify', express.urlencoded({ extended: false }), async (req, res) => {
  const b = req.body;
  if (!verifyNotification(b, process.env.PAYHERE_SECRET!)) return res.sendStatus(400);
  const order = await db.orders.find(b.order_id);
  if (order && b.status_code === '2' && Number(b.payhere_amount) === order.total && b.payhere_currency === order.currency) {
    await db.orders.markPaid(order.id, b.payment_id);   // make this idempotent
  }
  res.sendStatus(200);
});
```
Next.js route handler: `const form = await request.formData()` then `Object.fromEntries(form)`.
Browser/React: **never** call `checkoutHash` client-side; fetch the hash from your API.

## Go
```go
func md5Upper(s string) string { sum := md5.Sum([]byte(s)); return strings.ToUpper(hex.EncodeToString(sum[:])) }

func CheckoutHash(merchantID, orderID string, amount float64, currency, secret string) string {
	return md5Upper(merchantID + orderID + fmt.Sprintf("%.2f", amount) + currency + md5Upper(secret))
}

func VerifyNotification(r *http.Request, secret string) bool {
	if err := r.ParseForm(); err != nil { return false }
	f := r.PostForm // form body only
	local := md5Upper(f.Get("merchant_id") + f.Get("order_id") + f.Get("payhere_amount") +
		f.Get("payhere_currency") + f.Get("status_code") + md5Upper(secret))
	return subtle.ConstantTimeCompare([]byte(local), []byte(strings.ToUpper(f.Get("md5sig")))) == 1
}
```
Imports: `crypto/md5`, `crypto/subtle`, `encoding/hex`, `fmt`, `net/http`, `strings`. Handler: `http.HandleFunc("/payhere/notify", ...)`, verify, then act, `w.WriteHeader(200)`. For money prefer integer cents or `decimal` over `float64` in real code, and format as `%d.%02d`.
Gin: `c.PostForm("merchant_id")` etc. (build the same string); Fiber: `c.FormValue`.

## Python
```python
import hashlib, hmac
from decimal import Decimal, ROUND_HALF_UP

def md5_upper(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest().upper()

def fmt_amount(a) -> str:
    return str(Decimal(str(a)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def checkout_hash(merchant_id, order_id, amount, currency, secret) -> str:
    return md5_upper(f"{merchant_id}{order_id}{fmt_amount(amount)}{currency}{md5_upper(secret)}")

def verify_notification(f: dict, secret: str) -> bool:
    local = md5_upper(f["merchant_id"] + f["order_id"] + f["payhere_amount"] +
                      f["payhere_currency"] + f["status_code"] + md5_upper(secret))
    return hmac.compare_digest(local, f.get("md5sig", "").upper())
```
FastAPI: `async def notify(request: Request): form = dict(await request.form())` (needs `python-multipart`). Django: `request.POST` and `@csrf_exempt`. Flask: `request.form`.
CLI version: `scripts/payhere_sign.py`.

## PHP / Laravel
```php
function ph_hash(string $merchantId, string $orderId, $amount, string $currency, string $secret): string {
    return strtoupper(md5($merchantId . $orderId . number_format((float)$amount, 2, '.', '') . $currency . strtoupper(md5($secret))));
}
function ph_verify(array $p, string $secret): bool {
    $local = strtoupper(md5(($p['merchant_id'] ?? '') . ($p['order_id'] ?? '') . ($p['payhere_amount'] ?? '')
        . ($p['payhere_currency'] ?? '') . ($p['status_code'] ?? '') . strtoupper(md5($secret))));
    return hash_equals($local, strtoupper($p['md5sig'] ?? ''));
}
```
Laravel: route in `routes/web.php`, **exempt it from CSRF** (`bootstrap/app.php`: `$middleware->validateCsrfTokens(except: ['payhere/notify']);` or `$except` in `VerifyCsrfToken` on older versions):
```php
Route::post('/payhere/notify', function (Request $r) {
    if (! ph_verify($r->post(), config('services.payhere.secret'))) abort(400);
    if ($r->input('status_code') == 2) { /* mark order paid (idempotent) */ }
    return response('OK');
});
```
Community package: `lahirulhr/laravel-payhere` covers Checkout, Recurring, Preapproval, Charging, Retrieval, Subscription, Refund, Authorize, Capture; `api_endpoint` config = `https://www.payhere.lk` (live) or `https://sandbox.payhere.lk`. Third-party, not official: check maintenance before recommending.

## Rust
`Cargo.toml`: `md5 = "0.7"`, `subtle = "2"`.
```rust
use std::collections::HashMap;
use subtle::ConstantTimeEq;

fn md5_upper(s: &str) -> String { format!("{:X}", md5::compute(s.as_bytes())) }

pub fn checkout_hash(merchant_id: &str, order_id: &str, amount: f64, currency: &str, secret: &str) -> String {
    md5_upper(&format!("{merchant_id}{order_id}{amount:.2}{currency}{}", md5_upper(secret)))
}

pub fn verify_notification(form: &HashMap<String, String>, secret: &str) -> bool {
    let g = |k: &str| form.get(k).map(String::as_str).unwrap_or("");
    let local = md5_upper(&format!("{}{}{}{}{}{}", g("merchant_id"), g("order_id"), g("payhere_amount"),
        g("payhere_currency"), g("status_code"), md5_upper(secret)));
    local.as_bytes().ct_eq(g("md5sig").to_uppercase().as_bytes()).into()
}
```
Axum: `async fn notify(State(app): State<App>, Form(f): Form<HashMap<String, String>>) -> StatusCode` (Form extractor handles urlencoded). Actix: `web::Form<HashMap<String,String>>`. Use `rust_decimal` for real money handling.

## Java
```java
static String md5Upper(String s) {
    try {
        byte[] d = MessageDigest.getInstance("MD5").digest(s.getBytes(StandardCharsets.UTF_8));
        return String.format("%032X", new BigInteger(1, d));
    } catch (Exception e) { throw new IllegalStateException(e); }
}
public static String checkoutHash(String merchantId, String orderId, BigDecimal amount, String currency, String secret) {
    String amt = amount.setScale(2, RoundingMode.HALF_UP).toPlainString();   // never locale-dependent
    return md5Upper(merchantId + orderId + amt + currency + md5Upper(secret));
}
public static boolean verifyNotification(Map<String, String> p, String secret) {
    String local = md5Upper(p.get("merchant_id") + p.get("order_id") + p.get("payhere_amount")
            + p.get("payhere_currency") + p.get("status_code") + md5Upper(secret));
    return MessageDigest.isEqual(local.getBytes(StandardCharsets.UTF_8),
            p.getOrDefault("md5sig", "").toUpperCase().getBytes(StandardCharsets.UTF_8));
}
```
Spring Boot:
```java
@PostMapping(value = "/payhere/notify", consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE)
public ResponseEntity<Void> notify(@RequestParam Map<String, String> p) {
    if (!PayHereSign.verifyNotification(p, secret)) return ResponseEntity.badRequest().build();
    // check status_code, amount, order; idempotent update
    return ResponseEntity.ok().build();
}
```
Permit this path in Spring Security / disable CSRF for it. The docs' own Java sample uses `double` + `DecimalFormat("0.00")`: works but is locale-sensitive; prefer `BigDecimal`.

## C# (.NET 6+)
```csharp
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

static string Md5Upper(string s) => Convert.ToHexString(MD5.HashData(Encoding.UTF8.GetBytes(s))); // already uppercase

public static string CheckoutHash(string merchantId, string orderId, decimal amount, string currency, string secret) =>
    Md5Upper(merchantId + orderId + amount.ToString("0.00", CultureInfo.InvariantCulture) + currency + Md5Upper(secret));

public static bool VerifyNotification(IFormCollection f, string secret)
{
    string local = Md5Upper(f["merchant_id"] + f["order_id"] + f["payhere_amount"] +
        f["payhere_currency"] + f["status_code"] + Md5Upper(secret));
    return CryptographicOperations.FixedTimeEquals(
        Encoding.UTF8.GetBytes(local), Encoding.UTF8.GetBytes(f["md5sig"].ToString().ToUpperInvariant()));
}
```
Minimal API: `app.MapPost("/payhere/notify", async (HttpRequest req) => { var f = await req.ReadFormAsync(); ... Results.Ok(); }).DisableAntiforgery();` (.NET 8 needs antiforgery disabled for external POSTs). MVC: `[IgnoreAntiforgeryToken]`.
The docs' own C# sample builds hex with `$"{b:X2}"`, equivalent. `decimal` + `InvariantCulture` avoids comma decimals.

---
## Which framework detail matters
- Parse **form-encoded** bodies on notify (not JSON).
- Exempt the notify route from CSRF/antiforgery and from auth middleware.
- Return 2xx quickly; do slow work asynchronously.
- Never expose the secret or hash computation to the client.
