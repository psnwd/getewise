# Code: OAuth token + Charging API call (7 languages)

Pattern is identical everywhere (see `merchant-api.md`):
1. `POST {host}/merchant/v1/oauth/token`, header `Authorization: Basic base64(APP_ID:APP_SECRET)`, form body `grant_type=client_credentials`. Token lasts ~599 s.
2. `POST {host}/merchant/v1/payment/charge`, header `Authorization: Bearer <token>`, JSON body.
Hosts: sandbox `https://sandbox.payhere.lk`, live `https://www.payhere.lk`. Rate limit 20 req / 10 s. Live calls come only from whitelisted domain + server IP.

Cache the token and refresh ~30 s before expiry (or on an `invalid_token` response). Config via env: `PAYHERE_HOST`, `PAYHERE_APP_ID`, `PAYHERE_APP_SECRET`.

These snippets were written to the documented request shapes. They were not run against PayHere (no merchant credentials), so verify against the sandbox.

## curl (quick check)
```bash
TOKEN=$(curl -s -X POST https://sandbox.payhere.lk/merchant/v1/oauth/token \
  -u "$PAYHERE_APP_ID:$PAYHERE_APP_SECRET" -d grant_type=client_credentials | jq -r .access_token)

curl -s -X POST https://sandbox.payhere.lk/merchant/v1/payment/charge \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"PAYMENT","order_id":"Order12345","items":"Taxi Hire","currency":"LKR","amount":345.67,"customer_token":"<token>"}'
```

## Node / TypeScript (fetch, Node 18+)
```ts
let cache: { token: string; exp: number } | null = null;
async function getToken(): Promise<string> {
  if (cache && Date.now() < cache.exp) return cache.token;
  const basic = Buffer.from(`${process.env.PAYHERE_APP_ID}:${process.env.PAYHERE_APP_SECRET}`).toString('base64');
  const r = await fetch(`${process.env.PAYHERE_HOST}/merchant/v1/oauth/token`, {
    method: 'POST',
    headers: { Authorization: `Basic ${basic}`, 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'grant_type=client_credentials',
  });
  const j = await r.json();
  if (!j.access_token) throw new Error(`token error: ${JSON.stringify(j)}`);
  cache = { token: j.access_token, exp: Date.now() + (j.expires_in - 30) * 1000 };
  return cache.token;
}
export async function charge(body: object) {
  const r = await fetch(`${process.env.PAYHERE_HOST}/merchant/v1/payment/charge`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${await getToken()}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return r.json();   // { status, msg, data } ; data.status_code 2 = success
}
```

## Go
```go
func token(host, id, secret string) (string, error) {
	req, _ := http.NewRequest("POST", host+"/merchant/v1/oauth/token", strings.NewReader("grant_type=client_credentials"))
	req.SetBasicAuth(id, secret)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	resp, err := http.DefaultClient.Do(req)
	if err != nil { return "", err }
	defer resp.Body.Close()
	var out struct{ AccessToken string `json:"access_token"`; ExpiresIn int `json:"expires_in"` }
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil || out.AccessToken == "" { return "", fmt.Errorf("token error") }
	return out.AccessToken, nil
}

func charge(host, tok string, payload map[string]any) (map[string]any, error) {
	b, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", host+"/merchant/v1/payment/charge", bytes.NewReader(b))
	req.Header.Set("Authorization", "Bearer "+tok)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil { return nil, err }
	defer resp.Body.Close()
	var out map[string]any
	return out, json.NewDecoder(resp.Body).Decode(&out)
}
```
(`SetBasicAuth` does the base64 for you.)

## Python (requests)
```python
import os, time, requests
HOST = os.environ["PAYHERE_HOST"]; _cache = {"tok": None, "exp": 0}

def get_token() -> str:
    if _cache["tok"] and time.time() < _cache["exp"]:
        return _cache["tok"]
    r = requests.post(f"{HOST}/merchant/v1/oauth/token",
                      auth=(os.environ["PAYHERE_APP_ID"], os.environ["PAYHERE_APP_SECRET"]),
                      data={"grant_type": "client_credentials"}, timeout=15)
    j = r.json()
    _cache.update(tok=j["access_token"], exp=time.time() + j["expires_in"] - 30)
    return _cache["tok"]

def charge(payload: dict) -> dict:
    r = requests.post(f"{HOST}/merchant/v1/payment/charge",
                      headers={"Authorization": f"Bearer {get_token()}"}, json=payload, timeout=30)
    return r.json()
```

