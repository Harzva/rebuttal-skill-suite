#!/usr/bin/env python3
"""Check that the publishable skill-suite repo has no generated artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path


BAD_DIRS = {"__pycache__", ".pytest_cache"}
BAD_SUFFIXES = {
    ".aux",
    ".log",
    ".out",
    ".pdf",
    ".pyc",
    ".synctex.gz",
    ".fls",
    ".fdb_latexmk",
    ".toc",
    ".bbl",
    ".blg",
}


def bad_suffix(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in BAD_SUFFIXES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    findings: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".git" in rel_parts:
            continue
        if path.is_dir() and path.name in BAD_DIRS:
            findings.append(path)
        elif path.is_file() and bad_suffix(path):
            findings.append(path)

    if findings:
        print("REPO_CLEAN_FAILED")
        for path in findings:
            print(path.relative_to(root))
        return 1

    print("REPO_CLEAN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
