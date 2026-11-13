# Token V2 API (saved cards, CIT/MIT, recurring)

JSON REST API, separate from the redirect form. Base `https://{sandbox-host}/api` / `https://{production-host}/api`; hosts, `bankMID`s and credentials are issued during onboarding. Known hosts: staging `tokenize.stagingxpay.info` (`/t/api/` commercial, `/cargills/api/`), live `tokenize.webxpay.com` (`/v1/api/`, `/cargills/api/`) and, for the v2.2 line, `commtoken.webxpay.com` ("Setting Live" says to switch to it).

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
| Pay, customer present (CIT) | `POST /api/v2/merchant/hc/cards/pay` | synchronous; may need 3DS step-up if authenticated CIT is on (`authenticationRequired: true` forces a live challenge) |
| Pay, merchant initiated (MIT) | `POST /api/v2/merchant/hc/cards/pay-mit` | synchronous; needs `mitReason` = `recurring | installment | unscheduled`; MIT must be enabled for your merchant; MPGS or CyberSource routing only (Paycorp can't do MIT or authenticated CIT) |
| List cards | `POST /api/v2/merchant/cards/get` | `customer.id`, `customer.email` |
| Delete card | `DELETE /api/v2/merchant/cards/delete` | flat `cardId`, `customerId`, `customerEmail`, optional `bankMID`; irreversible |
| CUP save / session pay | `POST /cards/paycorp/save`, `POST /cards/pay/paycorp` | v1 paths, no hosted session needed |

## Older (v1) token endpoints
The official PHP sample still ships the v1 API: `POST auth`, `POST cards/save3ds`, `GET cards/other/{currency}`, `POST cards` (list), `POST cards/pay/`, `POST cards/pay/token3ds`, `POST cards/pay/session3ds`, `GET merchant/user`, `DELETE cards`. "Pay From Session" is `cards/pay/session3ds`; v2 replaced it with `pay-onetime` + `paymentPageUrl`. v1 auth returns `{"token": ...}`, v2 returns `{"access_token","token_type":"bearer","expires_in":3600}`. Save-card v1 also takes `session` plus the address block.

## Flow and rules
- Redirect flows return `paymentPageUrl` (or `html3ds_url` for 3DS). Full-page redirect the browser. Bank returns the browser to your `secure3dResponseURL` with `?result3ds=<base64>` (`&result3ds=` if a query string exists). Base64-decode, JSON-parse (standard response envelope).
- `cardId` = first 6 + last 4 digits (e.g. `4000002503`); not secret, but only valid with the same `customer.id` + `customer.email` used at save time.
- `orderNumber` must be unique per merchant (`ORDER_NUMBER_DUPLICATE` otherwise).
- Success: `status: "success"`, `error: false`. Card-save responses also carry `refundStatus: true` — a capability flag, not an endpoint. Request problem: `status: "failure"`, `error: true`, `code`. Decline: HTTP 402, `code: "CARD_PAYMENT_DECLINED"`, `paymentStatus: "DECLINED"`. Redirect needed: `type` is `url` or `3ds`.
- Error codes are stable enough to branch on: `UNAUTHORIZED` (401), `VALIDATION_ERROR` (422), `INVALID_MID` (422), `CURRENCY_VALIDATION_FAILED` (422), `MERCHANT_NOT_FOUND` (404), `ORDER_NUMBER_DUPLICATE` (409), `CARD_NOT_FOUND` (404), `CARD_EXPIRED` (422), `CARD_PAYMENT_DECLINED` (402), `CARD_MULTIPLE_MATCHES` (409), `CARD_DELETE_FAILED` (422), `CIT_AUTHENTICATION_UNSUPPORTED_GATEWAY` (422), `CARD_3DS_INITIATE_FAILED` (422), `CARD_3DS_AUTHENTICATION_FAILED` (422), `CARD_3DS_UNSUPPORTED_TOKEN` (422), `MIT_NOT_ENABLED` (403), `MIT_UNSUPPORTED_GATEWAY` (422), `MIT_NO_REFERENCE_TRANSACTION` (422).
- You must capture and store cardholder consent for MIT; WebXPay doesn't.
- Not documented: request bodies beyond the fields above, server-to-server webhooks, a refund endpoint, sample code. Get the OpenAPI/Postman from WebXPay.
