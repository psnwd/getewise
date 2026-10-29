# Sandbox, test cards, currencies, methods

## Test cards (docs.onepay.lk/testing/test-cards)
| Type | Number | Exp | CVV |
|---|---|---|---|
| Visa | 4508750015741019 | 01/39 | 100 |
| Visa | 4012000033330026 | 01/39 | 100 |
| Mastercard | 5123450000000008 | 01/39 | 100 |
| Mastercard | 5111111111111118 | 01/39 | 100 |
The page doesn't say which cards approve or decline. Card on File page lists separate tokenization cards (Visa 4564456445644564 / MC 5430489999999992, CVV 582, 12/26).

## Sandbox vs live
Separate credential sets per business account, both from the merchant dashboard. No sandbox base URL is published; use the sandbox App ID/Token against the same API and confirm with OnePay. Refunds don't work on sandbox transactions. Test fully, then swap in live credentials.

## Payment methods
Visa, Mastercard, Amex, Diners, Discover, UnionPay; Google Pay, Frimi, QPlus, HelaPay.

## Currencies
LKR, USD, GBP, EUR, AUD, JPY, INR, CHF, CAD, SGD (10). Which are enabled depends on the merchant account: ask the Relationship Officer ("currency not available for the app" is a 400). Settlement is always in LKR at the FX rate at transaction time. CBSL rules bar Sri Lankan businesses from taking USD from domestic customers. (The Items page says LKR/USD only for item prices.) Limits and fees are not stated in the docs.
