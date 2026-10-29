# Recurring API & Preapproval API

Both use the same hash/notify/md5sig pattern as `checkout-api.md`. Read that first for hash and verification logic. Only differences are listed here.

## Recurring API (subscriptions PayHere charges for you)

POST to the **same** action URL as Checkout:
- Live `https://www.payhere.lk/pay/checkout`, Sandbox `https://sandbox.payhere.lk/pay/checkout`

Extra required params on top of Checkout's: 
- `recurrence`: number + singular word: `1 Month`, `2 Week`, `6 Month`, `1 Year`
- `duration`: `Forever` or number+word compatible with recurrence (`1 Year`, `3 Year`)
- `amount` (e.g. `1000.00`), `hash`

Extra optional params:
- `startup_fee`: extra fee or discount on first payment
- `auto_cancel` (true/false, default true): stop subscription after max retries exhausted
- `max_retries`: retry attempts for a failed installment (one per day)
- `recurring_start_date` (YYYY-MM-DD): delayed start / free trial
- `is_recovery_due` (true/false, default true): recover missed installments in later cycles

**Live only**: `recurring_start_date`, `auto_cancel`, `max_retries`, `is_recovery_due` are NOT supported in sandbox.

### Hash with a future `recurring_start_date`
Hash is computed with an **overridden amount**: `10.00` for LKR, `0.50` for other currencies. The submitted `amount` field still holds the real subscription amount. Only the amount fed into the hash changes.

### Notification extras
In addition to checkout notification fields: `subscription_id`, `recurring` (1/0), `message_type`, `item_recurrence`, `item_duration`, `item_rec_status` (0 active, -1 cancelled, 1 completed), `item_rec_date_next` (YYYY-MM-DD), `item_rec_install_paid`. `method` is VISA/MASTER only.

`message_type` values (branch on this, not on arrival time):
- `AUTHORIZATION_SUCCESS` / `AUTHORIZATION_FAILED`: initial card authorization
- `RECURRING_INSTALLMENT_SUCCESS` / `RECURRING_INSTALLMENT_FAILED`: scheduled charge
- `RECURRING_COMPLETE`: all installments done
- `RECURRING_STOPPED`: stopped/cancelled early

### Default live behaviour
- Success: notify with `RECURRING_INSTALLMENT_SUCCESS`, status 2.
- Failure: retried once/day for up to 7 days; each failure notifies `RECURRING_INSTALLMENT_FAILED` (status -2); subscription stays active meanwhile. A successful retry doesn't shift the original schedule.
- Missed earlier installments are recovered with the current cycle, one attempt per day each (unless `is_recovery_due=false`).
- All retries fail: `RECURRING_STOPPED`, status -2, `item_rec_status=-1`; no more attempts.

### Sandbox testing
After the first authorization, PayHere fires the next installment about **1 minute** later so you can test both notifications. Live uses the real recurrence.

Manage subscriptions (list/retry/cancel) via the Subscription Manager API in `merchant-api.md`.

## Preapproval API (tokenize card for later on-demand charging)

Action URLs: Live `https://www.payhere.lk/pay/preapprove`, Sandbox `https://sandbox.payhere.lk/pay/preapprove`.

Required: same as Checkout minus `amount`: `merchant_id, return_url, cancel_url, notify_url, first_name, last_name, email, phone, address, city, country, order_id, items, currency, hash`.
Optional: `amount` (charge as part of preapproval), `platform`, `custom_1`, `custom_2`.

### Hash rule
- If you send `amount`: hash with that amount.
- If you do not: use **`10.00` for LKR, `0.51` for any other currency** in the hash.
- Mismatch here is a common cause of "Unauthorized payment request".

### Notification
Fields as checkout plus `customer_token` (encrypted card token), `card_holder_name`, `card_no`, `card_expiry`. Status codes: 2, 0, -1, -2.
Verify md5sig the same way, then store `customer_token` securely against the customer. Use it with the Charging API (`merchant-api.md`).

The docs' PHP sample checks `status_code == 2` for success on preapproval. Preapproval needs the Premium plan and works for Visa/Mastercard only (see `account-business.md`). PH-0022 applies here as well: live URL must keep `www` (`https://www.payhere.lk/pay/preapprove`).
