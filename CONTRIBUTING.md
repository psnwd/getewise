# Contributing

Thanks for helping! The most useful contributions:

1. **A new gateway.** Follow [docs/adding-a-gateway.md](docs/adding-a-gateway.md).
2. **A fix.** If a gateway changed its docs or a skill says something wrong, open a PR with a link to the official page that shows the correct fact.
3. **A new test question** under `evals/<gateway>/` that Claude gets wrong without the skill.

Ground rules
- Sources must be the gateway's **public docs**. No leaked or private material.
- Say where the docs are unclear. Put gaps in the gateway's `references/troubleshooting.md`; never fill them with guesses.
- Code samples: say which languages you actually ran. Mark the rest "not run".
- Never commit real keys, secrets or customer data.
- Run `python scripts/package.py` then `python scripts/verify.py` before a PR. CI runs `verify.py` and fails if `dist/` is stale, a reference file is unlinked, or a signing helper no longer matches its test vector.
- Releases: tag `vX.Y.Z` and the release workflow attaches the `.skill` files.

See also [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [CHANGELOG.md](CHANGELOG.md). Add a line to the changelog for user-visible changes.
