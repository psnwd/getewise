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

**Any agent, one command (`npx skills`)**

```bash
npx skills add psnwd/getewise
```

Needs Node.js 22.20+. The CLI detects installed agents; an interactive run asks which skills go to which agent. Non-interactive forms:

```bash
npx skills add psnwd/getewise --all -y                          # every skill, every detected agent
npx skills add psnwd/getewise --skill payhere -a claude-code -g -y # one skill, global, all projects
```

Project install (the default) writes the skills to `.agents/skills/` and records them in `skills-lock.json`; `-g` installs user-wide instead. On Windows it copies rather than links by default; `--copy` forces copies anywhere.

**GitHub CLI (`gh skill`, v2.90+)**

```bash
gh skill install psnwd/getewise                                  # list skills in the repo
gh skill install psnwd/getewise payhere --agent cursor --scope user
gh skill install psnwd/getewise --all --agent claude-code        # everything, project scope
gh skill preview psnwd/getewise payhere                          # read one before installing
```

`gh` discovers `skills/<name>/SKILL.md` automatically. `--pin vX.Y.Z` installs a release tag; default scope is project, default agent under `--yes` is `github-copilot`, so always pass `--agent`.

**Other agents (manual)**

Copy the skill folder into that tool's skills directory, keeping the folder name. Ask the user where their tool expects skills if it is not obvious; do not invent a path.

**Claude.ai (web or desktop)**

The user must do this one by hand: download `payhere.skill` (or whichever gateway they want) from the latest GitHub Release, or build it locally with `python scripts/package.py` into `dist/`. Then Settings → Capabilities → Skills → upload, and start a chat. Give them the file path and stop here.

## Step 2 — Verify

Three checks, cheapest first.

**a) The skills landed.**

```bash
npx skills list                 # installed skills, with source
npx skills add psnwd/getewise --list   # what the repo offers, without installing
```

Expect ten: `gatewise`, `payhere`, `onepay`, `webxpay`, `genie`, `koko`, `payment-basics`, `payment-testing`, `payment-refunds`, `payment-security-review`. For `gh`, `gh skill install psnwd/getewise` prints the same list.

**b) The helper scripts still work.** From the repo root:

```bash
python skills/payhere/scripts/payhere_sign.py hash \
  --merchant-id 1211149 --order-id ItemNo12345 --amount 1000 --currency LKR --secret testsecret
```

Expect exactly:

```
157365BBAF81B09B3FEC1749C1ED915D
```

If the user installed via a plugin, `npx skills` or `gh skill` rather than a clone, skip this and go to (c).

**c) A question only the skill gets right.** Ask the agent (yourself):

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
| Agent answers PayHere questions from memory | Skill folder is nested one level too deep | `SKILL.md` must sit directly in `~/.claude/skills/<name>/` (or the tool's skills dir) |
| Only one gateway works | Only that plugin or `--skill` was installed | Install `gatewise@gatewise`, `npx skills add psnwd/getewise --all`, or copy all of `skills/*` |
| Wrong gateway chosen for a "which gateway" question | Router not installed | Install the `gatewise` skill too |
| `npx skills add` reports no skills | Node older than 22.20, or run outside the repo source | Upgrade Node; the repo uses the standard `skills/<name>/SKILL.md` layout |
| `npx skills` installs into the wrong place | Project scope is the default | Re-run with `-g` for user-wide, or `--agent` to target one tool |
| Symlink errors on Windows | Developer Mode off | Add `--copy` |
| `gh skill` command missing | GitHub CLI older than v2.90 | `gh extension upgrade --all` or update `gh` |
| `gh skill install` ignores the agent | Default agent under `--yes` is `github-copilot` | Always pass `--agent claude-code` (or your tool) |
| `payhere_sign.py` output differs | Wrong secret or reformatted amount | Amount must be two decimals, no thousands separators; secret from env |
| `verify.py` skips RSA tests | `cryptography` missing | `pip install cryptography` |

Never ask the user for a real merchant secret, App Secret or private key during install. Nothing here needs one.