## PHP / Laravel
```php
use Illuminate\Support\Facades\Http;

function ph_token(): string {
    return cache()->remember('payhere_token', 540, fn () =>
        Http::withBasicAuth(config('services.payhere.app_id'), config('services.payhere.app_secret'))
            ->asForm()->post(config('services.payhere.host').'/merchant/v1/oauth/token', ['grant_type' => 'client_credentials'])
            ->throw()->json('access_token'));
}
function ph_charge(array $payload): array {
    return Http::withToken(ph_token())->post(config('services.payhere.host').'/merchant/v1/payment/charge', $payload)->json();
}
```

## Rust (reqwest + serde_json, features `json`)
```rust
async fn token(c: &reqwest::Client, host: &str, id: &str, secret: &str) -> anyhow::Result<String> {
    let v: serde_json::Value = c.post(format!("{host}/merchant/v1/oauth/token"))
        .basic_auth(id, Some(secret)).form(&[("grant_type", "client_credentials")])
        .send().await?.json().await?;
    Ok(v["access_token"].as_str().ok_or_else(|| anyhow::anyhow!("token error: {v}"))?.to_string())
}
async fn charge(c: &reqwest::Client, host: &str, tok: &str, body: &serde_json::Value) -> anyhow::Result<serde_json::Value> {
    Ok(c.post(format!("{host}/merchant/v1/payment/charge")).bearer_auth(tok).json(body).send().await?.json().await?)
}
```

## Java (java.net.http, 11+)
```java
HttpClient http = HttpClient.newHttpClient();
String basic = Base64.getEncoder().encodeToString((appId + ":" + appSecret).getBytes(StandardCharsets.UTF_8));
HttpRequest tokReq = HttpRequest.newBuilder(URI.create(host + "/merchant/v1/oauth/token"))
    .header("Authorization", "Basic " + basic)
    .header("Content-Type", "application/x-www-form-urlencoded")
    .POST(HttpRequest.BodyPublishers.ofString("grant_type=client_credentials")).build();
String tokJson = http.send(tokReq, HttpResponse.BodyHandlers.ofString()).body();   // parse access_token with Jackson/Gson

HttpRequest chargeReq = HttpRequest.newBuilder(URI.create(host + "/merchant/v1/payment/charge"))
    .header("Authorization", "Bearer " + accessToken)
    .header("Content-Type", "application/json")
    .POST(HttpRequest.BodyPublishers.ofString(chargeJson)).build();
String result = http.send(chargeReq, HttpResponse.BodyHandlers.ofString()).body();
```

## C# (HttpClient)
```csharp
var http = new HttpClient { BaseAddress = new Uri(host) };

async Task<string> GetTokenAsync()
{
    var basic = Convert.ToBase64String(Encoding.UTF8.GetBytes($"{appId}:{appSecret}"));
    var req = new HttpRequestMessage(HttpMethod.Post, "/merchant/v1/oauth/token")
    { Content = new FormUrlEncodedContent(new[] { new KeyValuePair<string, string>("grant_type", "client_credentials") }) };
    req.Headers.Authorization = new AuthenticationHeaderValue("Basic", basic);
    using var res = await http.SendAsync(req);
    return JsonDocument.Parse(await res.Content.ReadAsStringAsync()).RootElement.GetProperty("access_token").GetString()!;
}

async Task<string> ChargeAsync(string token, object payload)
{
    var req = new HttpRequestMessage(HttpMethod.Post, "/merchant/v1/payment/charge")
    { Content = JsonContent.Create(payload) };
    req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    using var res = await http.SendAsync(req);
    return await res.Content.ReadAsStringAsync();
}
```

## Same pattern for the other endpoints
Swap path/method/body: Retrieval `GET /merchant/v1/payment/search?order_id=`, Subscription `GET /merchant/v1/subscription[/{id}[/payments]]`, retry/cancel `POST /merchant/v1/subscription/{retry|cancel}`, refund `POST /merchant/v1/payment/refund`, capture `POST /merchant/v1/payment/capture`.
