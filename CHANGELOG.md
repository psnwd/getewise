# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use `vX.Y.Z` tags.

**Releasing:** move the `[Unreleased]` entries under a new `## [X.Y.Z] - YYYY-MM-DD` heading, bump the version in `package.json`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, then `git tag vX.Y.Z && git push --tags`. The release workflow publishes that section as the release notes and attaches the `.skill` files.

## [Unreleased]
### Added
- Cross-agent install: `npx skills add psnwd/getewise` and `gh skill install psnwd/getewise <skill> --agent <agent>`, documented in the README and `INSTALL_FOR_AGENTS.md` (both commands tested against this repo).

### Changed
- `COOKBOOK.md` and `evals/README.md`: aligned with the 0.4.0 re-check — PayHere notifications are sent once (so reconciliation is required), PayHere partial refunds are contradictory and must be confirmed, Koko refunds are portal-only and full-only, WebXPay's return check is PSS/SHA-1.

## [0.4.0] - 2026-11-13
### Added
- `COOKBOOK.md`: ten end-to-end recipes (PayHere checkout, Koko BNPL, WebXPay redirect, Genie webhooks, OnePay, recurring/saved cards, two-gateway failover, pre-launch review, refunds, adding a gateway), each with the prompt, the steps, and the rules the agent must not get wrong.
- `INSTALL_FOR_AGENTS.md`: install steps written for an agent, with a hash-vector check and a question-based check that proves the skill loaded.
- `evals/README.md`: how a round is scored, what to record in `docs/benchmarks`, and when to add a case.
- `docs/doc-recheck-2026-11.md`: what the November doc re-check resolved, the sources used and what is still unpublished.
- `onepay/references/subscriptions.md`: the `/v3/subscription/` API recovered from the archived docs and the npm SDK.

### Changed
- **All gateway skills re-checked against the live docs on 13 Nov 2026** (samples, plugin source and spec mocks where the prose is thin). Contradictions that couldn't be settled are still flagged, with the evidence on both sides.
- **WebXPay**: the return signature is **RSA-PSS / SHA-1**, not PKCS#1 v1.5 recovery — the old PHP sample fails on real responses, so `webxpay_crypto.py` (and the CI vector) now verify PSS first and keep recovery as a fallback. The response is documented as eight fields including requested/transaction amounts; the refund API is confirmed absent; published test cards and staging MIDs are listed.
- **PayHere**: Authorize success is code `3` (the page's own PHP sample still checks `== 2`); notifications are sent once and never retried, so a reconciliation sweep is required; permission/menu split corrected; add-on fees and Hold-on-Card rules added.
- **OnePay**: sandbox is an app mode on the same host, not a separate host; create-response schema, lowercase-hex hash, raw `AppToken` auth and the portal Callback Token/CIDR controls documented.
- **Genie**: Get Transaction path settled; `expiryDate`, `recurringFrequency` and refund-unit questions narrowed; webhook, customer and token endpoints documented; fees and settlement (now public) added.
- **Koko**: callback is RSA-SHA256 over `orderId+trnId+status` (JSON or form), error envelope and observed codes documented, refunds are portal-only and full-only, account/support facts added.
- `payment-testing` and `payment-refunds` matrices updated to match the gateway skills.

## [0.3.0] - 2026-11-02
### Added
- **Router: external providers** (Stripe, PayPal, Paddle, Lemon Squeezy) point to the vendors' current skills/docs instead of embedding API facts; 1 new eval.
- **`payment-testing` skill**: per-gateway sandbox and test-card facts, live-only gaps, scenario checklist; 3 evals.
- **`payment-refunds` skill**: refund/partial/chargeback matrix for the five gateways (marks undocumented ones) and a safe refund endpoint design; 3 evals.

## [0.2.0] - 2026-11-02
### Added
- **`gatewise` router skill**: picks the gateway skill from the user's region, features and stack; 3 evals.
- **`payment-basics` skill**: gateway-agnostic idempotency, callback verification, reconciliation, PCI scope and secrets; 3 evals.
- **`payment-security-review` skill**: evidence-based review checklist and report format for payment code (forged callbacks, amount tampering, secret leaks, IDOR, refund abuse); method adapted from cloudflare/security-audit-skill; 3 evals.
- **Multi-provider guide** (`references/multi-provider.md`) in every gateway skill: shared `Gateway` interface, one idempotent `settle()`, per-provider callbacks.
- **Koko**: webhook handlers (Express, Next.js, Laravel, FastAPI, Django) and an `orderView` reconciliation job, runtime-tested for Express and FastAPI.
- Standalone plugin entries for the router, `payment-basics` and `payment-security-review`.
- `scripts/changelog_notes.py`; release workflow now publishes the CHANGELOG section as release notes.

### Changed
- `.env` guidance in all five gateway skills: one banner-headed block per provider, prefixed variable names, all providers when none is named.

## [0.1.0] - 2026-10-29
### Added
- Skills: PayHere, OnePay, WebXPay, Genie Business (Dialog Pay Business), Koko (BNPL), each with references, helper script (where useful), 3 evals and a benchmark.
- Claude Code plugin marketplace (`gatewise` bundle plus one plugin per gateway).
- `scripts/verify.py` (CI) and `scripts/package.py` (builds `dist/*.skill`).
- Logo, banner, README, roadmap, contributing guide, gateway template.

[Unreleased]: https://github.com/psnwd/getewise/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/psnwd/getewise/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/psnwd/getewise/releases/tag/v0.1.0
