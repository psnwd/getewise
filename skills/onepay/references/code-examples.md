# Code: hash, create transaction, verify status (7 languages)

Vector for testing: `app_id=APP123`, `currency=LKR`, `amount=1500.00`, `salt=testsalt` → `763cbcabf99331edfac5d5a5301f08364b85da3ae4e27e5bdab25d99ce819482`.
Hash snippets for Node, Go, Python, PHP, Java and Rust were run against this vector; the C# one was not compiled (no dotnet here). HTTP calls follow the documented shapes but were not run against OnePay (no credentials); check them in sandbox.

Shared flow (server): compute hash → `POST /v3/checkout/link/` (`Authorization: <APP_TOKEN>`) → redirect to `redirect_url` → on callback/return call `POST /v3/transaction/status/` and trust only `status == true` + matching amount/currency.
Config via env: `ONEPAY_APP_ID`, `ONEPAY_APP_TOKEN`, `ONEPAY_SALT`, `ONEPAY_BASE=https://api.onepay.lk`.

## Node / TypeScript (Node 18+)
```ts
import { createHash } from 'node:crypto';
const fmt = (n: number | string) => Number(n).toFixed(2);
export const onepayHash = (appId: string, cur: string, amount: number | string, salt: string) =>
  createHash('sha256').update(`${appId}${cur}${fmt(amount)}${salt}`).digest('hex');

const H = { Authorization: process.env.ONEPAY_APP_TOKEN!, 'Content-Type': 'application/json' };
export async function createCheckout(o: { reference: string; amount: number; currency: string; first: string; last: string; phone: string; email: string; back: string }) {
  const amount = fmt(o.amount);
  const r = await fetch(`${process.env.ONEPAY_BASE}/v3/checkout/link/`, {
    method: 'POST', headers: H,
    body: JSON.stringify({
      app_id: process.env.ONEPAY_APP_ID, amount, currency: o.currency,
      hash: onepayHash(process.env.ONEPAY_APP_ID!, o.currency, amount, process.env.ONEPAY_SALT!),
      reference: o.reference, customer_first_name: o.first, customer_last_name: o.last,
      customer_phone_number: o.phone, customer_email: o.email, transaction_redirect_url: o.back,
    }),
  });
  return r.json(); // read redirect_url + ipg_transaction_id; store the id against your order
}
export async function isPaid(txId: string, expect: { amount: number; currency: string }) {
  const r = await fetch(`${process.env.ONEPAY_BASE}/v3/transaction/status/`, {
    method: 'POST', headers: H, body: JSON.stringify({ app_id: process.env.ONEPAY_APP_ID, onepay_transaction_id: txId }),
  });
  const j: any = await r.json();
  return j.status === true && Number(j.amount) === Number(expect.amount) && j.currency === expect.currency;
}
// Express callback: app.post('/onepay/callback', express.json(), async (req, res) => {
//   res.sendStatus(200);                       // ack fast
//   const { transaction_id } = req.body;       // unsigned: verify through isPaid(), idempotently
// });
```

## Go
```go
func onepayHash(appID, cur, amount, salt string) string {
	sum := sha256.Sum256([]byte(appID + cur + amount + salt))
	return hex.EncodeToString(sum[:])
}
// amount := fmt.Sprintf("%.2f", 1500.0)   // never locale-format

func post(path string, body any) (map[string]any, error) {
	b, _ := json.Marshal(body)
	req, _ := http.NewRequest("POST", os.Getenv("ONEPAY_BASE")+path, bytes.NewReader(b))
	req.Header.Set("Authorization", os.Getenv("ONEPAY_APP_TOKEN"))
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil { return nil, err }
	defer resp.Body.Close()
	var out map[string]any
	return out, json.NewDecoder(resp.Body).Decode(&out)
}
// create: post("/v3/checkout/link/", map[string]any{"app_id": id, "amount": amount, "currency": "LKR", "hash": onepayHash(id,"LKR",amount,salt), ...})
// verify: post("/v3/transaction/status/", map[string]any{"app_id": id, "onepay_transaction_id": txID}) ; check out["status"] == true
```

