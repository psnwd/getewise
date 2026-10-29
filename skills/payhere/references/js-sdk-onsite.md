# JavaScript SDK (payhere.js) & Onsite Checkout

Onsite Checkout = payment popup (card entry inside a PayHere iframe) on your own page, no redirect. Needs HTTPS on your site. Card data stays in PayHere's PCI DSS iframe. Same backend notify/md5sig flow as Checkout API (see `checkout-api.md`).

Plugins that support onsite: WooCommerce, OpenCart (toggle in plugin settings). Custom code: use payhere.js. Mobile apps: use native SDKs (`mobile-sdks.md`).

## Include
```html
<script src="https://www.payhere.lk/lib/payhere-2.0.js"></script>
```

## Flow
1. Your **backend** creates order, computes `hash` (see `checkout-api.md` / `scripts/`), returns payment object + hash to the page. Never compute the hash in the browser.
2. Front end builds the `payment` object, calls `payhere.startPayment(payment)`.
3. PayHere POSTs result to `notify_url` (backend verifies md5sig).
4. Front end events tell the UI what happened, but are **not proof of payment**; confirm via your backend/DB.

## payment object
Same fields as Checkout API: `merchant_id, notify_url, order_id, items, amount ("1000.00"), currency, hash, first_name, last_name, email, phone, address, city, country`, optional delivery_*, `custom_1/2`, `item_name_N` etc.
Extras for the SDK:
- `"sandbox": true` for sandbox merchant
- `return_url: undefined`, `cancel_url: undefined`: **leave undefined** so the popup doesn't redirect (docs mark these "Important")
- Preapproval: `"preapprove": true`
- Recurring: `recurrence`, `duration` (same format as Recurring API)
- Hold on card: `"authorize": true` (used by mobile SDKs; web SDK page lists preapprove/recurrence only)

## Events
```js
payhere.onCompleted = (orderId) => { /* checkout finished; may be success OR failure: verify server-side */ };
payhere.onDismissed = () => { /* user closed popup before processing */ };
payhere.onError = (error) => { /* invalid params */ };
document.getElementById('pay').onclick = () => payhere.startPayment(payment);
```

## Gotchas
- `onCompleted` fires even for failed payments. Poll/fetch your order status from your backend.
- Domain must be registered in Integrations with its own secret (per-domain secret).
- Hash amount string must match `payment.amount` exactly (e.g. `"1000.00"`).
- Same errors as Checkout API (Unauthorized payment request, PH-0022, etc.).
