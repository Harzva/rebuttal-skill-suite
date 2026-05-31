#!/usr/bin/env python3
"""Check that reviewer issues map to concrete rebuttal response anchors."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}
REQUIRED_COLUMNS = {"reviewer", "issue_id", "concern", "response_anchor", "status"}
ALLOWED_STATUSES = {
    "answered",
    "bounded",
    "merged",
    "nonfix",
    "revision-promised",
    "deferred",
}
BAD_STATUSES = {"todo", "tbd", "unanswered", "missing", "open"}
NEEDS_RATIONALE = {"nonfix", "deferred"}
NEEDS_EVIDENCE = {"answered", "bounded", "revision-promised"}
LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?")


@dataclass
class Finding:
    severity: str
    code: str
    row: int
    message: str


def normalize(text: str) -> str:
    text = re.sub(r"%.*", "", text)
    text = LATEX_COMMAND_RE.sub(lambda m: m.group(1) or " ", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9.+/%-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_reviewers(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def split_anchors(raw: str) -> list[str]:
    return [item.strip() for item in re.split(r"[;|]", raw or "") if item.strip()]


def load_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    return rows, fields


def check_issue_map(
    response_path: Path,
    map_path: Path,
    reviewers: list[str],
) -> tuple[list[Finding], int, int]:
    response = normalize(response_path.read_text(encoding="utf-8", errors="replace"))
    rows, fields = load_rows(map_path)
    findings: list[Finding] = []
    field_set = set(fields)

    missing_columns = sorted(REQUIRED_COLUMNS - field_set)
    if missing_columns:
        findings.append(
            Finding(
                "P0",
                "missing-columns",
                1,
                "issue map missing required columns: " + ",".join(missing_columns),
            )
        )
        return findings, len(rows), 0

    if not rows:
        findings.append(Finding("P0", "empty-map", 1, "issue map contains no reviewer issues"))
        return findings, 0, 0

    reviewers_seen = {row["reviewer"] for row in rows if row.get("reviewer")}
    for reviewer in reviewers:
        if reviewer not in reviewers_seen:
            findings.append(
                Finding("P0", "missing-reviewer", 1, f"no issue-map rows for reviewer {reviewer}")
            )

    seen_issue_ids: set[tuple[str, str]] = set()
    covered = 0
    for index, row in enumerate(rows, start=2):
        reviewer = row.get("reviewer", "")
        issue_id = row.get("issue_id", "")
        concern = row.get("concern", "")
        anchor = row.get("response_anchor", "")
        status = row.get("status", "").lower()
        evidence = row.get("evidence_pointer", "")
        rationale = row.get("rationale", "")

        for column, value in [
            ("reviewer", reviewer),
            ("issue_id", issue_id),
            ("concern", concern),
            ("response_anchor", anchor),
            ("status", status),
        ]:
            if not value:
                findings.append(
                    Finding("P0", "empty-required-field", index, f"missing {column}")
                )

        issue_key = (reviewer, issue_id)
        if reviewer and issue_id and issue_key in seen_issue_ids:
            findings.append(
                Finding(
                    "P1",
                    "duplicate-issue-id",
                    index,
                    f"duplicate issue_id {issue_id} for reviewer {reviewer}",
                )
            )
        seen_issue_ids.add(issue_key)

        if status in BAD_STATUSES:
            findings.append(
                Finding(
                    "P0",
                    "unresolved-status",
                    index,
                    f"status {status} is not submission-ready for {reviewer}/{issue_id}",
                )
            )
        elif status and status not in ALLOWED_STATUSES:
            findings.append(
                Finding(
                    "P1",
                    "unknown-status",
                    index,
                    f"status {status} is not one of {','.join(sorted(ALLOWED_STATUSES))}",
                )
            )

        if status in NEEDS_RATIONALE and not rationale:
            findings.append(
                Finding(
                    "P1",
                    "missing-nonfix-rationale",
                    index,
                    f"{status} issue lacks rationale for {reviewer}/{issue_id}",
                )
            )

        if status in NEEDS_EVIDENCE and not evidence:
            findings.append(
                Finding(
                    "P1",
                    "missing-evidence-pointer",
                    index,
                    f"{status} issue lacks evidence_pointer for {reviewer}/{issue_id}",
                )
            )

        anchors = split_anchors(anchor)
        if anchors:
            if any(normalize(item) in response for item in anchors):
                covered += 1
            else:
                findings.append(
                    Finding(
                        "P1",
                        "anchor-not-found",
                        index,
                        f"response_anchor not found in response for {reviewer}/{issue_id}: {anchor}",
                    )
                )

    return findings, len(rows), covered


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path)
    parser.add_argument("--map", required=True, type=Path, help="CSV issue map.")
    parser.add_argument("--reviewers", default="", help="Comma-separated reviewer IDs expected in map.")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    args = parser.parse_args()

    findings, rows, covered = check_issue_map(
        args.response,
        args.map,
        parse_reviewers(args.reviewers),
    )

    if findings:
        print(f"ISSUE_MAP_FINDINGS rows={rows} anchored={covered}")
        for finding in findings:
            print(
                f"{finding.severity}\t{finding.code}\trow {finding.row}\t{finding.message}"
            )
    else:
        print(f"ISSUE_MAP_OK rows={rows} anchored={covered}")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
