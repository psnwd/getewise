# Code examples

Each language shows the same three things: (1) create a transaction, (2) verify the webhook signature, (3) fetch the transaction and decide. Secrets come from env vars: `GENIE_API_KEY`, `GENIE_BASE` (`https://api.uat.geniebiz.lk` for sandbox, `https://api.geniebiz.lk` for production). Amounts are integer minor units. The signature function was checked against one shared vector in Node, Python, PHP, Go, Java and Rust (see the end); the C# version was not compiled.

Shared flow for a store:
1. Create your order in the DB with amount in minor units; use its ID as `localId`.
2. `POST /public/v2/transactions`; save `id`; redirect to `url`.
3. Webhook (or return page): verify signature, call Get Transaction, require `state == "CONFIRMED"`, compare amount, currency and `localId`, update the order once.

## Contents
Node/TypeScript, Go, Python, PHP/Laravel, Rust, Java, C#

## Node / TypeScript (Express, Node 18+)
```ts
import crypto from "node:crypto";
import express from "express";

const BASE = process.env.GENIE_BASE!;
const KEY = process.env.GENIE_API_KEY!;
const headers = { Authorization: KEY, "Content-Type": "application/json" };

export async function createTransaction(orderId: string, minorAmount: number) {
  const r = await fetch(`${BASE}/public/v2/transactions`, {
    method: "POST", headers,
    body: JSON.stringify({
      amount: minorAmount, currency: "LKR", localId: orderId,
      redirectUrl: "https://shop.example/pay/return",
      webhook: "https://shop.example/webhooks/genie",
    }),
  });
  if (!r.ok) throw new Error(`genie create ${r.status}`);
  return r.json() as Promise<{ id: string; url: string }>;     // redirect customer to url
}

export function validSignature(nonce: string, ts: string, sig: string) {
  const expected = crypto.createHash("sha256").update(nonce + ts + KEY).digest("hex");
  const a = Buffer.from(expected), b = Buffer.from(sig ?? "");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}

const app = express();
app.use(express.json());
app.post("/webhooks/genie", async (req, res) => {
  const h = req.headers;
  if (!validSignature(String(h["x-signature-nonce"]), String(h["x-signature-timestamp"]), String(h["x-signature"])))
    return res.sendStatus(401);
  const tx = await (await fetch(`${BASE}/public/transactions/${req.body.transactionId}`, { headers })).json();
  // look up order by tx.localId; require tx.state === "CONFIRMED", tx.amount === order.minor, tx.currency === "LKR"
  // update idempotently (key: tx.id)
  res.sendStatus(200);
});
```

## Go (net/http)
```go
package genie

import (
	"bytes"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
)

var base, key = os.Getenv("GENIE_BASE"), os.Getenv("GENIE_API_KEY")

func Sign(nonce, ts, apiKey string) string {
	h := sha256.Sum256([]byte(nonce + ts + apiKey))
	return hex.EncodeToString(h[:])
}

func Valid(nonce, ts, sig string) bool {
	return subtle.ConstantTimeCompare([]byte(Sign(nonce, ts, key)), []byte(sig)) == 1
}

type Tx struct {
	ID       string `json:"id"`
	URL      string `json:"url"`
	State    string `json:"state"`
	Amount   int64  `json:"amount"`
	Currency string `json:"currency"`
	LocalID  string `json:"localId"`
}

func call(method, path string, body any) (*Tx, error) {
	var buf bytes.Buffer
	if body != nil {
		json.NewEncoder(&buf).Encode(body)
	}
	req, _ := http.NewRequest(method, base+path, &buf)
	req.Header.Set("Authorization", key)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 300 {
		return nil, fmt.Errorf("genie %s: %d", path, resp.StatusCode)
	}
	var t Tx
	return &t, json.NewDecoder(resp.Body).Decode(&t)
}

func Create(orderID string, minor int64) (*Tx, error) {
	return call("POST", "/public/v2/transactions", map[string]any{
		"amount": minor, "currency": "LKR", "localId": orderID,
		"redirectUrl": "https://shop.example/pay/return",
		"webhook":     "https://shop.example/webhooks/genie",
	})
}

func Webhook(w http.ResponseWriter, r *http.Request) {
	if !Valid(r.Header.Get("X-Signature-Nonce"), r.Header.Get("X-Signature-Timestamp"), r.Header.Get("X-Signature")) {
		http.Error(w, "bad signature", http.StatusUnauthorized)
		return
	}
	var ev struct{ TransactionID string `json:"transactionId"` }
	json.NewDecoder(r.Body).Decode(&ev)
	tx, err := call("GET", "/public/transactions/"+ev.TransactionID, nil)
	if err == nil && tx.State == "CONFIRMED" {
		// load order by tx.LocalID, compare tx.Amount and tx.Currency, mark paid once
	}
	w.WriteHeader(http.StatusOK)
}
```

