# Plugins and platforms

Both plugin guides require the public and secret keys from the Merchant Portal and a return URL set under Settings > Website integration.

- **Shopify** (app store: apps.shopify.com/webxpay): install app > Manage > enter public + secret keys > pick payment methods, optional Test mode > in the portal add return URL `https://webxpay.secureapps.center/reply.php`.
- **WooCommerce** (plugin v5.4.1 zip from developers.webxpay.com/Plugins): Plugins > Add > Upload > Activate > WooCommerce > Settings > Payments > WebXpay > Manage > tick "Enable WebXpay Module", paste keys, optional "Save Card" (one-click payments), save > in the portal add return URL `https://yourdomain.com/checkout/order-received/`.
- Magento, OpenCart, PrestaShop, WHMCS: listed in the nav, but no guide pages were published. Use the redirect integration with `cms` set to the platform name, or ask WebXPay for the module.
- Official sample projects (zip downloads, not read): PHP redirect, PHP token, React, .NET, Node, JS (Python link is a placeholder).
