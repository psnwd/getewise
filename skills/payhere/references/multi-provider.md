# Multiple gateways in one app

Applies when one app accepts payments through several Gatewise providers (PayHere, OnePay, WebXPay, Genie, Koko). Each gateway signs and calls back differently; keep that difference at the edge and the rest of the app uniform.

## Layout
- **Env:** one prefixed block per provider (see "Env files" in `SKILL.md`). Never share a var between providers.
- **Routes:** one callback route per provider, e.g. `/pay/payhere/notify`, `/pay/koko/response`. Each verifies its own signature, then calls the shared `settle()` below. Exempt every one from CSRF/auth middleware.
- **Adapter per provider**, same shape, so checkout and reconciliation do not branch on provider:

```ts
interface Gateway {
  id: "payhere" | "onepay" | "webxpay" | "genie" | "koko";
  startCheckout(order: Order): Promise<{ url?: string; fields?: Record<string, string> }>;   // redirect URL or signed form
  verifyCallback(req: Request): Promise<{ orderId: string; ref: string; paid: boolean } | null>;  // null = bad signature
  lookup(order: Order): Promise<{ ref: string; paid: boolean } | null>;                      // status API, for reconciliation
}
```

## One idempotent settle
```ts
async function settle(provider: string, orderId: string, ref: string) {
  // unique (provider, ref) makes retries and duplicate callbacks no-ops
  const first = await db.payments.insertIfAbsent({ provider, ref, orderId });
  if (first) await db.orders.markPaid(orderId, { provider, ref });   // amount/currency checked against the order first
}
```

## Rules
1. **Order owns the provider.** Store `provider` on the order at checkout; a callback for a different provider than the order's is rejected.
2. **Key references by `(provider, ref)`.** Transaction ids are unique per gateway, not across them.
3. **Check amount and currency** from your DB against the callback, per provider; never trust the redirect.
4. **Reconcile per provider** with its status API (`Gateway.lookup`) for orders stuck pending; each gateway's file in its own skill has the call.
5. **Per-provider sandbox switch** (its own host var), so one provider can go live while others stay on sandbox.