## Python
```python
import hashlib, os, requests
BASE = os.environ["ONEPAY_BASE"]; HDR = {"Authorization": os.environ["ONEPAY_APP_TOKEN"], "Content-Type": "application/json"}

def onepay_hash(app_id, currency, amount, salt):
    return hashlib.sha256(f"{app_id}{currency}{float(amount):.2f}{salt}".encode()).hexdigest()

def create_checkout(reference, amount, currency, first, last, phone, email, back):
    amt = f"{float(amount):.2f}"; app = os.environ["ONEPAY_APP_ID"]
    r = requests.post(f"{BASE}/v3/checkout/link/", headers=HDR, timeout=30, json={
        "app_id": app, "amount": amt, "currency": currency,
        "hash": onepay_hash(app, currency, amt, os.environ["ONEPAY_SALT"]),
        "reference": reference, "customer_first_name": first, "customer_last_name": last,
        "customer_phone_number": phone, "customer_email": email, "transaction_redirect_url": back})
    return r.json()

def is_paid(tx_id, amount, currency):
    j = requests.post(f"{BASE}/v3/transaction/status/", headers=HDR, timeout=30,
                      json={"app_id": os.environ["ONEPAY_APP_ID"], "onepay_transaction_id": tx_id}).json()
    return j.get("status") is True and float(j["amount"]) == float(amount) and j["currency"] == currency
```

## PHP / Laravel
```php
function onepay_hash(string $appId, string $cur, float $amount, string $salt): string {
    return hash('sha256', $appId . $cur . number_format($amount, 2, '.', '') . $salt);
}
// Laravel
$amt = number_format($amount, 2, '.', '');
$res = Http::withHeaders(['Authorization' => config('services.onepay.token')])
  ->post(config('services.onepay.base').'/v3/checkout/link/', [
    'app_id' => config('services.onepay.app_id'), 'amount' => $amt, 'currency' => 'LKR',
    'hash' => onepay_hash(config('services.onepay.app_id'), 'LKR', (float)$amt, config('services.onepay.salt')),
    'reference' => $order->id, 'customer_first_name' => $u->first, 'customer_last_name' => $u->last,
    'customer_phone_number' => $u->phone, 'customer_email' => $u->email,
    'transaction_redirect_url' => route('onepay.return'),
  ])->json();
// Callback route: exclude from CSRF (VerifyCsrfToken::$except), read $request->json('transaction_id'),
// then call /v3/transaction/status/ and update the order idempotently.
```

## Rust (sha2, reqwest `json`, serde_json)
```rust
use sha2::{Digest, Sha256};
fn onepay_hash(app_id: &str, cur: &str, amount: f64, salt: &str) -> String {
    let s = format!("{app_id}{cur}{amount:.2}{salt}");
    hex::encode(Sha256::digest(s.as_bytes()))
}
async fn post(c: &reqwest::Client, path: &str, body: serde_json::Value) -> anyhow::Result<serde_json::Value> {
    Ok(c.post(format!("{}{}", std::env::var("ONEPAY_BASE")?, path))
        .header("Authorization", std::env::var("ONEPAY_APP_TOKEN")?)
        .json(&body).send().await?.json().await?)
}
```

## Java (11+)
```java
static String onepayHash(String appId, String cur, BigDecimal amount, String salt) throws Exception {
    String s = appId + cur + amount.setScale(2, RoundingMode.HALF_UP).toPlainString() + salt;
    byte[] d = MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
    StringBuilder sb = new StringBuilder(); for (byte b : d) sb.append(String.format("%02x", b));
    return sb.toString();
}
HttpRequest req = HttpRequest.newBuilder(URI.create(base + "/v3/checkout/link/"))
    .header("Authorization", appToken).header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString(json)).build();
```
`BigDecimal.toPlainString()` avoids locale commas; never use `String.format("%.2f")` without `Locale.US`.

## C#
```csharp
static string OnePayHash(string appId, string cur, decimal amount, string salt)
{
    var s = appId + cur + amount.ToString("0.00", CultureInfo.InvariantCulture) + salt;
    return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(s))).ToLowerInvariant();
}
var req = new HttpRequestMessage(HttpMethod.Post, "/v3/checkout/link/") { Content = JsonContent.Create(payload) };
req.Headers.TryAddWithoutValidation("Authorization", appToken);   // raw token, no "Bearer"
using var res = await http.SendAsync(req);
```
