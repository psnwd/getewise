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
- The `Dialog Pay Business - Test API Keys 2.txt` file linked from geniebusiness.lk/developer now **404s** (four filename variants tried), so we have no sample test card numbers. UAT keys still come by email from genie.integration@dialog.lk (confirmed on the developer page FAQ). Never put real keys in code or this skill.

## Payment methods
Cards (Visa, Mastercard, UnionPay, Amex), Genie wallet, eZ Cash, UPI, Alipay, JustPay; local and foreign currency; payment links with expiry. Which are active depends on the merchant account. Tokenisation: cards only.

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
- Fees and settlement are on the pricing page (geniebusiness.lk/pricing), not in the developer docs — see the table below. Limits and minimum amount are still not published; send the user to support or the account manager for those.

### Fees, settlement and plans
| Item | Value |
|---|---|
| MDR, Visa / Mastercard / UnionPay | 2.75% (IPG, E-Store, Payment Links) |
| MDR, American Express | 3.00% |
| LQR | 0% up to LKR 5,000, 1.00% above |
| Int QR | 1.85% (Starter/Pro 1.80%) |
| Monthly plan | Rs 400 / 500 / 750 / 1,000 |
| Setup | IPG Rs 4,500; E-Store / Payment Link Rs 2,500; DCC Rs 4,900; MiniPOS Rs 5,000–8,500; Standard POS Rs 15,000 |
| Settlement | next day for sole proprietors/individuals (including holidays); T+2 for LLC/partnership |
| Settlement account | must be a Dialog Finance savings account; **LKR 5** fee to settle to another bank |
| MCP | refund USD 50; chargeback USD 50 + the full transaction amount |

Account setup is quoted at "within 3 working days".

## Change log highlights (from the docs)
2023-10 customer and tokenization in Create Transaction; 2023-12 card-on-file; 2024-01 customer-initiated flag; 2024-02 field limits and examples; 2024-04 `customers.externalId`, `preferredSubscriptionPlan`; 2024-05 multiple MCC and plans; 2024-06 refund API; 2024-07 static QR in Get Company; 2024-11 Charge Stored Token fields for a new 3DS provider; 2025-06 FX API.
