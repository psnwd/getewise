#!/usr/bin/env python3
"""Repo checks run by CI (and by you before a PR):  python scripts/verify.py

1. Every skills/<name>/ has a valid SKILL.md (name == folder, description <= 1024 chars).
2. Every references/ file the SKILL.md links to exists, and every reference file is linked.
3. Every evals/<name>/ case has prompt.md + case.yaml + graders.
4. Each gateway's signing helper still reproduces its known test vector.
5. Plugin manifests are valid JSON and list every skill.
6. dist/*.skill files match skills/ (run `python scripts/package.py` if not).
7. README lists every skill.
8. Relative links in Markdown files resolve.
9. No private keys or live-looking secrets are committed.
10. Manifest versions agree.
"""
import hashlib, json, re, subprocess, sys, zipfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
errors = []
def err(m): errors.append(m); print("FAIL", m)
def ok(m): print("ok  ", m)

skills = sorted(p.name for p in (root / "skills").iterdir() if p.is_dir())

# 1-2 skills
for n in skills:
    d = root / "skills" / n
    md = d / "SKILL.md"
    if not md.exists(): err(f"{n}: SKILL.md missing"); continue
    text = md.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m: err(f"{n}: no frontmatter"); continue
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    if not name or name.group(1).strip() != n: err(f"{n}: frontmatter name must equal folder name")
    if not desc: err(f"{n}: description missing")
    elif len(desc.group(1)) > 1024: err(f"{n}: description is {len(desc.group(1))} chars (max 1024)")
    refs = {p.name for p in (d / "references").glob("*.md")} if (d / "references").exists() else set()
    linked = set(re.findall(r"references/([\w.-]+\.md)", text))
    for r in sorted(linked - refs): err(f"{n}: SKILL.md links references/{r} which does not exist")
    for r in sorted(refs - linked): err(f"{n}: references/{r} is not linked from SKILL.md")
    for s in re.findall(r"scripts/([\w.-]+\.py)", text):
        if not (d / "scripts" / s).exists(): err(f"{n}: SKILL.md mentions scripts/{s} which does not exist")
    ok(f"{n}: SKILL.md + {len(refs)} references")

# 3 evals
for n in skills:
    e = root / "evals" / n
    cases = [c for c in e.iterdir() if c.is_dir()] if e.exists() else []
    if not cases: err(f"{n}: no evals/{n}/ cases"); continue
    for c in cases:
        for f in ("prompt.md", "case.yaml"):
            if not (c / f).exists(): err(f"evals/{n}/{c.name}: {f} missing")
        if not list((c / "graders").glob("*.md")): err(f"evals/{n}/{c.name}: no graders")
    ok(f"{n}: {len(cases)} eval cases")

# 4 signing helpers: known vectors
def run(*a, env=None):
    import os
    return subprocess.run([sys.executable, *a], capture_output=True, text=True, env={**os.environ, **(env or {})})
r = run("skills/payhere/scripts/payhere_sign.py", "--help")
if r.returncode: err("payhere_sign.py --help failed: " + r.stderr[-200:])
else: ok("payhere_sign.py runs")
r = run("skills/onepay/scripts/onepay_sign.py", "hash", "--app-id", "APP123", "--currency", "LKR", "--amount", "1500", env={"ONEPAY_SALT": "testsalt"})
if "763cbcabf99331edfac5d5a5301f08364b85da3ae4e27e5bdab25d99ce819482" not in r.stdout: err("onepay hash vector mismatch: " + r.stdout + r.stderr)
else: ok("onepay hash vector")
want = hashlib.sha256(b"APP123LKR1500.00testsalt").hexdigest()
if want not in r.stdout: err("onepay hash differs from SHA256(app_id+currency+amount+salt)")
r = run("skills/genie/scripts/genie_webhook.py", "sign", "--nonce", "n1", "--timestamp", "1700000000", env={"GENIE_API_KEY": "testkey"})
want = hashlib.sha256(b"n11700000000testkey").hexdigest()
if want not in r.stdout or want != "95c7088ce897c937b06fa06b6c08048563b18cb8104e8d449eeb0d89f20af8d6": err("genie webhook signature mismatch: " + r.stdout + r.stderr)
else:
    v = run("skills/genie/scripts/genie_webhook.py", "verify", "--nonce", "n1", "--timestamp", "1700000000", "--signature", want, env={"GENIE_API_KEY": "testkey"})
    bad = run("skills/genie/scripts/genie_webhook.py", "verify", "--nonce", "n1", "--timestamp", "1700000001", "--signature", want, env={"GENIE_API_KEY": "testkey"})
    if v.returncode or "VALID" not in v.stdout or bad.returncode == 0: err("genie verify wrong")
    else: ok("genie webhook signature vector (valid accepted, tampered rejected)")
