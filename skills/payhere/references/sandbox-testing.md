# Sandbox & Testing

- Sandbox is a **separate clone** of the live platform. Nothing is actually processed: payments are simulated. Sandbox accounts, merchant IDs, secrets and settings **cannot be converted** to a live account; apply for live separately after testing.
- Sandbox hosts: checkout `https://sandbox.payhere.lk/pay/checkout`, preapprove `.../pay/preapprove`, authorize `.../pay/authorize`, REST `https://sandbox.payhere.lk/merchant/v1/...`.
- Plugins: tick "Enable Sandbox Mode" in the plugin settings. JS/mobile SDKs: `"sandbox": true` (Android: `PHConfigs.setBaseUrl(PHConfigs.SANDBOX_URL)`).
- Use the **sandbox** merchant ID and a secret for a sandbox-registered domain; live credentials won't work there and vice versa.

## Test cards (published by PayHere)
Any name, any valid CVV and expiry. Any card **not** listed fails.

| Scenario | Visa | MasterCard | AMEX |
|---|---|---|---|
| Success | 4916217501611292 | 5307732125531191 | 346781005510225 |
| Insufficient funds | 4024007194349121 | 5459051433777487 | 370787711978928 |
| Limit exceeded | 4929119799365646 | 5491182243178283 | 340701811823469 |
| Do not honor | 4929768900837248 | 5388172137367973 | 374664175202812 |
| Network error | 4024007120869333 | 5237980565185003 | 373433500205887 |

## Sandbox-specific behaviour
- Recurring: next installment fires ~1 minute after authorization, so you can test `AUTHORIZATION_SUCCESS` then `RECURRING_INSTALLMENT_SUCCESS`.
- Recurring options `recurring_start_date`, `auto_cancel`, `max_retries`, `is_recovery_due` are live-only.
- Charging API `type: AUTHORIZE` is live-only.
- REST API "Access denied for the domain": set the API key's allowed domain to `*` in sandbox.
- notify_url cannot be localhost; use a public tunnel.
