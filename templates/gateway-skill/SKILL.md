---
name: GATEWAY_SLUG
description: Expert knowledge of GATEWAY_NAME (domain), covering code integration AND account/support questions. Use whenever the user mentions GATEWAY_NAME, its domains, its API names or parameter names, or errors like ... even if they never say the name.
---

# GATEWAY_NAME

One-paragraph summary: who it serves, regulator, sandbox vs live.

## How to use this skill
1. Identify the task with the routing table.
2. Read only the matching reference file(s).
3. State that fees/limits come from docs as of <date>; point to official support for anything contractual.

## Routing table
| User needs | Read |
|---|---|
| Checkout / one-time payment | `references/checkout-api.md` |
| Subscriptions / recurring | `references/recurring.md` |
| Server APIs, refunds | `references/server-api.md` |
| SDKs / plugins | `references/sdks-plugins.md` |
| Test cards, sandbox | `references/sandbox-testing.md` |
| Plans, fees, onboarding | `references/account-business.md` |
| Errors, doc contradictions | `references/troubleshooting.md` |

## Core rules
1. Signing: ...
2. Webhook verification: ...
3. URLs / environments: ...

## Working style
- Flag documented contradictions; never invent parameters.
- Secrets in env vars only.
