# Payment Links and Items

Both are token-auth APIs (`Authorization: <APP_TOKEN>`, `Content-Type: application/json`), no hash.

## Payment Link: `/v3/payment-link/`
- Create: `POST /v3/payment-link/?app_id=...` (body fields are not documented on the page; the overview mentions `expiration_date` and `allow_partial_payment`). Link is active immediately until expiry. Partial payment applies to amounts over LKR 100,000 or USD 100, minimum 30-100% of total.
- Get: `GET /v3/payment-link/{link_id}/?app_id=...` (`link_id` is 8 chars e.g. `8IT20WK7`). Returns `data.is_complete`, `is_delete`, `link_url`, `amount`, `expiration_date`, `created_at`, `updated_at`. Poll `is_complete` for fulfilment.
- Update: `PUT /v3/payment-link/{link_id}/` body `app_id`, `description`. Only `description` can change.
- Delete: `DELETE /v3/payment-link/{link_id}/?app_id=...`. Soft delete; blocked (400 "Cannot delete a link with successful transactions.") if paid.
- Doc conflict: page says `app_id` is a query param, not in the body, yet the Update table lists it in the body. Send it where each endpoint's table says, and test.

## Items: `/v3/item/`
- Create `POST /v3/item/`: `name`, `description`, `price`, `currency` (LKR or USD per this page; the currencies page lists 10) required; `image_url`, `metadata` (object) optional. Returns `data.item_id`.
- List `GET /v3/item/?app_id=...`
- Update `PUT /v3/item/{item_id}/`: `app_id` in body, any of `name, price, description, image_url, metadata` (metadata array replaces all existing).
- Delete `DELETE /v3/item/{item_id}/?app_id=...` (not allowed for items on completed transactions).
- Attach to a payment with the `items` array on create transaction (custom API integrations only).
- Inconsistencies: `metadata` is an object on create but array of `{key,value}` on get/update; `price` number on write, string on read; `app_id` placement varies.
