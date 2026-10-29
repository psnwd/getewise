# Environments, account, plugins, support

## Environments
| | Production | Sandbox (UAT) |
|---|---|---|
| API base | `https://api.geniebiz.lk` | `https://api.uat.geniebiz.lk` |
| Hosted page | `transaction.geniebiz.lk` (assumed from UAT form) | `https://transaction.uat.geniebiz.lk/<id>` |
| Keys | Merchant dashboard (https://dashboard.geniebiz.lk/) > Connect | issued on request: email genie.integration@dialog.lk |
| Money | real | none; transactions don't appear in your merchant account |

- Sandbox credentials are separate: API key, and for plugins a client ID. A key from one environment fails on the other.
- **Test payment provider on production**: Genie says you can enable a test provider on your production credentials. Transactions then use the live account but aren't paid out and show in the dashboard (`isTest` on the object). Handy for end-to-end tests of live webhooks, but keep them out of your real reports.
- A Test API Keys text file is linked from geniebusiness.lk/developer (`Dialog Pay Business - Test API Keys 2.txt`). It wasn't fetchable for this skill, so we have no sample test card numbers. Ask the user to read them from that file. Never put real keys in code or this skill.

## Payment methods
Cards (Visa, Mastercard, Amex), Genie wallet, eZ Cash, UPI, Alipay, JustPay; local and foreign currency; payment links with expiry. Which are active depends on the merchant account. Tokenisation: cards only.

## Plugins and integrations
| Platform | Notes |
|---|---|
| WooCommerce ("Genie Business Payment Gateway" on wordpress.org, slug `genie-business-payment-gateway`; code `geniebiz-woocommerce` v1.0.3 in the version we saw) | needs PHP 7.0+, WordPress 4.8+, WooCommerce 3.5.5+, cURL, JSON and bcrypt PHP modules. Settings: client ID and client secret, sandbox or production mode, payment expiry, payment link sync, secure logger |
| OpenCart | extension listed on the OpenCart marketplace (id 44044) |
| Custom | the Connect API in the other references |

The plugin asks for a client ID and secret, while the API docs describe a single API key. Don't assume they map one to one; use the credentials the dashboard or support gave for each.

## Account and docs
- Developer hub: https://www.geniebusiness.lk/developer (links to the guideline PDF, Stoplight docs, test keys).
- API docs: https://geniebusiness.stoplight.io/docs/genie-business-connect (Change Logs, Card-On-File Payments, Webhooks, Transaction States, Merchant-Initiated-Transactions, then Connect API with groups Categories, Company, Custom Fees, Order Fields, Products, Shops, Taxes, Transactions, Webhooks, Customers, Tokenization, FX, Schemas).
- The "Open API Guideline" PDF is a navigation guide to the Stoplight docs, not a spec.
- Support: genie.integration@dialog.lk (integration and sandbox keys), dialogpaymerchantsupport@dialogfinance.lk (merchant support).
- Fees, MDR, settlement timing, limits, onboarding documents and chargeback rules aren't in the public developer docs. Say so and send the user to Genie support or their account manager; don't quote numbers.

## Change log highlights (from the docs)
2023-10 customer and tokenization in Create Transaction; 2023-12 card-on-file; 2024-01 customer-initiated flag; 2024-02 field limits and examples; 2024-04 `customers.externalId`, `preferredSubscriptionPlan`; 2024-05 multiple MCC and plans; 2024-06 refund API; 2024-07 static QR in Get Company; 2024-11 Charge Stored Token fields for a new 3DS provider; 2025-06 FX API.
