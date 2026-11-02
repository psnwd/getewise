# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use `vX.Y.Z` tags.

**Releasing:** move the `[Unreleased]` entries under a new `## [X.Y.Z] - YYYY-MM-DD` heading, bump the version in `package.json`, `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, then `git tag vX.Y.Z && git push --tags`. The release workflow publishes that section as the release notes and attaches the `.skill` files.

## [Unreleased]

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
