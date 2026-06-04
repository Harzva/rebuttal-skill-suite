#!/usr/bin/env python3
"""Sanitize private dashboard data into a public README/webview sample."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

LOCAL_PATH_RE = re.compile(r"(?:/[^\s:]+){2,}|[A-Za-z]:\\[^\s]+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SUBMISSION_RE = re.compile(r"\b(?:submission|paper|openreview|cmt)[-_ ]?(?:id)?[:# ]+[A-Za-z0-9_-]+\b", re.I)
PRIVATE_WORDS = [
    re.compile(r"老师|导师|改分|开发者备注"),
    re.compile(r"\b(AC-facing|dangerous reviewer|score increase|private note|internal note)\b", re.I),
]


def sanitize_str(value: str, project_title: str) -> str:
    value = LOCAL_PATH_RE.sub("[local path removed]", value)
    value = EMAIL_RE.sub("[email removed]", value)
    value = SUBMISSION_RE.sub("[submission id removed]", value)
    for pattern in PRIVATE_WORDS:
        value = pattern.sub("[private process removed]", value)
    return value


def walk(value: Any, project_title: str) -> Any:
    if isinstance(value, str):
        return sanitize_str(value, project_title)
    if isinstance(value, list):
        return [walk(item, project_title) for item in value]
    if isinstance(value, dict):
        return {key: walk(item, project_title) for key, item in value.items() if key not in {"raw_sources", "source_paths", "private_notes"}}
    return value


def normalize_reviewers(data: dict[str, Any]) -> None:
    reviewers = data.get("reviewers", [])
    mapping = {}
    for idx, reviewer in enumerate(reviewers, start=1):
        old = str(reviewer.get("id", f"R{idx}"))
        new = f"R{idx}"
        mapping[old] = new
        reviewer["id"] = new
    for issue in data.get("issues", []):
        issue["reviewers"] = [mapping.get(str(r), str(r) if str(r).startswith("R") else "R?") for r in issue.get("reviewers", [])]
    for reviewer in reviewers:
        reviewer["anchors"] = [str(anchor) for anchor in reviewer.get("anchors", [])]


def check_public(data: dict[str, Any]) -> list[str]:
    text = json.dumps(data, ensure_ascii=False)
    issues = []
    checks = [LOCAL_PATH_RE, EMAIL_RE, SUBMISSION_RE, *PRIVATE_WORDS]
    for pattern in checks:
        if pattern.search(text):
            issues.append(f"public data still matches private pattern: {pattern.pattern}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-title", default="Anonymized Rebuttal Project")
    parser.add_argument("--check", action="store_true", help="Check the output after writing and fail on obvious private patterns.")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    data = walk(data, args.project_title)
    data["title"] = "Anonymous Rebuttal Dashboard"
    data["subtitle"] = "Sanitized demo data for an evidence-backed rebuttal review loop"
    data["project"] = args.project_title
    data["generated_at"] = datetime.now().strftime("%Y-%m-%d")
    data["branch"] = "sanitized-demo"
    data["sync_status"] = "public sample"
    data["notes"] = list(data.get("notes", [])) + [
        "This is sanitized public sample data, not a live private project dashboard.",
        "Reviewer IDs, project names, local paths, and private process details are anonymized or removed.",
    ]
    normalize_reviewers(data)

    issues = check_public(data)
    if issues:
        print("SANITIZE_CHECK_FAILED")
        for issue in issues:
            print(f"ISSUE\t{issue}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"WROTE_SANITIZED_DASHBOARD {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
