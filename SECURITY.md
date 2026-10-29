# Security

Gatewise is plain files: Markdown notes, small helper scripts and example code. It has no server and collects nothing.

## Report a problem
- **A skill gives advice that could lose money or leak secrets** (for example, a wrong signature check or a step that exposes a key): open an issue using the "wrong fact" template, or email the maintainer via the GitHub profile if it is sensitive.
- **A leaked secret or private document in this repo:** report it privately first, so it can be removed and rotated.

## Rules the skills follow
- Secrets (API keys, salts, merchant secrets, tokens) come from environment variables, never from code in answers.
- Payment is confirmed server-side from the gateway's API or a verified callback, never from a browser redirect.
- Helper scripts read secrets from the environment, not from command history where possible.

## Not covered
Gatewise is unofficial and not tested against live merchant accounts. Always test in the gateway's sandbox first.
