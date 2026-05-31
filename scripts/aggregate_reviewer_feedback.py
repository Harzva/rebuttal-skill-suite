#!/usr/bin/env python3
"""Aggregate reviewer-persona feedback files into P0/P1/P2 buckets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SEVERITIES = ("P0", "P1", "P2")
SECTION_ALIASES = {
    "P0": re.compile(r"\b(P0|blocker|trust risk|fatal|must fix)\b", re.I),
    "P1": re.compile(r"\b(P1|major|should fix|concern|risk)\b", re.I),
    "P2": re.compile(r"\b(P2|minor|polish|optional|style)\b", re.I),
}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for child in sorted(path.rglob("*")):
        if child.suffix.lower() in {".md", ".txt"}:
            yield child


def normalize_item(item: str) -> str:
    item = re.sub(r"\s+", " ", item).strip()
    item = re.sub(r"^(finding|issue|risk|fix)\s*[:\-]\s*", "", item, flags=re.I)
    return item


def detect_heading(line: str) -> str | None:
    clean = re.sub(r"^#{1,6}\s*", "", line).strip()
    for sev, pattern in SECTION_ALIASES.items():
        if pattern.search(clean):
            return sev
    return None


def extract_items(text: str):
    current = None
    buckets = {key: [] for key in SEVERITIES}
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("#"):
            current = detect_heading(line)
            continue

        m = re.match(r"^(P[012])\s*[:\-]\s*(.+)", line, flags=re.I)
        if m:
            item = normalize_item(m.group(2))
            if item:
                buckets[m.group(1).upper()].append(item)
            continue

        m = re.match(r"^[-*]\s*(P[012])\s*[:\-]\s*(.+)", line, flags=re.I)
        if m:
            item = normalize_item(m.group(2))
            if item:
                buckets[m.group(1).upper()].append(item)
            continue

        if current and re.match(r"^([-*]|\d+[.)])\s+", line):
            item = normalize_item(re.sub(r"^([-*]|\d+[.)])\s+", "", line))
            if item and item.lower() != "none":
                buckets[current].append(item)
    return buckets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Feedback file or directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    parser.add_argument("--fail-on-p0", action="store_true", help="Exit nonzero when P0 findings are present")
    args = parser.parse_args()

    aggregate = {key: [] for key in SEVERITIES}
    for path in iter_files(args.path):
        buckets = extract_items(path.read_text(encoding="utf-8", errors="replace"))
        for severity, items in buckets.items():
            for item in items:
                aggregate[severity].append({"source": path.name, "item": item})

    deduped = {key: [] for key in SEVERITIES}
    for severity in SEVERITIES:
        seen = set()
        for entry in aggregate[severity]:
            key = re.sub(r"\W+", " ", entry["item"].lower()).strip()
            if key in seen:
                continue
            seen.add(key)
            deduped[severity].append(entry)

    if args.json:
        print(json.dumps(deduped, indent=2, ensure_ascii=False))
    else:
        print("# Aggregated Reviewer Feedback\n")
        for severity in SEVERITIES:
            print(f"## {severity} ({len(deduped[severity])})\n")
            if not deduped[severity]:
                print("- None\n")
                continue
            for entry in deduped[severity]:
                print(f"- [{entry['source']}] {entry['item']}")
            print()

        if deduped["P0"]:
            print("Recommendation: fix P0 before any style polish.")
        elif deduped["P1"]:
            print("Recommendation: resolve or explicitly bound P1 issues, then re-run gates.")
        else:
            print("Recommendation: submit or only apply optional P2 polish.")

    return 1 if args.fail_on_p0 and deduped["P0"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