try:
    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    pub = key.public_key()
    import tempfile, os
    fd, tmpname = tempfile.mkstemp(suffix=".pem"); os.close(fd); tmp = Path(tmpname)
    tmp.write_bytes(pub.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    pay = b"12001|T372016I24522|2016-04-20 09:57:52|00|Approved|40"
    nums = key.private_numbers(); n_, d_ = nums.public_numbers.n, nums.d
    k = (n_.bit_length() + 7) // 8
    em = b"\x00\x01" + b"\xff" * (k - len(pay) - 3) + b"\x00" + pay
    sig = pow(int.from_bytes(em, "big"), d_, n_).to_bytes(k, "big")
    r = run("skills/webxpay/scripts/webxpay_crypto.py", "verify", "--key", str(tmp),
            "--payment", base64.b64encode(pay).decode(), "--signature", base64.b64encode(sig).decode())
    bad = run("skills/webxpay/scripts/webxpay_crypto.py", "verify", "--key", str(tmp),
              "--payment", base64.b64encode(b"x|y").decode(), "--signature", base64.b64encode(sig).decode())
    tmp.unlink()
    if "VALID" not in r.stdout or r.returncode: err("webxpay verify rejected a valid signature")
    elif bad.returncode == 0: err("webxpay verify accepted a forged payment")
    else: ok("webxpay RSA sign/verify round trip (accepts valid, rejects forged)")
except ImportError:
    print("skip webxpay round trip (pip install cryptography)")

# 5 manifests
for f in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "package.json"):
    try: json.loads((root / f).read_text(encoding="utf-8"))
    except Exception as ex: err(f"{f}: {ex}")
mk = json.loads((root / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
listed = {s.lstrip("./") for p in mk["plugins"] for s in p["skills"]}
for n in skills:
    if n not in listed: err(f"marketplace.json does not list skill {n}")
ok("plugin manifests")

# 6 dist
for n in skills:
    z = root / "dist" / f"{n}.skill"
    if not z.exists(): err(f"dist/{n}.skill missing (python scripts/package.py)"); continue
    with zipfile.ZipFile(z) as zf:
        packed = {i.filename: hashlib.sha256(zf.read(i)).hexdigest() for i in zf.infolist() if not i.is_dir()}
    src = {str(Path(n) / f.relative_to(root / "skills" / n)).replace("\\", "/"): hashlib.sha256(f.read_bytes()).hexdigest()
           for f in (root / "skills" / n).rglob("*") if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc"}
    if packed != src: err(f"dist/{n}.skill is out of date (python scripts/package.py)")
    else: ok(f"dist/{n}.skill up to date")

# 7 README
readme = (root / "README.md").read_text(encoding="utf-8")
for n in skills:
    if f"skills/{n}/SKILL.md" not in readme: err(f"README.md does not list {n}")
ok("README lists all skills")

# 8 relative markdown links
for md in list(root.glob("*.md")) + list((root / "docs").rglob("*.md")) + list((root / "skills").rglob("*.md")):
    text = md.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if re.match(r"^(https?:|mailto:|#)", target): continue
        path = target.split("#")[0]
        if path and not (md.parent / path).resolve().exists():
            err(f"{md.relative_to(root)}: broken link {target}")
ok("markdown relative links")

# 9 secrets scan
bad = re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|sk_live_[0-9a-zA-Z]{10,}|AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{30,}")
for f in root.rglob("*"):
    if not f.is_file() or f.suffix in {".skill", ".png", ".ico", ".svg"} or {".git", "dist", "node_modules"} & set(f.parts): continue
    try: t = f.read_text(encoding="utf-8")
    except Exception: continue
    if bad.search(t): err(f"possible secret in {f.relative_to(root)}")
ok("no secrets found")

# 10 versions
vers = {json.loads((root / "package.json").read_text())["version"],
        json.loads((root / ".claude-plugin/plugin.json").read_text())["version"]}
vers |= {p["version"] for p in mk["plugins"]}
if len(vers) != 1: err(f"manifest versions differ: {sorted(vers)}")
else: ok(f"manifest versions agree ({vers.pop()})")

print()
if errors: sys.exit(f"{len(errors)} problem(s)")
print("all checks passed")
