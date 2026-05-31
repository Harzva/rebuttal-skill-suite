#!/usr/bin/env python3
"""Generate a draft reviewer-issue map from review text.

The output is intentionally a draft. It gives authors a CSV scaffold that should
be manually checked before it is used with check_reviewer_issue_map.py.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


ISSUE_COLUMNS = [
    "reviewer",
    "issue_id",
    "concern",
    "response_anchor",
    "status",
    "evidence_pointer",
    "rationale",
]

CUE_RE = re.compile(
    r"\b(unclear|missing|concern|question|weak|limitation|cost|runtime|memory|"
    r"latency|baseline|fair|comparison|negative|failure|threshold|protocol|"
    r"label|tuned|fixed|ablation|evidence|artifact|reproduc)\b",
    re.I,
)
HEADING_RE = re.compile(
    r"^\s{0,3}(?:#{1,6}\s*)?(?:reviewer|review|referee|r)\s*[:#-]?\s*([A-Za-z0-9_-]+)\b",
    re.I,
)
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.*\S)\s*$")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{2,}")

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "although",
    "because",
    "before",
    "between",
    "could",
    "does",
    "evidence",
    "from",
    "have",
    "method",
    "paper",
    "result",
    "should",
    "table",
    "their",
    "there",
    "these",
    "this",
    "those",
    "using",
    "with",
    "would",
}


@dataclass
class Issue:
    reviewer: str
    concern: str
    anchor: str = ""


def normalize_reviewers(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def reviewer_from_line(line: str, reviewers: list[str]) -> Optional[str]:
    match = HEADING_RE.search(line)
    if match:
        return match.group(1)
    for reviewer in reviewers:
        if re.search(rf"\b{re.escape(reviewer)}\b", line):
            if line.lstrip().startswith("#") or re.search(r"\breviewer\b|\breview\b", line, re.I):
                return reviewer
    return None


def strip_markup(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[[^\]]+\]\([^)]*\)", lambda m: m.group(0).split("]", 1)[0].lstrip("["), text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> Iterable[str]:
    for part in re.split(r"(?<=[.!?])\s+", text):
        part = strip_markup(part)
        if part:
            yield part


def collect_issues(review_text: str, reviewers: list[str], max_per_reviewer: int) -> list[Issue]:
    sections: list[tuple[str, list[str]]] = []
    current_reviewer = "UNASSIGNED"
    current_lines: list[str] = []

    for line in review_text.splitlines():
        maybe_reviewer = reviewer_from_line(line, reviewers)
        if maybe_reviewer:
            if current_lines:
                sections.append((current_reviewer, current_lines))
            current_reviewer = maybe_reviewer
            current_lines = []
            continue
        current_lines.append(line.rstrip())
    if current_lines:
        sections.append((current_reviewer, current_lines))

    issues: list[Issue] = []
    for reviewer, lines in sections:
        concerns: list[str] = []
        prose_parts: list[str] = []
        for line in lines:
            bullet = BULLET_RE.match(line)
            if bullet:
                item = strip_markup(bullet.group(1))
                if item:
                    concerns.append(item)
                continue
            if line.strip() and not line.lstrip().startswith("#"):
                prose_parts.append(line.strip())
        for sentence in split_sentences(" ".join(prose_parts)):
            if CUE_RE.search(sentence):
                concerns.append(sentence)
        if not concerns:
            fallback = [strip_markup(line) for line in lines if strip_markup(line) and not line.lstrip().startswith("#")]
            concerns.extend(fallback[:max_per_reviewer])
        seen: set[str] = set()
        kept = 0
        for concern in concerns:
            concern = concern[:240].strip()
            key = concern.lower()
            if not concern or key in seen:
                continue
            seen.add(key)
            issues.append(Issue(reviewer=reviewer, concern=concern))
            kept += 1
            if kept >= max_per_reviewer:
                break
    return issues


def choose_anchor(concern: str, response_text: str) -> str:
    if not response_text:
        return ""
    response_lower = response_text.lower()
    words = [w.lower() for w in WORD_RE.findall(concern)]
    candidates = [w for w in words if len(w) >= 5 and w not in STOPWORDS]
    for word in candidates:
        if word in response_lower:
            return word
    for left, right in zip(candidates, candidates[1:]):
        phrase = f"{left} {right}"
        if phrase in response_lower:
            return phrase
    return ""


def issue_id(reviewer: str, index: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "", reviewer) or "R"
    return f"{safe}-I{index:02d}"


def write_csv(issues: list[Issue], output: Optional[Path]) -> None:
    handle = output.open("w", newline="", encoding="utf-8") if output else sys.stdout
    close = output is not None
    try:
        writer = csv.DictWriter(handle, fieldnames=ISSUE_COLUMNS)
        writer.writeheader()
        counters: dict[str, int] = {}
        for issue in issues:
            counters[issue.reviewer] = counters.get(issue.reviewer, 0) + 1
            writer.writerow(
                {
                    "reviewer": issue.reviewer,
                    "issue_id": issue_id(issue.reviewer, counters[issue.reviewer]),
                    "concern": issue.concern,
                    "response_anchor": issue.anchor,
                    "status": "candidate" if issue.anchor else "draft",
                    "evidence_pointer": "",
                    "rationale": "draft row; verify anchor and evidence before gating",
                }
            )
    finally:
        if close:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviews", type=Path, help="Review text, Markdown, or exported comments.")
    parser.add_argument("--response", type=Path, help="Optional rebuttal draft used to guess response anchors.")
    parser.add_argument("--reviewers", help="Comma-separated reviewer IDs to recognize, e.g. R1,R2,R3.")
    parser.add_argument("--max-per-reviewer", type=int, default=12)
    parser.add_argument("--output", type=Path, help="Write CSV here instead of stdout.")
    args = parser.parse_args()

    review_text = args.reviews.read_text(encoding="utf-8", errors="replace")
    response_text = args.response.read_text(encoding="utf-8", errors="replace") if args.response else ""
    issues = collect_issues(review_text, normalize_reviewers(args.reviewers), args.max_per_reviewer)
    for issue in issues:
        issue.anchor = choose_anchor(issue.concern, response_text)
    write_csv(issues, args.output)
    if not issues:
        print("WARNING\tno reviewer issues detected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
