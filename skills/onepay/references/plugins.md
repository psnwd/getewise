# Plugins

All need App ID, App Token, Hash Salt from the merchant portal.

- **WordPress / WooCommerce**: needs WooCommerce. Install "Onepay Payment Gateway" from the plugin directory, activate, paste App ID/App Token/Hash Salt. Redirect defaults to the WooCommerce thank-you page. No version matrix or callback setup documented.
- **Shopify**: app `apps.shopify.com/onepay-payment-new`. Add app, connect merchant account, activate under Settings > Payments, enable app embeds if needed, test in Test Mode, then switch to Live. Migrating from the old app: deactivate old method, uninstall, clean theme code for "onepay", remove leftover scripts/pixels, duplicate theme first, export settlement reports first.
- **WHMCS**: get files from the OnePay WHMCS GitHub repo or your Relationship Officer. Copy the `onepay` folder and `onepay.php` into `modules/gateways`, and the callback `onepay.php` into `gateways/callback`. Configure App ID/App Token/Hash Salt in WHMCS admin.
- **Zoho Books / Inventory**: install the OnePay extension from Zoho Marketplace, enter API keys from the Merchant Admin Console (IPG Apps), enable on invoices. Invoice updates automatically after payment.
Troubleshooting from docs: payments failing usually means mistyped credentials; checkout broken after Shopify migration means leftover old-app code. Docs don't list supported platform versions.
