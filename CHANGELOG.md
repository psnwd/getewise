# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/). Versions use `vX.Y.Z` tags.

## [Unreleased]
### Added
- `gatewise` router skill: picks a gateway skill from region, features and stack (with 3 evals).
- `payment-security-review` skill: evidence-based security review checklist and report format for payment code, method adapted from cloudflare/security-audit-skill (with 3 evals).
- `payment-basics` skill: gateway-agnostic idempotency, callback verification, reconciliation, PCI and secrets (with 3 evals).
- `references/multi-provider.md` in every gateway skill; Koko webhook handlers and `orderView` reconciliation example; banner-separated per-provider `.env` guidance.

## [0.1.0] - 2026-10-29
### Added
- Skills: PayHere, OnePay, WebXPay, Genie Business (Dialog Pay Business), Koko (BNPL), each with references, helper script (where useful), 3 evals and a benchmark.
- Claude Code plugin marketplace (`gatewise` bundle plus one plugin per gateway).
- `scripts/verify.py` (CI) and `scripts/package.py` (builds `dist/*.skill`).
- Logo, banner, README, roadmap, contributing guide, gateway template.
