#!/usr/bin/env python3
"""Check whether rebuttal cost evidence is scannable and baseline-grounded."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}
COST_CUE_RE = re.compile(r"\b(?:cost|memory|mem\.?|latency|runtime|route\s+ratio|route)\b", re.I)
FIELD_PATTERNS = {
    "memory": re.compile(r"\b(?:memory|mem\.?|vram|gpu\s+memory|footprint)\b", re.I),
    "latency": re.compile(r"\b(?:lat\.?|latency|runtime|run\s*time|time|throughput|sec(?:ond)?s?|ms|s/img)\b", re.I),
    "route": re.compile(r"\b(?:route\s+ratio|route|routed|routing|branch|% VLM|% proposal|100% VLM)\b", re.I),
    "baseline": re.compile(r"\b(?:baseline|vs\.?|versus|relative\s+to|compared\s+(?:with|to))\b", re.I),
}
BASELINE_FAMILIES = {
    "proposal_only": re.compile(r"\b(?:proposal|retrieval|clip)[-\s]?only\b|\b(?:proposal|retrieval|clip)\b", re.I),
    "vlm_only": re.compile(
        r"\b(?:vlm|generator|model)[-\s]?only\b|\b(?!clip|proposal|retrieval|verifier|verification|route|routed|hybrid)[A-Za-z][A-Za-z0-9.-]+-only\b",
        re.I,
    ),
    "verifier_only": re.compile(r"\b(?:verifier|verification)[-\s]?only\b", re.I),
    "routed": re.compile(r"\b(?:routed|routing|hybrid|route[-\s]?dependent)\b", re.I),
}
LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def is_escaped_percent(line: str, idx: int) -> bool:
    slash_count = 0
    cursor = idx - 1
    while cursor >= 0 and line[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def is_numeric_percent(line: str, idx: int) -> bool:
    before = idx - 1
    while before >= 0 and line[before].isspace():
        before -= 1
    after = idx + 1
    while after < len(line) and line[after].isspace():
        after += 1
    return (before >= 0 and line[before].isdigit()) or (after < len(line) and line[after].isdigit())


def strip_latex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        comment_at = None
        for idx, char in enumerate(body):
            if char == "%" and not is_escaped_percent(body, idx) and not is_numeric_percent(body, idx):
                comment_at = idx
                break
        if comment_at is not None:
            body = body[:comment_at]
        lines.append(body + newline)
    return "".join(lines)


def normalize_text(text: str) -> str:
    text = strip_latex_comments(text)
    text = text.replace("&", " ")
    text = text.replace("\\\\", "\n")
    text = LATEX_COMMAND_RE.sub(lambda m: m.group(1) or " ", text)
    return re.sub(r"\s+", " ", text)


def check_cost_evidence(path: Path, require_cost: bool, require_families: bool) -> tuple[list[Finding], dict[str, bool], dict[str, bool], bool]:
    text = normalize_text(path.read_text(encoding="utf-8", errors="replace"))
    has_cost_cue = bool(COST_CUE_RE.search(text))
    fields = {name: bool(pattern.search(text)) for name, pattern in FIELD_PATTERNS.items()}
    families = {name: bool(pattern.search(text)) for name, pattern in BASELINE_FAMILIES.items()}
    findings: list[Finding] = []

    if not has_cost_cue:
        if require_cost:
            findings.append(Finding("P1", "missing-cost-answer", "no cost, memory, latency, runtime, or route-ratio discussion was found"))
        return findings, fields, families, has_cost_cue

    for field in ("memory", "latency", "route"):
        if not fields[field]:
            findings.append(Finding("P1", f"missing-{field}", f"cost evidence should state {field}"))

    if fields["latency"] and not fields["baseline"]:
        findings.append(Finding("P1", "latency-without-baseline", "latency/runtime evidence should say which baseline it is relative to"))

    if require_families:
        missing = [name for name, present in families.items() if not present]
        if missing:
            readable = ", ".join(name.replace("_", "-") for name in missing)
            findings.append(
                Finding(
                    "P1",
                    "missing-cost-baseline-family",
                    "cost comparison should cover proposal-only, VLM-only, verifier-only, and routed/hybrid variants when relevant; missing: "
                    + readable,
                )
            )

    return findings, fields, families, has_cost_cue


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    parser.add_argument("--require-cost", action="store_true", help="Fail when no cost discussion is present")
    parser.add_argument(
        "--no-require-baseline-families",
        action="store_true",
        help="Do not require proposal-only/VLM-only/verifier-only/routed family coverage",
    )
    args = parser.parse_args()

    findings, fields, families, has_cost_cue = check_cost_evidence(
        args.path,
        require_cost=args.require_cost,
        require_families=not args.no_require_baseline_families,
    )
    if findings:
        print(
            "COST_EVIDENCE_FINDINGS "
            f"cost_cue={int(has_cost_cue)} "
            f"fields={','.join(name for name, present in fields.items() if present) or 'none'} "
            f"families={','.join(name for name, present in families.items() if present) or 'none'}"
        )
        for finding in findings:
            print(f"{finding.severity}\t{finding.code}\t{finding.message}")
    elif has_cost_cue:
        print(
            "COST_EVIDENCE_OK "
            f"fields={','.join(name for name, present in fields.items() if present)} "
            f"families={','.join(name for name, present in families.items() if present)}"
        )
    else:
        print("COST_EVIDENCE_SKIPPED no cost cue found")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
