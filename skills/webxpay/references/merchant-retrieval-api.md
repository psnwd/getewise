# Merchant login and Transaction Retrieval (redirect-integration merchants)

Form-data POSTs on `https://webxpay.com/index.php?route=api/merchant_api/...`. All calls are form-data, not JSON. Fields and paths below come from the downloadable Postman collections on the docs page (the response field list is in a screenshot, `Images/response.png`).

## Login (get a bearer token)
| Call | Fields | Returns |
|---|---|---|
| `route=api/merchant_api/loginRequest` | `email`, `password` | auth token |
| `route=api/merchant_api/apiLogin` | `api_username`, `api_password`, `merchant_number` | auth token |

Send the token on retrieval calls as `Authorization: Bearer <token>`. Expiry is not documented. The page text that says the second retrieval call "returns an auth token" is a copy-paste error.

## Transaction retrieval (needs the token)
| Purpose | Call | Fields |
|---|---|---|
| By WebXPay order reference | `route=api/merchant_api/getTransactionData` | `order_refference_number` — note the double `f`; example `T580332021I07` |
| By your own reference | `route=api/merchant_api/getTransactionByMerchantReference` | `merchant_reference`; example `166606175214` |

## Response fields
`order_id`, `order_reference_number`, `payment_status_id` (`2`), `payment_status` (`Approved`), `date_added`, `processing_currency_id` (`5`), `total_amount` (`5.50`), `gateway_order_id` (`wxp_264475`), `date_time_transaction`, `merchant_payout_status_id` (`1`), `date_time_settlement`, `first_name`, `last_name`, `address_line_one`, `address_line_two`, `city`, `contact_number`, `order_status` (`Processing`).

There is **no card mask, no gateway id and no signature** in this response. The numeric `*_id` columns (`payment_status_id`, `processing_currency_id`, `merchant_payout_status_id`) have no published legend — only the observed values above.

Use this to confirm payment status server-side after a return-URL hit. That matters more here than usual: the redirect flow has no server-to-server callback.
