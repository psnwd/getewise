# Shopping-cart plugins (no-code / low-code)

All plugins need: **Merchant ID** and **Merchant Secret** from PayHere dashboard > Integrations (older docs call it Settings > Domains & Credentials or Account > Business "Secret Key"). Each has a **Sandbox mode** toggle for testing against a sandbox account. Don't set a Return URL in the PayHere dashboard for plugins that handle it themselves (WooCommerce, OpenCart). WooCommerce and OpenCart support Onsite Checkout (popup) via a plugin setting.

| Platform | Install | Where to configure |
|---|---|---|
| **WooCommerce** | Download from the WordPress plugin store/PayHere, upload `woocommerce-payhere` to `/wp-content/plugins`, activate "WooCommerce PayHere Payment Gateway" | WooCommerce > Settings > Checkout > PayHere: enable, title/description, Merchant ID, Secret Key (same as in PayHere dashboard), Sandbox checkbox. In PayHere: Account > Business > Edit: set Secret Key, leave Return URL empty |
| **OpenCart** | From OpenCart Extension Directory; upload files | Extensions > Payments > PayHere > Install > Edit: Status Enabled, Merchant ID, Secret Key, Sandbox Mode, Order Status = Complete. Same PayHere-side Secret Key rule |
| **Shopify** | PayHere Payment App (one-click): Add App > Install > enter Merchant ID + Merchant Secret > Save > "Activate PayHere Payment Gateway" | Settings > Payments > PayHere Payment Gateway > Manage. Old plugin removed from Settings > Payments. Gateway re-ordering needs Shopify Plus scripts or Shopify support |
| **Magento 1.x** | Upload files to the Magento dir, flush cache | System > Configuration > Payment Methods > PayHere |
| **Magento 2.x** | Pick the build for your version (2.4.6+, 2.3-2.4.5, 2.0-2.2.x); upload to `/app/code/`; run `bin/magento setup:upgrade`, clear `var/cache/*` and `generated/*`; flush cache and reindex | Stores > Configuration > Sales > Payment Methods > Other Payment Methods > PayHere |
| **PrestaShop 1.6 / 1.7** | Upload to `modules/`; 1.6: Modules and Services > Payments and Gateways; 1.7: Module Manager > Install > Configure | Merchant ID, Merchant Secret, Sandbox/Live-mode toggle (1.7 labels it "Live mode": select **No** for live, **Yes** for sandbox, which reads inverted) |
| **WHMCS** | Upload to `modules/gateways` | Setup > Payments > Payment Gateways > All Payment Gateways > PayHere (or Manage Existing Gateways) |
| **CS-Cart** | Add-ons > Manage add-ons > gear > Manual Installation > Local upload | Administration > Payment methods > + > processor "PayHere" > Configure tab |
| **Moodle 3.9+** | Site Administration > Plugins > Install plugins, plugin type "Enrolment method (enrol)" | Plugins overview > PayHere > Settings; enable under Manage enrol plugins; add PayHere as enrolment method per course |
| **ShopHere** | Built-in | ShopHere Settings > Payments > Enable Online Payments, PayHere Merchant ID; Merchant Secret only needed with a custom domain |

Notes
- Secret must match between the plugin and the PayHere dashboard (per-domain secret, so register the shop's domain first).
- Plugin sandbox mode needs sandbox merchant ID/secret, not live ones.
- If a plugin version or admin path differs from this table, it may have been updated; check the plugin's own docs.
