#!/usr/bin/env python3
"""Print the CHANGELOG.md section for a version (release notes).

    python scripts/changelog_notes.py v0.2.0     # or 0.2.0

Exits 1 if the section is missing or empty, so a release cannot ship without notes.
"""
import re, sys
from pathlib import Path

ver = sys.argv[1].lstrip("v")
text = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
m = re.search(rf"^## \[{re.escape(ver)}\][^\n]*\n(.*?)(?=^## \[|^\[[^\]]+\]:|\Z)", text, re.S | re.M)
body = m.group(1).strip() if m else ""
if not body:
    sys.exit(f"CHANGELOG.md has no notes for [{ver}]")
print(body)
