# Koko code examples

Env vars: `KOKO_MID`, `KOKO_API_KEY`, `KOKO_PRIVATE_KEY_PEM` (merchant), `KOKO_PUBLIC_KEY_PEM` (Koko's), `KOKO_HOST` (e.g. `https://qaapi.paykoko.com`). All examples sign with RSA-SHA256 PKCS#1 v1.5 and base64.

## PHP
```php
<?php
function koko_order(array $o): string {           // $o: order from DB
  $f = [
    '_mId' => getenv('KOKO_MID'), '_amount' => number_format($o['amount'], 2, '.', ''),
    '_currency' => 'LKR', '_pluginName' => 'customapi', '_pluginVersion' => '1.0.1',
    '_returnUrl' => $o['return'], '_cancelUrl' => $o['cancel'], '_orderId' => (string)$o['id'],
    '_reference' => (string)$o['id'], '_firstName' => $o['first'], '_lastName' => $o['last'],
    '_email' => $o['email'], '_description' => $o['desc'], 'api_key' => getenv('KOKO_API_KEY'),
    '_responseUrl' => $o['response'],
  ];
  $data = implode('', $f);                          // order above == dataString order
  openssl_sign($data, $sig, getenv('KOKO_PRIVATE_KEY_PEM'), OPENSSL_ALGO_SHA256);
  $f += ['dataString' => $data, 'signature' => base64_encode($sig)];
  $h = '';
  foreach ($f as $k => $v) $h .= '<input type="hidden" name="'.$k.'" value="'.htmlspecialchars($v).'">';
  return '<form id="k" method="POST" action="'.getenv('KOKO_HOST').'/api/merchants/orderCreate">'.$h
       . '</form><script>document.getElementById("k").submit()</script>';
}

// _responseUrl handler
$d = $_POST['orderId'].$_POST['trnId'].$_POST['status'];
$ok = openssl_verify($d, base64_decode($_POST['signature']), getenv('KOKO_PUBLIC_KEY_PEM'), OPENSSL_ALGO_SHA256) === 1;
```

## Node / TypeScript
```ts
import { createSign, createVerify } from "node:crypto";

export function kokoFields(o: Record<string, string>) {
  const f = {
    _mId: process.env.KOKO_MID!, _amount: o.amount, _currency: "LKR",
    _pluginName: "customapi", _pluginVersion: "1.0.1", _returnUrl: o.returnUrl,
    _cancelUrl: o.cancelUrl, _orderId: o.id, _reference: o.id, _firstName: o.first,
    _lastName: o.last, _email: o.email, _description: o.desc,
    api_key: process.env.KOKO_API_KEY!, _responseUrl: o.responseUrl,
  };
  const dataString = Object.values(f).join("");     // insertion order == dataString order
  const signature = createSign("RSA-SHA256").update(dataString).sign(process.env.KOKO_PRIVATE_KEY_PEM!, "base64");
  return { ...f, dataString, signature };           // render as hidden form -> `${KOKO_HOST}/api/merchants/orderCreate`
}

export const kokoVerify = (orderId: string, trnId: string, status: string, sig: string) =>
  createVerify("RSA-SHA256").update(orderId + trnId + status).verify(process.env.KOKO_PUBLIC_KEY_PEM!, sig, "base64");
```

## Python
```python
import base64, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEYS = ["_mId","_amount","_currency","_pluginName","_pluginVersion","_returnUrl","_cancelUrl",
        "_orderId","_reference","_firstName","_lastName","_email","_description","api_key","_responseUrl"]

def koko_fields(f: dict) -> dict:                   # f has all KEYS
    data = "".join(f[k] for k in KEYS)
    pk = serialization.load_pem_private_key(os.environ["KOKO_PRIVATE_KEY_PEM"].encode(), None)
    sig = base64.b64encode(pk.sign(data.encode(), padding.PKCS1v15(), hashes.SHA256())).decode()
    return {**f, "dataString": data, "signature": sig}

def koko_verify(order_id, trn_id, status, sig) -> bool:   # raises-free
    pub = serialization.load_pem_public_key(os.environ["KOKO_PUBLIC_KEY_PEM"].encode())
    try:
        pub.verify(base64.b64decode(sig), (order_id + trn_id + status).encode(), padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False
```

## Go
```go
func kokoSign(priv *rsa.PrivateKey, data string) (string, error) {
	h := sha256.Sum256([]byte(data))
	s, err := rsa.SignPKCS1v15(rand.Reader, priv, crypto.SHA256, h[:])
	return base64.StdEncoding.EncodeToString(s), err
}

func kokoVerify(pub *rsa.PublicKey, orderID, trnID, status, sigB64 string) bool {
	sig, err := base64.StdEncoding.DecodeString(sigB64)
	if err != nil { return false }
	h := sha256.Sum256([]byte(orderID + trnID + status))
	return rsa.VerifyPKCS1v15(pub, crypto.SHA256, h[:], sig) == nil
}
// dataString = strings.Join of the 15 fields in checkout-api.md order, separator "".
```

## orderView (any language)
`dataString = _mId + _pluginName + _pluginVersion + _orderId + api_key`, sign the same way, POST fields `_mId, api_key, _orderId, _pluginName, _pluginVersion, signature` form-encoded to `{host}/api/merchants/orderView`.

# `_responseUrl` handlers by framework
All follow the same steps: verify Koko signature > load order by `orderId` > skip if already paid > mark paid, store `trnId` > **200**. `markPaid` must be idempotent (Koko may retry). Exempt the route from CSRF/auth middleware.

Koko sends the callback as JSON **or** form-encoded. Parse both. On any failure — missing/invalid signature, unknown order, exception — log it and still answer `200`: a non-200 makes Koko retry.

## Express
```ts
import express from "express";
import { kokoVerify } from "./koko";            // from Node example above

app.post("/koko/response", express.json(), express.urlencoded({ extended: false }), async (req, res) => {
  try {
    const { orderId, trnId, status, signature } = req.body ?? {};
    if (kokoVerify(String(orderId ?? ""), String(trnId ?? ""), String(status ?? ""), String(signature ?? ""))) {
      const order = await db.orders.find(orderId);
      if (order && status === "SUCCESS" && order.status !== "paid") await db.orders.markPaid(orderId, trnId);
    }
  } catch (e) {
    console.error("koko callback", e);
  }
  res.sendStatus(200);                            // always 200
});
```

## Next.js (App Router)
```ts
// app/koko/response/route.ts
import { kokoVerify } from "@/lib/koko";

export async function POST(req: Request) {
  try {
    const ct = req.headers.get("content-type") ?? "";
    const f: Record<string, unknown> = ct.includes("application/json")
      ? await req.json().catch(() => ({}))
      : Object.fromEntries((await req.formData()).entries());
    const [orderId, trnId, status, sig] = ["orderId", "trnId", "status", "signature"].map((k) => String(f[k] ?? ""));
    if (kokoVerify(orderId, trnId, status, sig)) {
      const order = await db.orders.find(orderId);
      if (order && status === "SUCCESS" && order.status !== "paid") await db.orders.markPaid(orderId, trnId);
    }
  } catch (e) {
    console.error("koko callback", e);
  }
  return new Response("OK", { status: 200 });     // always 200
}
```

## Laravel
```php
// routes/web.php: Route::post('/koko/response', [KokoController::class, 'response']);
// add 'koko/response' to VerifyCsrfToken::$except
public function response(Request $r) {
    $in = $r->isJson() ? $r->json() : $r->all();
    $data = ($in['orderId'] ?? '') . ($in['trnId'] ?? '') . ($in['status'] ?? '');
    $ok = openssl_verify($data, base64_decode($in['signature'] ?? ''), config('services.koko.public_key'), OPENSSL_ALGO_SHA256) === 1;
    if ($ok) {
        $order = Order::find($in['orderId'] ?? null);
        if ($order && $in['status'] === 'SUCCESS' && $order->status !== 'paid') $order->update(['status' => 'paid', 'trn_id' => $in['trnId']]);
    }
    return response('OK', 200);                   // always 200
}
```

## FastAPI
```python
from fastapi import FastAPI, Request
app = FastAPI()

@app.post("/koko/response")
async def koko_response(request: Request):
    try:
        ct = request.headers.get("content-type", "")
        body = await request.json() if "application/json" in ct else dict(await request.form())
    except Exception:
        body = {}
    try:
        p = {k: str(body.get(k, "")) for k in ("orderId", "trnId", "status", "signature")}
        if koko_verify(p["orderId"], p["trnId"], p["status"], p["signature"]):   # from Python example above
            order = db.get_order(p["orderId"])
            if order and p["status"] == "SUCCESS" and order.status != "paid":
                db.mark_paid(p["orderId"], p["trnId"])
    except Exception as e:
        print("koko callback", e)
    return {}                                      # always 200
```
(Needs `python-multipart` for `request.form()`.)

## Django
```python
@csrf_exempt
@require_POST
def koko_response(request):
    try:
        body = json.loads(request.body) if request.content_type == "application/json" else request.POST
        p = {k: str(body.get(k, "")) for k in ("orderId", "trnId", "status", "signature")}
        if koko_verify(p["orderId"], p["trnId"], p["status"], p["signature"]):
            order = Order.objects.filter(pk=p["orderId"]).first()
            if order and p["status"] == "SUCCESS" and order.status != "paid":
                order.mark_paid(p["trnId"])
    except Exception:
        logger.exception("koko callback")
    return HttpResponse("OK", status=200)          # always 200
```

# Reconciliation job (missing `_responseUrl` callbacks)
Run every few minutes. Looks up orders still pending after a grace period, asks Koko via `orderView`, and applies the result through the same idempotent path as the callback. See `order-view-api.md` for the fields.

```ts
import { createSign } from "node:crypto";
import { kokoVerify } from "./koko";            // from Node example above

async function kokoOrderView(orderId: string) {
  const f = { _mId: process.env.KOKO_MID!, api_key: process.env.KOKO_API_KEY!, _orderId: orderId,
              _pluginName: "customapi", _pluginVersion: "1.0.1" };
  const dataString = f._mId + f._pluginName + f._pluginVersion + f._orderId + f.api_key;   // fixed order, no separators
  const signature = createSign("RSA-SHA256").update(dataString).sign(process.env.KOKO_PRIVATE_KEY_PEM!, "base64");
  const res = await fetch(`${process.env.KOKO_HOST}/api/merchants/orderView`, {
    method: "POST", body: new URLSearchParams({ ...f, signature }),   // form-encoded
  });
  return res.ok ? await res.json() : null;      // { content: { orderId, trnId, status, desc, signature }, status, statusCode }
}

export async function reconcileKoko() {
  const cutoff = new Date(Date.now() - 10 * 60_000);          // callback grace period
  for (const o of await db.orders.pendingBefore("koko", cutoff)) {
    const r = await kokoOrderView(o.id);
    const c = r?.content;
    if (!c || c.orderId !== o.id) continue;                    // retry next run
    // Koko's own plugin never verifies the response signature; signed string is unknown.
    // If you verify, it is assumed orderId+trnId+status — drop the check if Koko confirms otherwise.
    if (!kokoVerify(c.orderId, c.trnId, c.status, c.signature)) continue;
    if (c.status === "SUCCESS") await db.orders.markPaid(o.id, c.trnId);        // idempotent
    else if (c.status === "FAILED") await db.orders.markFailed(o.id);
    // PENDING: leave; give up (expire) after your own max age
  }
}
```