## Python (FastAPI + httpx)
```python
import hashlib, hmac, os
import httpx
from fastapi import FastAPI, Header, HTTPException, Request

BASE, KEY = os.environ["GENIE_BASE"], os.environ["GENIE_API_KEY"]
H = {"Authorization": KEY, "Content-Type": "application/json"}
app = FastAPI()

def create_transaction(order_id: str, minor: int) -> dict:
    r = httpx.post(f"{BASE}/public/v2/transactions", headers=H, json={
        "amount": minor, "currency": "LKR", "localId": order_id,
        "redirectUrl": "https://shop.example/pay/return",
        "webhook": "https://shop.example/webhooks/genie"})
    r.raise_for_status()
    return r.json()                      # redirect to ["url"]

def valid(nonce: str, ts: str, sig: str) -> bool:
    expected = hashlib.sha256((nonce + ts + KEY).encode()).hexdigest()
    return hmac.compare_digest(expected, sig or "")

@app.post("/webhooks/genie")
async def hook(req: Request, x_signature_nonce: str = Header(""), x_signature_timestamp: str = Header(""),
               x_signature: str = Header("")):
    if not valid(x_signature_nonce, x_signature_timestamp, x_signature):
        raise HTTPException(401)
    ev = await req.json()
    tx = httpx.get(f"{BASE}/public/transactions/{ev['transactionId']}", headers=H).json()
    if tx["state"] == "CONFIRMED":
        pass  # load order by tx["localId"], compare tx["amount"], tx["currency"], mark paid once
    return {"ok": True}
```

## PHP / Laravel
```php
// config/services.php: 'genie' => ['base' => env('GENIE_BASE'), 'key' => env('GENIE_API_KEY')]
use Illuminate\Support\Facades\Http;

function genieCreate(string $orderId, int $minor): array {
    $c = config('services.genie');
    return Http::withHeaders(['Authorization' => $c['key']])
        ->post($c['base'].'/public/v2/transactions', [
            'amount' => $minor, 'currency' => 'LKR', 'localId' => $orderId,
            'redirectUrl' => url('/pay/return'), 'webhook' => url('/webhooks/genie'),
        ])->throw()->json();                       // redirect()->away($tx['url'])
}

// routes/web.php: Route::post('/webhooks/genie', GenieWebhook::class);
// app/Http/Middleware/VerifyCsrfToken.php: $except = ['webhooks/genie'];
class GenieWebhook {
    public function __invoke(\Illuminate\Http\Request $r) {
        $c = config('services.genie');
        $expected = hash('sha256', $r->header('X-Signature-Nonce').$r->header('X-Signature-Timestamp').$c['key']);
        if (!hash_equals($expected, (string) $r->header('X-Signature'))) abort(401);
        $tx = Http::withHeaders(['Authorization' => $c['key']])
            ->get($c['base'].'/public/transactions/'.$r->input('transactionId'))->throw()->json();
        if ($tx['state'] === 'CONFIRMED') {
            // find order by $tx['localId'], compare $tx['amount'] and $tx['currency'], mark paid once
        }
        return response('OK');
    }
}
```

## Rust (axum, reqwest, sha2, hex, subtle)
```rust
use axum::{http::{HeaderMap, StatusCode}, Json};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use subtle::ConstantTimeEq;

fn sign(nonce: &str, ts: &str, key: &str) -> String {
    hex::encode(Sha256::digest(format!("{nonce}{ts}{key}").as_bytes()))
}

fn valid(h: &HeaderMap, key: &str) -> bool {
    let g = |n: &str| h.get(n).and_then(|v| v.to_str().ok()).unwrap_or("");
    let expected = sign(g("x-signature-nonce"), g("x-signature-timestamp"), key);
    expected.as_bytes().ct_eq(g("x-signature").as_bytes()).into()
}

async fn create(base: &str, key: &str, order_id: &str, minor: i64) -> reqwest::Result<Value> {
    reqwest::Client::new()
        .post(format!("{base}/public/v2/transactions"))
        .header("Authorization", key)
        .json(&json!({"amount": minor, "currency": "LKR", "localId": order_id,
                      "redirectUrl": "https://shop.example/pay/return",
                      "webhook": "https://shop.example/webhooks/genie"}))
        .send().await?.error_for_status()?.json().await   // redirect to ["url"]
}

async fn webhook(h: HeaderMap, Json(ev): Json<Value>) -> StatusCode {
    let (base, key) = (std::env::var("GENIE_BASE").unwrap(), std::env::var("GENIE_API_KEY").unwrap());
    if !valid(&h, &key) { return StatusCode::UNAUTHORIZED; }
    let id = ev["transactionId"].as_str().unwrap_or_default();
    if let Ok(r) = reqwest::Client::new().get(format!("{base}/public/transactions/{id}"))
        .header("Authorization", &key).send().await {
        if let Ok(tx) = r.json::<Value>().await {
            if tx["state"] == "CONFIRMED" { /* match localId, amount, currency; mark paid once */ }
        }
    }
    StatusCode::OK
}
```

