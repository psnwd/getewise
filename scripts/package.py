#!/usr/bin/env python3
"""Zip every skill in skills/ into dist/<name>.skill (what Claude.ai's "Upload skill" expects).

    python scripts/package.py            # all skills
    python scripts/package.py payhere    # one skill
"""
import sys, zipfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
names = sys.argv[1:] or sorted(p.name for p in (root / "skills").iterdir() if (p / "SKILL.md").exists())
(root / "dist").mkdir(exist_ok=True)
for n in names:
    src = root / "skills" / n
    if not (src / "SKILL.md").exists():
        sys.exit(f"no skills/{n}/SKILL.md")
    out = root / "dist" / f"{n}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(src.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.suffix != ".pyc":
                z.write(f, Path(n) / f.relative_to(src))
    print("wrote", out.relative_to(root))
