# Token V2 API (saved cards, CIT/MIT, recurring)

JSON REST API, separate from the redirect form. Base `https://{sandbox-host}/api` / `https://{production-host}/api`; hosts, `bankMID`s and credentials are issued during onboarding (not on the public page).

## Auth
- `POST /api/auth` `{username, password}` → `access_token`, `token_type: "bearer"`, `expires_in` (seconds).
- Send `Authorization: Bearer <token>` on every call.
- `POST /api/refresh` renews with the current or recently expired token (request body undocumented).

## Endpoints
| Purpose | Call | Notes |
|---|---|---|
| Save card | `POST /api/v2/merchant/hc/cards/save` | redirect flow; verification hold is reversed; returns `data.card.id` |
| Save and pay | `POST /api/v2/merchant/hc/cards/saveandpay` | redirect; card saved even if payment declined |
| Pay once | `POST /api/v2/merchant/hc/cards/pay-onetime` | redirect; nothing saved, no cardId |
| Pay, customer present (CIT) | `POST /api/v2/merchant/hc/cards/pay` | synchronous; may need 3DS step-up if authenticated CIT is on |
| Pay, merchant initiated (MIT) | `POST /api/v2/merchant/hc/cards/pay-mit` | synchronous; needs `mitReason` = `recurring | installment | unscheduled`; MIT must be enabled for your merchant; MPGS or CyberSource routing only (Paycorp can't do MIT or authenticated CIT) |
| List cards | `POST /api/v2/merchant/cards/get` | `customer.id`, `customer.email` |
| Delete card | `DELETE /api/v2/merchant/cards/delete` | flat `cardId`, `customerId`, `customerEmail`, optional `bankMID`; irreversible |

## Flow and rules
- Redirect flows return `paymentPageUrl` (or `html3ds_url` for 3DS). Full-page redirect the browser. Bank returns the browser to your `secure3dResponseURL` with `?result3ds=<base64>` (`&result3ds=` if a query string exists). Base64-decode, JSON-parse (standard response envelope).
- `cardId` = first 6 + last 4 digits (e.g. `4000002503`); not secret, but only valid with the same `customer.id` + `customer.email` used at save time.
- `orderNumber` must be unique per merchant (`ORDER_NUMBER_DUPLICATE` otherwise).
- Success: `status: "success"`, `error: false`. Request problem: `status: "failure"`, `error: true`, `code`. Decline: HTTP 402, `code: "CARD_PAYMENT_DECLINED"`, `paymentStatus: "DECLINED"`. Redirect needed: `type` is `url` or `3ds`.
- You must capture and store cardholder consent for MIT; WebXPay doesn't.
- Not documented: request bodies beyond the fields above, server-to-server webhooks, Refund / Pay From Session APIs (listed in the nav but no page), sample code. Get the OpenAPI/Postman from WebXPay.