## Java (11+, Jackson)
```java
import java.net.URI;
import java.net.http.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;

public class Genie {
    static final String BASE = System.getenv("GENIE_BASE"), KEY = System.getenv("GENIE_API_KEY");
    static final HttpClient HTTP = HttpClient.newHttpClient();

    static String sign(String nonce, String ts, String key) throws Exception {
        byte[] d = MessageDigest.getInstance("SHA-256").digest((nonce + ts + key).getBytes(StandardCharsets.UTF_8));
        return HexFormat.of().formatHex(d);
    }

    static boolean valid(String nonce, String ts, String sig) throws Exception {
        return MessageDigest.isEqual(sign(nonce, ts, KEY).getBytes(StandardCharsets.UTF_8),
                (sig == null ? "" : sig).getBytes(StandardCharsets.UTF_8));
    }

    static String create(String orderId, long minor) throws Exception {
        String body = String.format("{\"amount\":%d,\"currency\":\"LKR\",\"localId\":\"%s\","
            + "\"redirectUrl\":\"https://shop.example/pay/return\","
            + "\"webhook\":\"https://shop.example/webhooks/genie\"}", minor, orderId);
        HttpRequest req = HttpRequest.newBuilder(URI.create(BASE + "/public/v2/transactions"))
            .header("Authorization", KEY).header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(body)).build();
        return HTTP.send(req, HttpResponse.BodyHandlers.ofString()).body();   // parse "url" and "id"
    }

    static String get(String txId) throws Exception {
        HttpRequest req = HttpRequest.newBuilder(URI.create(BASE + "/public/transactions/" + txId))
            .header("Authorization", KEY).GET().build();
        return HTTP.send(req, HttpResponse.BodyHandlers.ofString()).body();    // require state == CONFIRMED
    }
}
```
In Spring: `@PostMapping("/webhooks/genie")` reading `@RequestHeader("X-Signature-Nonce")` etc., call `valid(...)`, then `get(txId)`. Build the JSON with Jackson, not `String.format`, if `orderId` can contain quotes.

## C# (ASP.NET Core minimal API)
```csharp
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text;

var baseUrl = Environment.GetEnvironmentVariable("GENIE_BASE")!;
var key = Environment.GetEnvironmentVariable("GENIE_API_KEY")!;
var http = new HttpClient { BaseAddress = new Uri(baseUrl) };
http.DefaultRequestHeaders.TryAddWithoutValidation("Authorization", key);

static string Sign(string nonce, string ts, string key) =>
    Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(nonce + ts + key))).ToLowerInvariant();

var app = WebApplication.CreateBuilder(args).Build();

app.MapPost("/webhooks/genie", async (HttpRequest r, System.Text.Json.JsonElement ev) =>
{
    var expected = Encoding.UTF8.GetBytes(Sign(r.Headers["X-Signature-Nonce"].ToString(),
                                               r.Headers["X-Signature-Timestamp"].ToString(), key));
    var got = Encoding.UTF8.GetBytes(r.Headers["X-Signature"].ToString());
    if (!CryptographicOperations.FixedTimeEquals(expected, got)) return Results.Unauthorized();

    var id = ev.GetProperty("transactionId").GetString();
    var tx = await http.GetFromJsonAsync<System.Text.Json.JsonElement>($"/public/transactions/{id}");
    if (tx.GetProperty("state").GetString() == "CONFIRMED")
    {
        // load order by tx.localId, compare amount and currency, mark paid once
    }
    return Results.Ok();
});

// create: var res = await http.PostAsJsonAsync("/public/v2/transactions",
//   new { amount = minor, currency = "LKR", localId = orderId, redirectUrl = "...", webhook = "..." });
// var tx = await res.Content.ReadFromJsonAsync<JsonElement>();  redirect to tx.GetProperty("url")
app.Run();
```
`FixedTimeEquals` needs equal-length spans; a different-length header returns false rather than throwing.

## Checked
Signature vector used in checks: nonce `n1`, timestamp `1700000000`, key `testkey` gives `95c7088ce897c937b06fa06b6c08048563b18cb8104e8d449eeb0d89f20af8d6` (`scripts/genie_webhook.py` and CI check it). The HTTP calls follow the Stoplight docs; they were not run against a live Genie account.
