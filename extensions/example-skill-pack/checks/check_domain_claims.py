#!/usr/bin/env python3
"""Example extension checker for broad rebuttal claims without evidence hooks."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}
BROAD_PATTERNS = [
    re.compile(r"\b(generalizes?|universally|always|deployment-ready|production-ready)\b", re.I),
    re.compile(r"\b(no additional cost|free speedup|strictly better)\b", re.I),
]
EVIDENCE_HINTS = ["Table", "Appendix", "ledger", "ablation", "baseline", "limitation", "scope:", "evidence:"]


def should_fail(severity: str, threshold: str) -> bool:
    return SEVERITY_ORDER[severity] <= SEVERITY_ORDER[threshold]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--fail-on", default="P1", choices=sorted(SEVERITY_ORDER))
    args = parser.parse_args()

    text = Path(args.path).read_text(encoding="utf-8")
    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(pattern.search(line) for pattern in BROAD_PATTERNS):
            if not any(hint.lower() in line.lower() for hint in EVIDENCE_HINTS):
                findings.append(("P1", line_no, line.strip()))

    for severity, line_no, line in findings:
        print(f"{severity}: broad domain claim lacks evidence hook at line {line_no}: {line}")

    if any(should_fail(severity, args.fail_on) for severity, _, _ in findings):
        return 1
    print("DOMAIN_CLAIMS_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
