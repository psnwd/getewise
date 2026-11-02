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
All follow the same steps: verify Koko signature > load order by `orderId` > skip if already paid > mark paid, store `trnId` > 200. `markPaid` must be idempotent (Koko may retry). Exempt the route from CSRF/auth middleware.

## Express
```ts
import express from "express";
import { kokoVerify } from "./koko";            // from Node example above

app.post("/koko/response", express.urlencoded({ extended: false }), async (req, res) => {
  const { orderId, trnId, status, signature } = req.body;
  if (!kokoVerify(orderId, trnId, status, signature)) return res.sendStatus(400);
  const order = await db.orders.find(orderId);
  if (!order) return res.sendStatus(404);
  if (status === "SUCCESS" && order.status !== "paid") await db.orders.markPaid(orderId, trnId);
  res.sendStatus(200);
});
```

## Next.js (App Router)
```ts
// app/koko/response/route.ts
import { kokoVerify } from "@/lib/koko";

export async function POST(req: Request) {
  const f = await req.formData();
  const [orderId, trnId, status, sig] = ["orderId", "trnId", "status", "signature"].map((k) => String(f.get(k) ?? ""));
  if (!kokoVerify(orderId, trnId, status, sig)) return new Response(null, { status: 400 });
  const order = await db.orders.find(orderId);
  if (!order) return new Response(null, { status: 404 });
  if (status === "SUCCESS" && order.status !== "paid") await db.orders.markPaid(orderId, trnId);
  return new Response(null, { status: 200 });
}
```

## Laravel
```php
// routes/web.php: Route::post('/koko/response', [KokoController::class, 'response']);
// add 'koko/response' to VerifyCsrfToken::$except
public function response(Request $r) {
    $data = $r->orderId . $r->trnId . $r->status;
    $ok = openssl_verify($data, base64_decode($r->signature), config('services.koko.public_key'), OPENSSL_ALGO_SHA256) === 1;
    if (!$ok) return response('', 400);
    $order = Order::find($r->orderId);
    if (!$order) return response('', 404);
    if ($r->status === 'SUCCESS' && $order->status !== 'paid') $order->update(['status' => 'paid', 'trn_id' => $r->trnId]);
    return response('', 200);
}
```

## FastAPI
```python
from fastapi import FastAPI, Form, HTTPException
app = FastAPI()

@app.post("/koko/response")
def koko_response(orderId: str = Form(...), trnId: str = Form(...), status: str = Form(...), signature: str = Form(...)):
    if not koko_verify(orderId, trnId, status, signature):   # from Python example above
        raise HTTPException(400)
    order = db.get_order(orderId)
    if not order:
        raise HTTPException(404)
    if status == "SUCCESS" and order.status != "paid":
        db.mark_paid(orderId, trnId)
    return {}
```
(Needs `python-multipart` for `Form`.)

## Django
```python
@csrf_exempt
@require_POST
def koko_response(request):
    p = request.POST
    if not koko_verify(p.get("orderId", ""), p.get("trnId", ""), p.get("status", ""), p.get("signature", "")):
        return HttpResponse(status=400)
    order = Order.objects.filter(pk=p["orderId"]).first()
    if not order:
        return HttpResponse(status=404)
    if p["status"] == "SUCCESS" and order.status != "paid":
        order.mark_paid(p["trnId"])
    return HttpResponse(status=200)
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
  return res.ok ? await res.json() : null;      // { orderId, trnId, status, desc, signature }
}

export async function reconcileKoko() {
  const cutoff = new Date(Date.now() - 10 * 60_000);          // callback grace period
  for (const o of await db.orders.pendingBefore("koko", cutoff)) {
    const r = await kokoOrderView(o.id);
    if (!r || r.orderId !== o.id) continue;                    // retry next run
    // ponytail: signed string for the response is assumed orderId+trnId+status (PDF is silent); drop this check if Koko confirms otherwise
    if (!kokoVerify(r.orderId, r.trnId, r.status, r.signature)) continue;
    if (r.status === "SUCCESS") await db.orders.markPaid(o.id, r.trnId);        // idempotent
    else if (r.status === "FAILED") await db.orders.markFailed(o.id);
    // PENDING: leave; give up (expire) after your own max age
  }
}
```
