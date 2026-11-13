# Install for agents

You are an AI coding agent. The user asked you to install the Gatewise skills. Follow this exactly.

Gatewise is plain files: no CLI, no login, no API keys, no network calls. Install means "put the skill folders where the agent looks for them".

## Step 1 — Pick a method

**Claude Code, all gateways (recommended)**

Inside Claude Code:

```
/plugin marketplace add psnwd/getewise
/plugin install gatewise@gatewise
```

**Claude Code, one skill only**

Same marketplace, then install one of: `payhere`, `onepay`, `webxpay`, `genie`, `koko`, `payment-basics`, `payment-testing`, `payment-refunds`, `payment-security-review` — e.g. `/plugin install payhere@gatewise`. Use `gatewise` for the router itself.

**Claude Code, manual copy**

macOS / Linux:

```bash
git clone https://github.com/psnwd/getewise.git
mkdir -p ~/.claude/skills
cp -r getewise/skills/* ~/.claude/skills/
```

Windows (PowerShell):

```powershell
git clone https://github.com/psnwd/getewise.git
New-Item -ItemType Directory -Force $env:USERPROFILE\.claude\skills | Out-Null
Copy-Item -Recurse getewise\skills\* $env:USERPROFILE\.claude\skills\
```

One gateway is enough for most users: copy only that folder, e.g. `skills/payhere`.

**Other agents (Cursor, Codex CLI, Gemini CLI, ...)**

Each skill is a standard `SKILL.md` plus `references/` and optional `scripts/`. Copy the skill folder into that tool's skills directory, keeping the folder name (`payhere`, `onepay`, ...). Ask the user where their tool expects skills if it is not obvious; do not invent a path.

**Claude.ai (web or desktop)**

The user must do this one by hand: download the gateway from the latest GitHub Release (or build it with `python scripts/package.py` into `dist/`) (for example `payhere.skill`), then Settings → Capabilities → Skills → upload. Offer the file path and stop.

## Step 2 — Verify

Two checks, cheapest first.

**a) The helper scripts still work.** From the repo root:

```bash
python skills/payhere/scripts/payhere_sign.py hash \
  --merchant-id 1211149 --order-id ItemNo12345 --amount 1000 --currency LKR --secret testsecret
```

Expect exactly:

```
157365BBAF81B09B3FEC1749C1ED915D
```

If the user installed from the marketplace rather than a clone, skip this and go to (b).

**b) A question only the skill gets right.** Ask the agent (yourself):

> "My PayHere `notify_url` never fires when I test locally. What's wrong?"

The answer must say that `notify_url` has to be a public HTTPS URL, that `localhost` never works, and suggest a tunnel (cloudflared or ngrok) with re-registration. If the answer hedges or invents a `localhost` support flag, the skill is not loaded.

Full repo health (contributors only):

```bash
python scripts/package.py   # builds dist/*.skill (gitignored)
python scripts/verify.py
```

`verify.py` checks frontmatter, linked references, evals, signing vectors, manifests, README coverage, relative links and committed secrets.

## Step 3 — Report

Tell the user which skills are installed and give them two starter prompts, not a file tree. For example:

- "Add PayHere checkout to my Express app and verify the payment notification."
- "My OnePay refund failed in sandbox, what's wrong?"

Point them at [COOKBOOK.md](COOKBOOK.md) for full workflows.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Agent answers PayHere questions from memory | Skill folder is nested one level too deep | `SKILL.md` must sit directly in `~/.claude/skills/<name>/` |
| Only one gateway works | Only that plugin was installed | Install `gatewise@gatewise` or copy all of `skills/*` |
| Wrong gateway chosen for a "which gateway" question | Router not installed | Install the `gatewise` skill too |
| `payhere_sign.py` output differs | Wrong secret or reformatted amount | Amount must be two decimals, no thousands separators; secret from env |
| `verify.py` skips RSA tests | `cryptography` missing | `pip install cryptography` |

Never ask the user for a real merchant secret, App Secret or private key during install. Nothing here needs one.
