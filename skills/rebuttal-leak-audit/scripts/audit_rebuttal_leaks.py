#!/usr/bin/env python3
"""Scan reviewer-facing rebuttal drafts for leaked internal notes."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Rule:
    severity: str
    category: str
    pattern: re.Pattern[str]
    advice: str


RULES: list[Rule] = [
    Rule(
        "High",
        "local-path",
        re.compile(r"(?i)(/home/|/users/|/tmp/|/mnt/|/workspace/|[a-z]:\\|~/.codex|\.sock\b)"),
        "Remove local/user-specific paths; cite appendix, artifact name, or anonymous repo instead.",
    ),
    Rule(
        "High",
        "tool-trace",
        re.compile(r"(?i)\b(ran|running command|exec_command|tool call|tmux|nvidia-smi|sleep\s+\d+|tail\s+-n|pdflatex log|shell output)\b"),
        "Delete shell/tool traces; convert only the resulting scientific evidence to public prose.",
    ),
    Rule(
        "High",
        "ai-dev-trace",
        re.compile(r"(?i)\b(codex|chatgpt|claude|opus|developer note|system prompt|ide setup|open tabs|llm reviewer|persona feedback)\b"),
        "Remove AI/developer/reviewer-simulation traces entirely from reviewer-facing text.",
    ),
    Rule(
        "High",
        "advisor-internal-trace",
        re.compile(r"(?i)\b(teacher said|advisor said|advisor suggested|pi suggested|supervisor suggested|internal only|do not submit|draft only)\b|老师|导师|备注|改分"),
        "Remove advisor/internal attribution; keep only the reviewer-facing scientific point.",
    ),
    Rule(
        "High",
        "draft-marker",
        re.compile(r"(?i)\b(todo|fixme|note to self|placeholder|needs cleanup before submission)\b"),
        "Remove draft-only markers before public submission.",
    ),
    Rule(
        "Medium",
        "experiment-logistics",
        re.compile(r"(?i)\b(logs?/|outputs?/|failed_datasets|partial|shard|cache \+|merge \+|route_derived|server ready|gpu memory|sock)\b"),
        "Avoid operational logistics; cite stable results, appendix tables, or anonymized artifacts.",
    ),
    Rule(
        "Medium",
        "meta-audience",
        re.compile(r"(?i)\b(ac-facing|reviewer-specific|triage|borderline expert|score increase|increase .*score|dangerous reviewer|persuade the ac)\b"),
        "Rewrite strategic meta-language as neutral reviewer-facing substance.",
    ),
    Rule(
        "Medium",
        "private-finalization",
        re.compile(r"(?i)\b(finalcheck|backup|copy this|right lower corner|page looks empty|stop modifying)\b"),
        "Check whether draft/finalization logistics should be removed or converted to formal revision prose.",
    ),
    Rule(
        "Medium",
        "uncertain-draft-language",
        re.compile(r"(?i)\b(probably|maybe|i think|not sure|should be okay|seems fine|looks fine|good enough)\b"),
        "Replace informal uncertainty with a precise limitation, assumption, or verified claim.",
    ),
    Rule(
        "Low",
        "private-file-name",
        re.compile(r"(?i)\b(submission5\.29|chagpt|scratch|debug|temp|backup|finalcheck)\b"),
        "Check whether this file/directory name reveals private drafting workflow.",
    ),
]


def iter_files(paths: Iterable[Path], exts: set[str]) -> Iterable[Path]:
    for path in paths:
        if path.is_file() and path.suffix.lower() in exts:
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in exts:
                    yield child


def scan_file(path: Path) -> list[tuple[Rule, int, str, str]]:
    findings: list[tuple[Rule, int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"ERROR\t{path}\t{exc}")
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule in RULES:
            match = rule.pattern.search(line)
            if match:
                snippet = line.strip()
                if len(snippet) > 220:
                    snippet = snippet[:217] + "..."
                findings.append((rule, line_no, match.group(0), snippet))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to scan")
    parser.add_argument("--ext", nargs="+", default=[".tex", ".md", ".txt"], help="Extensions to include")
    parser.add_argument("--fail-on", choices=["High", "Medium", "Low"], help="Exit nonzero if severity is found")
    args = parser.parse_args()

    exts = {ext if ext.startswith(".") else f".{ext}" for ext in args.ext}
    severity_order = {"High": 3, "Medium": 2, "Low": 1}
    fail_threshold = severity_order.get(args.fail_on or "", 99)
    worst = 0
    count = 0

    for path in iter_files(args.paths, exts):
        for rule, line_no, matched, snippet in scan_file(path):
            count += 1
            worst = max(worst, severity_order[rule.severity])
            print(
                f"{rule.severity}\t{rule.category}\t{path}:{line_no}\t"
                f"match={matched!r}\t{snippet}\tadvice={rule.advice}"
            )

    if count == 0:
        print("OK\tNo obvious internal-note leakage patterns found.")
    else:
        print(f"SUMMARY\t{count} potential leak(s) found.")

    return 1 if worst >= fail_threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
