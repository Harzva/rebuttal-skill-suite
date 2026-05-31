#!/usr/bin/env python3
"""Check structured result CSV/TSV tables against expected values.

Expectation CSV columns:
  id,row_key,row,column,expected,tolerance,severity,must_find,note

The result table may be CSV or TSV. `row_key` defaults to `row` if omitted.
Row and column names are matched case-insensitively after trimming whitespace.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


SEVERITY_ORDER = {"P0": 3, "P1": 2, "P2": 1, "INFO": 0}


@dataclass
class Finding:
    severity: str
    item_id: str
    message: str
    note: str


def norm(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def sniff_dialect(path: Path) -> csv.Dialect:
    sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t")
    except csv.Error:
        class Default(csv.excel):
            delimiter = "\t" if "\t" in sample and sample.count("\t") > sample.count(",") else ","
        return Default


def read_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    dialect = sniff_dialect(path)
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, dialect=dialect)
        rows = [{key: value for key, value in row.items()} for row in reader]
        fieldnames = reader.fieldnames or []
    return fieldnames, rows


def get_ci(row: dict[str, str], key: str) -> str | None:
    wanted = norm(key)
    for existing, value in row.items():
        if norm(existing) == wanted:
            return value
    return None


def find_rows(rows: list[dict[str, str]], row_key: str, row_value: str) -> list[dict[str, str]]:
    wanted = norm(row_value)
    found = []
    for row in rows:
        value = get_ci(row, row_key)
        if value is not None and norm(value) == wanted:
            found.append(row)
    return found


def check_expectation(rows: list[dict[str, str]], exp: dict[str, str]) -> list[Finding]:
    item_id = exp.get("id", "unnamed") or "unnamed"
    row_key = exp.get("row_key", "row") or "row"
    row_value = exp.get("row", "") or ""
    column = exp.get("column", "") or ""
    severity = (exp.get("severity", "P1") or "P1").upper()
    note = (exp.get("note", "") or "").strip()
    must_find = (exp.get("must_find", "true") or "true").strip().lower() in {"1", "true", "yes"}
    tolerance = float(exp.get("tolerance", "0.005") or "0.005")
    findings: list[Finding] = []

    if not row_value or not column:
        findings.append(Finding(severity, item_id, "expectation missing row or column", note))
        return findings

    expected_raw = (exp.get("expected", "") or "").strip()
    try:
        expected = float(expected_raw)
    except ValueError:
        findings.append(Finding(severity, item_id, f"invalid expected number: {expected_raw}", note))
        return findings

    matches = find_rows(rows, row_key, row_value)
    if not matches:
        if must_find:
            findings.append(Finding(severity, item_id, f"row not found: {row_key}={row_value}", note))
        return findings

    values: list[float] = []
    for row in matches:
        raw = get_ci(row, column)
        if raw is None:
            continue
        try:
            values.append(float(str(raw).strip().replace("%", "")))
        except ValueError:
            findings.append(Finding(severity, item_id, f"non-numeric value in {column}: {raw}", note))

    if not values:
        findings.append(Finding(severity, item_id, f"column not found or no numeric values: {column}", note))
        return findings

    if not any(abs(value - expected) <= tolerance for value in values):
        pretty = ", ".join(f"{value:.6g}" for value in values)
        findings.append(
            Finding(
                severity,
                item_id,
                f"expected {expected:.6g} +/- {tolerance:.6g} at {row_value}.{column}, found {pretty}",
                note,
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path, help="Result CSV/TSV table")
    parser.add_argument("--expect", type=Path, required=True, help="Expectation CSV")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2"], default="P0")
    args = parser.parse_args()

    _, rows = read_table(args.table)
    findings: list[Finding] = []
    with args.expect.open(newline="", encoding="utf-8") as fh:
        for exp in csv.DictReader(fh):
            findings.extend(check_expectation(rows, exp))

    threshold = SEVERITY_ORDER[args.fail_on]
    worst = 0
    if findings:
        print("RESULT_TABLE_FINDINGS")
        for finding in findings:
            worst = max(worst, SEVERITY_ORDER.get(finding.severity, 0))
            suffix = f" note={finding.note}" if finding.note else ""
            print(f"{finding.severity}\t{finding.item_id}\t{finding.message}{suffix}")
    else:
        print("RESULT_TABLE_OK")

    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    raise SystemExit(main())
