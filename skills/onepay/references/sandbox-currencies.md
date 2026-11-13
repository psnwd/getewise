# Sandbox, test cards, currencies, methods

## Test cards (docs.onepay.lk/testing/test-cards)
| Type | Number | Exp | CVV |
|---|---|---|---|
| Visa | 4508750015741019 | 01/39 | 100 |
| Visa | 4012000033330026 | 01/39 | 100 |
| Mastercard | 5123450000000008 | 01/39 | 100 |
| Mastercard | 5111111111111118 | 01/39 | 100 |
The page doesn't say which cards approve or decline. Card on File page lists separate tokenization cards (Visa 4564456445644564 / MC 5430489999999992, CVV 582, 12/26). No sandbox App ID, App Token or Hash Salt is published — every official example shows a masked 20-char id and a placeholder `hashToken`.

## Sandbox vs live
Same host and version prefix: `https://api.onepay.lk`. **There is no separate sandbox base URL** — the docs' "Base URLs" block lists only Live. Sandbox is an **app-level mode**: each business account has separate live and sandbox credentials (App ID, App Token, Hash Salt), and the app moves `On Development → Pending Approval → Live` via "Request to Go Live" (up to 3 working days; after requesting you can't modify the app without OnePay admin permission). `sandbox.*` / `uat.*` / `api-sandbox.*` hosts are NXDOMAIN.

Refunds don't work on sandbox transactions ("both `status = true` (paid) and `is_live = true`"). 3DS is mandatory for every transaction — "OnePay does not support 2D (non-authenticated) transactions under any circumstances", OTP comes from the issuing bank inside the hosted flow. Test fully, then swap in live credentials.

## Payment methods
Visa, Mastercard, Amex, Diners, Discover, UnionPay; Google Pay, Frimi, QPlus, HelaPay.

## Currencies
LKR, USD, GBP, EUR, AUD, JPY, INR, CHF, CAD, SGD (10). Which are enabled depends on the merchant account: ask the Relationship Officer ("currency not available for the app" is a 400). Settlement is always in LKR at the FX rate at transaction time. CBSL rules bar Sri Lankan businesses from taking USD from domestic customers. (The Items page says LKR/USD only for item prices.) Transaction min/max amounts are not stated; plan fees and volume caps are in `refund-payouts.md`.
