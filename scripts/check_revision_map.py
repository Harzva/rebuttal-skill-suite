#!/usr/bin/env python3
"""Check compact revision/protocol maps for role and label-use consistency."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}
LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?")
TABULAR_ENV_RE = re.compile(
    r"\\begin\{tabular\}(?:\[[^\]]*\])?\{[^\n]*\}(.*?)\\end\{tabular\}",
    re.S,
)
TABLE_RULE_RE = re.compile(
    r"\\(?:toprule|midrule|bottomrule|hline|cline|cmidrule)(?:\{[^{}]*\})?",
    re.I,
)


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


def strip_latex_comments(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        comment_at = None
        for idx, char in enumerate(body):
            if char == "%" and not is_escaped_percent(body, idx):
                comment_at = idx
                break
        if comment_at is not None:
            body = body[:comment_at]
        lines.append(body + newline)
    return "".join(lines)


def clean_cell(cell: str) -> str:
    cell = TABLE_RULE_RE.sub(" ", cell)
    cell = LATEX_COMMAND_RE.sub(lambda m: m.group(1) or " ", cell)
    cell = re.sub(r"[$_*`{}]", " ", cell)
    return re.sub(r"\s+", " ", cell).strip()


def split_latex_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for raw_row in re.split(r"\\\\(?:\s*\[[^\]]*\])?", body):
        raw_row = TABLE_RULE_RE.sub(" ", raw_row).strip()
        if not raw_row:
            continue
        cells = [clean_cell(cell) for cell in raw_row.split("&")]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append(cells)
    return rows


def split_markdown_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        if re.fullmatch(r"\|[\s:|.-]+\|", stripped):
            continue
        cells = [clean_cell(cell) for cell in stripped.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def iter_candidate_tables(text: str) -> list[list[list[str]]]:
    text = strip_latex_comments(text)
    tables: list[list[list[str]]] = []
    for match in TABULAR_ENV_RE.finditer(text):
        rows = split_latex_rows(match.group(1))
        if rows:
            tables.append(rows)
    markdown_rows = split_markdown_rows(text)
    if markdown_rows:
        tables.append(markdown_rows)
    return tables


def normalize_header(cell: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", cell.lower()).strip("_")


def header_index(header: list[str]) -> dict[str, int]:
    aliases = {
        "role": {"role", "claim_role", "map_role"},
        "row": {"row", "variant", "method", "claim", "entry"},
        "label_use": {"label_use", "label", "labels", "label_status", "label_usage"},
        "avg": {"avg", "average", "mean", "accuracy", "acc"},
        "where": {"where", "evidence", "pointer", "artifact", "location"},
    }
    normalized = [normalize_header(cell) for cell in header]
    result: dict[str, int] = {}
    for key, names in aliases.items():
        for idx, value in enumerate(normalized):
            if value in names or any(name in value for name in names):
                result[key] = idx
                break
    return result


def is_revision_map(header: list[str], rows: list[list[str]], full_text: str) -> bool:
    index = header_index(header)
    header_text = " ".join(header).lower()
    cue_text = full_text.lower()
    return (
        ("revision map" in cue_text or "protocol map" in cue_text or "label use" in header_text)
        and "role" in index
        and ("label_use" in index or "where" in index or "avg" in index)
    ) or ("label use" in header_text and "role" in header_text)


def get_cell(row: list[str], index: dict[str, int], key: str) -> str:
    idx = index.get(key)
    if idx is None or idx >= len(row):
        return ""
    return row[idx]


def check_row(row: list[str], index: dict[str, int], row_number: int) -> list[Finding]:
    role = get_cell(row, index, "role").lower()
    label = get_cell(row, index, "label_use").lower()
    avg = get_cell(row, index, "avg")
    findings: list[Finding] = []

    if "label_use" in index and not label:
        findings.append(Finding("P1", "missing-label-use", f"revision-map row {row_number} lacks a label-use value"))

    if re.search(r"\b(main|strict|deployable)\b", role):
        if label and not re.search(r"\b(none|no labels?|label[-\s]?free|preset|shared global)\b", label):
            findings.append(
                Finding(
                    "P1",
                    "main-claim-label-use-ambiguous",
                    f"main/deployable row {row_number} should use none/no-label/preset/shared-global label-use wording, not: {label}",
                )
            )

    if re.search(r"\b(diagnostic|fixed|pair|audit)\b", role):
        if label and not re.search(r"\b(shared pair|fixed pair|shared|global)\b", label):
            findings.append(
                Finding(
                    "P1",
                    "diagnostic-label-use-ambiguous",
                    f"diagnostic/fixed-pair row {row_number} should state shared/fixed-pair label use, not: {label}",
                )
            )

    if re.search(r"\b(calibrated|selected|tuned|validation)\b", role):
        if not label or re.search(r"\b(none|label[-\s]?free|no labels?)\b", label):
            findings.append(
                Finding(
                    "P1",
                    "calibrated-label-use-ambiguous",
                    f"calibrated/tuned row {row_number} should not look label-free; label-use value is: {label or 'missing'}",
                )
            )

    if "avg" in index and avg and not re.search(r"\d|n/?a|--|not applicable", avg, re.I):
        findings.append(Finding("P2", "avg-without-value", f"revision-map row {row_number} has a nonnumeric Avg cell: {avg}"))

    return findings


def check_revision_map(path: Path, require_map: bool) -> tuple[list[Finding], int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    checked_rows = 0
    matched_map = False

    for table in iter_candidate_tables(text):
        if not table:
            continue
        header = None
        data_rows: list[list[str]] = []
        for idx, candidate in enumerate(table):
            candidate_index = header_index(candidate)
            if "role" in candidate_index and ("label_use" in candidate_index or "avg" in candidate_index or "where" in candidate_index):
                header = candidate
                data_rows = table[idx + 1 :]
                break
        if header is None:
            continue
        if not is_revision_map(header, data_rows, text):
            continue
        matched_map = True
        index = header_index(header)
        required = ["role", "label_use"]
        for key in required:
            if key not in index:
                findings.append(Finding("P1", "missing-revision-map-column", f"revision map missing required column: {key}"))
        if any(key not in index for key in required):
            continue
        for row_number, row in enumerate(data_rows, start=2):
            if len(row) < 2:
                continue
            checked_rows += 1
            findings.extend(check_row(row, index, row_number))

    if require_map and not matched_map:
        findings.append(Finding("P1", "missing-revision-map", "no revision/protocol map table was found"))

    return findings, checked_rows


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    parser.add_argument("--require-map", action="store_true")
    args = parser.parse_args()

    findings, checked_rows = check_revision_map(args.path, require_map=args.require_map)
    if findings:
        print(f"REVISION_MAP_FINDINGS rows={checked_rows}")
        for finding in findings:
            print(f"{finding.severity}\t{finding.code}\t{finding.message}")
    elif checked_rows:
        print(f"REVISION_MAP_OK rows={checked_rows}")
    else:
        print("REVISION_MAP_SKIPPED no revision/protocol map found")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
