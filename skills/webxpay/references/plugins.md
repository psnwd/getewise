# Plugins and platforms

Both plugin guides require the public and secret keys from the Merchant Portal and a return URL set under Settings > Website integration.

- **Shopify** (app store: apps.shopify.com/webxpay): install app > Manage > enter public + secret keys > pick payment methods, optional Test mode > in the portal add return URL `https://webxpay.secureapps.center/reply.php`.
- **WooCommerce** (plugin v5.4.1 zip from developers.webxpay.com/Plugins): Plugins > Add > Upload > Activate > WooCommerce > Settings > Payments > WebXpay > Manage > tick "Enable WebXpay Module", paste keys, optional "Save Card" (one-click payments), save > in the portal add return URL `https://yourdomain.com/checkout/order-received/`.
- **Magento 2.4.x, OpenCart 3.0.x, PrestaShop 1.7.x, WHMCS V3.2**: the current site dropped their guides, but the zips are still served under `integration.webxpay.com/Plugins/`. Treat them as reference code: the Magento module hard-disables refunds (`$_canRefund = false`) and the WHMCS refund function is an empty stub.
- Official sample projects (zip downloads): PHP redirect, PHP token, React, .NET, Node, JS (the Python link is a placeholder). The Node and .NET samples are the ones that show RSA-PSS return-signature verification; the PHP samples still show the older recovery scheme.

## What the plugins reveal
- `POST /api/v2/merchant/hc/cards/saveandpay` and the redirect form both read `payment` fields 5-7 (`payment_gateway_used`, requested amount, transaction amount) — the amount **is** in newer responses.
- The redirect flow's one-click card saving is `token_parameter` (base64 of RSA-encrypted `userID|email|timestamp`) + `is_tokenize=true` + `version=5.2`, not Token V2.
- The Woo plugin treats return code `'10'` as success as well as `'00'`. That is likely a bug: `'10'` is not a documented status and its own index mapping is off by one for real payloads.
