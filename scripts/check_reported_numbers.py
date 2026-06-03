#!/usr/bin/env python3
"""Check reported numeric claims in rebuttal text against an expected-number ledger.

CSV columns:
  id,pattern,expected,tolerance,severity,must_find,note

`pattern` should contain either a named group `(?P<value>...)` or one capturing group
for the reported number. Patterns are matched against lightly normalized LaTeX text.
"""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_ORDER = {"P0": 3, "P1": 2, "P2": 1, "INFO": 0}
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


@dataclass
class Finding:
    severity: str
    claim_id: str
    message: str
    note: str


def strip_latex_comments(text: str) -> str:
    """Remove LaTeX comments while preserving escaped percent signs."""
    stripped_lines = []
    for line in text.splitlines():
        out = []
        for idx, char in enumerate(line):
            if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
                break
            out.append(char)
        stripped_lines.append("".join(out))
    return "\n".join(stripped_lines)


def normalize_latex(text: str) -> str:
    text = strip_latex_comments(text)
    text = text.replace("\\%", " percent ")
    text = text.replace("\\theta", "theta").replace("θ", "theta").replace("Θ", "theta")
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r" \1 ", text)
    text = re.sub(r"[{}$]", " ", text)
    text = text.replace("=", " = ")
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def extract_value(match: re.Match[str]) -> float | None:
    value = match.groupdict().get("value")
    if value is None and match.groups():
        value = match.group(1)
    if value is None:
        found = NUMBER_RE.search(match.group(0))
        value = found.group(0) if found else None
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def check_row(text: str, row: dict[str, str]) -> list[Finding]:
    claim_id = row.get("id", "unnamed") or "unnamed"
    pattern = (row.get("pattern", "") or "").strip()
    severity = (row.get("severity", "P1") or "P1").upper()
    note = (row.get("note", "") or "").strip()
    must_find = (row.get("must_find", "true") or "true").strip().lower() in {"1", "true", "yes"}
    tolerance = float(row.get("tolerance", "0.005") or "0.005")
    findings: list[Finding] = []

    if not pattern:
        return findings

    expected_raw = (row.get("expected", "") or "").strip()
    try:
        expected = float(expected_raw)
    except ValueError:
        findings.append(Finding(severity, claim_id, f"invalid expected number: {expected_raw}", note))
        return findings

    matches = list(re.finditer(pattern, text, flags=re.I))
    if not matches:
        if must_find:
            findings.append(Finding(severity, claim_id, f"numeric claim not found: {pattern}", note))
        return findings

    values = [extract_value(match) for match in matches]
    values = [value for value in values if value is not None]
    if not values:
        findings.append(Finding(severity, claim_id, "pattern matched but no numeric value could be extracted", note))
        return findings

    if not any(abs(value - expected) <= tolerance for value in values):
        pretty = ", ".join(f"{value:.6g}" for value in values)
        findings.append(
            Finding(
                severity,
                claim_id,
                f"expected {expected:.6g} +/- {tolerance:.6g}, found {pretty}",
                note,
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path, help="Rebuttal .tex/.md/.txt file")
    parser.add_argument("--numbers", type=Path, required=True, help="CSV expected-number ledger")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2"], default="P0")
    args = parser.parse_args()

    text = normalize_latex(args.text.read_text(encoding="utf-8", errors="replace"))
    findings: list[Finding] = []
    with args.numbers.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            findings.extend(check_row(text, row))

    threshold = SEVERITY_ORDER[args.fail_on]
    worst = 0
    if findings:
        print("NUMBER_LEDGER_FINDINGS")
        for finding in findings:
            worst = max(worst, SEVERITY_ORDER.get(finding.severity, 0))
            suffix = f" note={finding.note}" if finding.note else ""
            print(f"{finding.severity}\t{finding.claim_id}\t{finding.message}{suffix}")
    else:
        print("NUMBER_LEDGER_OK")

    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
