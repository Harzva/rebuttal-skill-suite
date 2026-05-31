#!/usr/bin/env python3
"""Check rebuttal text against a generic claim ledger.

CSV columns:
  id,pattern,required_near,forbidden_near,severity,must_find,note

`required_near` uses semicolon-separated groups. Each group may contain `|` alternatives;
every group must match near at least one occurrence of `pattern`.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_ORDER = {"P0": 3, "P1": 2, "P2": 1, "INFO": 0}


@dataclass
class Finding:
    severity: str
    claim_id: str
    message: str
    note: str


def normalize_latex(text: str) -> str:
    text = text.replace("\\theta", "theta").replace("θ", "theta").replace("Θ", "theta")
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r" \1 ", text)
    text = re.sub(r"[{}$]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def split_groups(value: str) -> list[list[str]]:
    groups = []
    for group in (value or "").split(";"):
        group = group.strip()
        if not group:
            continue
        groups.append([part.strip() for part in group.split("|") if part.strip()])
    return groups


def any_alt_matches(alts: list[str], text: str) -> bool:
    return any(re.search(alt, text, flags=re.I) for alt in alts)


def check_row(text: str, row: dict[str, str], window: int) -> list[Finding]:
    claim_id = row.get("id", "unnamed") or "unnamed"
    pattern = row.get("pattern", "").strip()
    severity = (row.get("severity", "P1") or "P1").upper()
    note = row.get("note", "").strip()
    must_find = (row.get("must_find", "false") or "false").strip().lower() in {"1", "true", "yes"}
    findings: list[Finding] = []

    if not pattern:
        return findings

    matches = list(re.finditer(pattern, text, flags=re.I))
    if not matches:
        if must_find:
            findings.append(Finding(severity, claim_id, f"pattern not found: {pattern}", note))
        return findings

    required_groups = split_groups(row.get("required_near", ""))
    forbidden_groups = split_groups(row.get("forbidden_near", ""))
    contexts = [text[max(0, m.start() - window) : min(len(text), m.end() + window)] for m in matches]

    for group in required_groups:
        if not any(any_alt_matches(group, ctx) for ctx in contexts):
            findings.append(
                Finding(
                    severity,
                    claim_id,
                    "required nearby term missing: " + " | ".join(group),
                    note,
                )
            )

    for group in forbidden_groups:
        bad_contexts = [ctx for ctx in contexts if any_alt_matches(group, ctx)]
        if bad_contexts:
            findings.append(
                Finding(
                    severity,
                    claim_id,
                    "forbidden nearby term present: " + " | ".join(group),
                    note,
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path, help="Rebuttal .tex/.md/.txt file")
    parser.add_argument("--ledger", type=Path, required=True, help="CSV claim ledger")
    parser.add_argument("--window", type=int, default=220, help="Characters around a matched claim")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2"], default="P0")
    args = parser.parse_args()

    text = normalize_latex(args.text.read_text(encoding="utf-8", errors="replace"))
    findings: list[Finding] = []
    with args.ledger.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            findings.extend(check_row(text, row, args.window))

    threshold = SEVERITY_ORDER[args.fail_on]
    worst = 0
    if findings:
        print("CLAIM_LEDGER_FINDINGS")
        for finding in findings:
            worst = max(worst, SEVERITY_ORDER.get(finding.severity, 0))
            suffix = f" note={finding.note}" if finding.note else ""
            print(f"{finding.severity}\t{finding.claim_id}\t{finding.message}{suffix}")
    else:
        print("CLAIM_LEDGER_OK")

    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
