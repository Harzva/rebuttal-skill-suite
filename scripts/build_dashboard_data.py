#!/usr/bin/env python3
"""Build private local dashboard data for the static rebuttal webview.

This script is deliberately conservative. It packages structured inputs and simple
heuristics into dashboard JSON, but it does not pretend to understand a paper as
well as a human or Codex review pass. When inputs are missing, it records access
issues instead of fabricating dashboard state.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / ".local" / "dashboard_data.json"
DEFAULT_WEBVIEW_COPY = ROOT / "webview" / "dashboard_data.local.json"
DEFAULT_HISTORY = ROOT / ".local" / "dashboard_history.jsonl"

SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}
STATUS_RESOLVED = {"resolved", "answered", "pass", "done", "closed"}
STATUS_BLOCKING = {"blocking", "fail", "failed", "p0"}
REVIEWER_RE = re.compile(r"\bR(?:eviewer\s*)?(\d+)\b", re.I)
LOCAL_PATH_RE = re.compile(r"(?:/[^\s:]+){2,}|[A-Za-z]:\\[^\s]+")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def read_text(path: Path | None) -> str:
    if not path:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def safe_count_csv(path: Path | None) -> tuple[int, list[dict[str, str]]]:
    if not path or not path.exists():
        return 0, []
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        rows = list(csv.DictReader(fh))
    return len(rows), rows


def git_value(project_root: Path, args: list[str], fallback: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=project_root, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=2)
    except Exception:
        return fallback
    value = result.stdout.strip()
    return value or fallback


def reviewer_id(value: str) -> str:
    match = REVIEWER_RE.search(value or "")
    if match:
        return f"R{match.group(1)}"
    value = (value or "").strip()
    return value if value.startswith("R") else "R1"


def severity_from_text(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ["leak", "contradict", "wrong", "invalid", "protocol", "label leakage", "private"]):
        return "P0"
    if any(token in lower for token in ["missing", "unclear", "cost", "fair", "baseline", "evidence", "overclaim", "scope"]):
        return "P1"
    return "P2"


def status_from_text(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in STATUS_RESOLVED):
        return "resolved"
    if any(token in lower for token in STATUS_BLOCKING):
        return "blocking"
    if any(token in lower for token in ["watch", "needs", "todo", "open", "missing"]):
        return "watch"
    return "open"


def theme_from_text(text: str) -> str:
    lower = text.lower()
    mapping = [
        ("Safety", ["leak", "private", "path", "tone"]),
        ("Protocol", ["protocol", "label", "threshold", "fixed", "calibrated"]),
        ("Cost", ["cost", "latency", "memory", "runtime"]),
        ("Evidence", ["evidence", "table", "number", "claim", "baseline"]),
        ("Scope", ["scope", "general", "deployment", "overclaim"]),
        ("Coverage", ["reviewer", "coverage", "concern"]),
        ("Layout", ["layout", "page", "density", "orphan"]),
        ("Submission", ["openreview", "cmt", "word", "character"]),
    ]
    for theme, keys in mapping:
        if any(key in lower for key in keys):
            return theme
    return "Evidence"


def summarize(text: str, limit: int = 150) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    clean = LOCAL_PATH_RE.sub("[local path removed]", clean)
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def issue_from_row(idx: int, row: dict[str, str]) -> dict[str, Any]:
    joined = " ".join(str(v) for v in row.values())
    title = row.get("title") or row.get("issue") or row.get("concern") or row.get("claim_text") or f"Reviewer concern {idx}"
    reviewers_raw = row.get("reviewers") or row.get("reviewer") or row.get("reviewer_anchor") or "R1"
    reviewers = sorted({reviewer_id(part) for part in re.split(r"[,;\s]+", reviewers_raw) if part.strip()}) or ["R1"]
    severity = (row.get("severity") or row.get("severity_if_missing") or severity_from_text(joined)).upper()
    if severity not in SEVERITY_ORDER:
        severity = severity_from_text(joined)
    status = status_from_text(row.get("status") or joined)
    evidence_raw = row.get("evidence") or row.get("evidence_anchor") or row.get("where") or row.get("response_anchor") or "needs evidence"
    evidence = [summarize(part, 64) for part in re.split(r"[;|]", evidence_raw) if part.strip()] or ["needs evidence"]
    return {
        "id": row.get("id") or row.get("issue_id") or f"ISS-{idx:03d}",
        "title": summarize(title, 64),
        "theme": row.get("theme") or theme_from_text(joined),
        "reviewers": reviewers,
        "severity": severity,
        "status": status,
        "summary": summarize(row.get("summary") or row.get("response") or row.get("claim_text") or joined, 170),
        "evidence": evidence,
        "risk": summarize(row.get("risk") or "Verify this issue has a bounded reviewer-facing response before submission.", 150),
    }


def issues_from_issue_map(path: Path | None) -> list[dict[str, Any]]:
    _, rows = safe_count_csv(path)
    return [issue_from_row(i, row) for i, row in enumerate(rows, start=1)]


def issues_from_reviews(paths: list[Path], start_idx: int = 1) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in paths:
        text = read_text(path)
        blocks = re.split(r"\n\s*\n", text)
        for block in blocks:
            clean = block.strip()
            if len(clean) < 40:
                continue
            if not any(token in clean.lower() for token in ["weak", "concern", "question", "missing", "unclear", "cost", "baseline", "label", "protocol", "evidence", "limitation"]):
                continue
            reviewers = sorted({f"R{m}" for m in REVIEWER_RE.findall(clean)}) or [reviewer_id(path.stem)]
            severity = severity_from_text(clean)
            issue_id = f"ISS-{start_idx + len(issues):03d}"
            issues.append({
                "id": issue_id,
                "title": summarize(clean.split(".")[0], 58),
                "theme": theme_from_text(clean),
                "reviewers": reviewers,
                "severity": severity,
                "status": "watch" if severity in {"P0", "P1"} else "open",
                "summary": summarize(clean, 170),
                "evidence": ["needs evidence"],
                "risk": "Review extracted concern and attach a concrete rebuttal or evidence anchor.",
            })
    return issues


def reviewer_map(reviewers: list[str], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for rid in reviewers:
        anchors = [issue["id"] for issue in issues if rid in issue.get("reviewers", [])]
        high = [issue for issue in issues if rid in issue.get("reviewers", []) and issue.get("severity") in {"P0", "P1"}]
        resolved = [issue for issue in high if issue.get("status") in STATUS_RESOLVED]
        coverage = 100 if not high and anchors else (round(len(resolved) / len(high) * 100) if high else 0)
        concerns = sorted({issue.get("theme", "Evidence") for issue in issues if rid in issue.get("reviewers", [])})[:5]
        out.append({
            "id": rid,
            "stance": "Needs review coverage verification." if anchors else "No extracted concerns yet.",
            "covered": bool(anchors) and (not high or coverage >= 80),
            "coverage": coverage,
            "concerns": concerns or ["none extracted"],
            "anchors": anchors,
        })
    return out


def evidence_map(args: argparse.Namespace, access_issues: list[str]) -> list[dict[str, Any]]:
    specs = [
        ("Claim ledger", args.claim_ledger),
        ("Number ledger", args.number_ledger),
        ("Result table", args.result_table),
        ("Reviewer issue map", args.reviewer_issue_map),
        ("Revision promises", args.revision_promises),
    ]
    rows = []
    for name, path in specs:
        if path and path.exists():
            count, _ = safe_count_csv(path)
            rows.append({"name": name, "mapped": count, "total": count, "status": "pass" if count else "watch"})
        else:
            access_issues.append(f"Missing optional input for {name}; coverage is unknown.")
            rows.append({"name": name, "mapped": 0, "total": 0, "status": "unknown"})
    return rows


def gate_runs(paths: list[Path]) -> list[dict[str, str]]:
    gates = []
    if not paths:
        return [{"gate": "Dashboard Data", "result": "watch", "detail": "No gate output files were provided."}]
    for path in paths:
        text = read_text(path)
        lower = text.lower()
        if any(token in lower for token in ["failed", "fail", "p0:", "issue\t"]):
            result = "watch"
        elif any(token in lower for token in ["ok", "pass", "suite_validate_ok"]):
            result = "pass"
        else:
            result = "watch"
        gates.append({"gate": summarize(path.stem.replace("_", " ").title(), 40), "result": result, "detail": summarize(text.splitlines()[-1] if text.splitlines() else "No detail", 90)})
    return gates


def summary(issues: list[dict[str, Any]], reviewers: list[dict[str, Any]], evidence: list[dict[str, Any]], gates: list[dict[str, str]]) -> dict[str, Any]:
    resolved = sum(1 for issue in issues if issue.get("status") in STATUS_RESOLVED)
    open_count = max(len(issues) - resolved, 0)
    p0_blocking = sum(1 for issue in issues if issue.get("severity") == "P0" and issue.get("status") not in STATUS_RESOLVED)
    reviewer_coverage = round(sum(r.get("coverage", 0) for r in reviewers) / len(reviewers)) if reviewers else 0
    evidence_total = sum(item.get("total", 0) for item in evidence)
    evidence_mapped = sum(item.get("mapped", 0) for item in evidence)
    gate_total = len(gates)
    gate_passed = sum(1 for gate in gates if gate.get("result") == "pass")
    score = max(0, min(100, 100 - p0_blocking * 18 - sum(1 for i in issues if i.get("severity") == "P1" and i.get("status") not in STATUS_RESOLVED) * 5))
    label = "Good" if score >= 80 else "Watch" if score >= 55 else "Blocking"
    return {
        "issues_total": len(issues),
        "resolved": resolved,
        "open": open_count,
        "p0_blocking": p0_blocking,
        "score": score,
        "score_label": label,
        "reviewer_coverage": reviewer_coverage,
        "reviewers_covered": sum(1 for r in reviewers if r.get("covered")),
        "reviewers_total": len(reviewers),
        "evidence_mapped": evidence_mapped,
        "evidence_total": evidence_total,
        "gate_passed": gate_passed,
        "gate_total": gate_total,
    }


def append_history(path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "date": data["generated_at"],
        "P0": sum(1 for i in data["issues"] if i.get("severity") == "P0" and i.get("status") not in STATUS_RESOLVED),
        "P1": sum(1 for i in data["issues"] if i.get("severity") == "P1" and i.get("status") not in STATUS_RESOLVED),
        "P2": sum(1 for i in data["issues"] if i.get("severity") == "P2" and i.get("status") not in STATUS_RESOLVED),
        "resolved": data["summary"]["resolved"],
    }
    existing = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                existing.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    existing.append(snapshot)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in existing[-30:]) + "\n", encoding="utf-8")
    recent = existing[-7:]
    if len(recent) == 1:
        recent[0]["date"] = "Now"
    return recent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--project-title", default=None)
    parser.add_argument("--paper", type=Path)
    parser.add_argument("--rebuttal", type=Path)
    parser.add_argument("--reviews", type=Path, action="append", default=[])
    parser.add_argument("--reviewer-issue-map", type=Path)
    parser.add_argument("--claim-ledger", type=Path)
    parser.add_argument("--number-ledger", type=Path)
    parser.add_argument("--result-table", type=Path)
    parser.add_argument("--revision-promises", type=Path)
    parser.add_argument("--gate-output", type=Path, action="append", default=[])
    parser.add_argument("--reviewers", default="R1,R2,R3,R4")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--webview-copy", type=Path, default=DEFAULT_WEBVIEW_COPY)
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--no-history", action="store_true")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    access_issues: list[str] = []
    if not args.reviews and not args.reviewer_issue_map:
        access_issues.append("No reviews or reviewer issue map provided; issue extraction is incomplete.")
    if not args.rebuttal:
        access_issues.append("No rebuttal draft provided; response anchors cannot be verified.")

    issues = issues_from_issue_map(args.reviewer_issue_map)
    if args.reviews:
        issues.extend(issues_from_reviews(args.reviews, start_idx=len(issues) + 1))

    reviewer_ids = [r.strip() for r in args.reviewers.split(",") if r.strip()]
    for issue in issues:
        for rid in issue.get("reviewers", []):
            if rid not in reviewer_ids:
                reviewer_ids.append(rid)

    reviewers = reviewer_map(reviewer_ids, issues)
    evidence = evidence_map(args, access_issues)
    gates = gate_runs(args.gate_output)

    data: dict[str, Any] = {
        "title": "Private Rebuttal Dashboard",
        "subtitle": "Local dashboard data generated from project files",
        "generated_at": today(),
        "branch": git_value(project_root, ["branch", "--show-current"], "unknown"),
        "sync_status": git_value(project_root, ["status", "--short"], "local snapshot") or "clean",
        "project": args.project_title or project_root.name,
        "quick_actions": [
            {"label": "Run Gates", "hint": "bash scripts/run_rebuttal_gates.sh <rebuttal.tex> R1,R2,R3,R4"},
            {"label": "Rebuild Data", "hint": "python3 scripts/build_dashboard_data.py --reviews reviews.md --rebuttal rebuttal.tex"},
            {"label": "Sanitize", "hint": "python3 scripts/sanitize_dashboard_data.py .local/dashboard_data.json webview/sample_dashboard_data.json"},
            {"label": "Render README", "hint": "python3 scripts/render_dashboard_views.py"},
        ],
        "issues": issues,
        "reviewers": reviewers,
        "evidence_map": evidence,
        "gate_runs": gates,
        "report_exports": [
            {"format": "JSON", "status": "ready", "description": "Private dashboard snapshot written locally."},
            {"format": "Public sample", "status": "preview", "description": "Run sanitizer before committing public demo data."},
            {"format": "README SVG", "status": "preview", "description": "Regenerate after sanitizing public sample data."},
        ],
        "notes": [
            "Private local dashboard data may include project-specific summaries; do not commit it.",
            "Refresh in the webview reloads the latest JSON but does not execute local scripts.",
        ],
        "access_issues": access_issues,
    }
    data["summary"] = summary(issues, reviewers, evidence, gates)
    data["risk_history"] = [] if args.no_history else append_history(args.history, data)
    if args.no_history:
        data["notes"].append("Risk trend is disabled for this snapshot; no historical data was written.")
    elif len(data["risk_history"]) <= 1:
        data["notes"].append("Risk trend currently has one real snapshot only; rebuild over time to accumulate history.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.webview_copy:
        args.webview_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.out, args.webview_copy)
    print(f"WROTE_PRIVATE_DASHBOARD {args.out}")
    if args.webview_copy:
        print(f"WROTE_WEBVIEW_COPY {args.webview_copy}")
    if access_issues:
        print("ACCESS_ISSUES")
        for issue in access_issues:
            print(f"- {issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
