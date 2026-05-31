#!/usr/bin/env python3
"""Validate reviewer persona prompts or outputs use the required P0/P1/P2 structure."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED = [
    re.compile(r"^##\s*P0\s+findings\b", re.I | re.M),
    re.compile(r"^##\s*P1\s+findings\b", re.I | re.M),
    re.compile(r"^##\s*P2\s+(polish|findings)\b", re.I | re.M),
    re.compile(r"^##\s*Minimal\s+patch\b", re.I | re.M),
    re.compile(r"^##\s*.*recommendation\b", re.I | re.M),
]


def iter_markdown(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*.md")):
        if child.name.lower() == "readme.md":
            continue
        yield child


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Persona prompt/output file or directory")
    args = parser.parse_args()

    issues: list[str] = []
    checked = 0
    for path in iter_markdown(args.path):
        checked += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [pat.pattern for pat in REQUIRED if not pat.search(text)]
        if missing:
            issues.append(f"{path}: missing {len(missing)} required section(s)")

    if issues:
        print("PERSONA_STRUCTURE_FAILED")
        for issue in issues:
            print(issue)
        return 1

    print(f"PERSONA_STRUCTURE_OK checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
