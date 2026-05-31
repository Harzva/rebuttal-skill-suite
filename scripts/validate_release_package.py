#!/usr/bin/env python3
"""Validate the publishable rebuttal-skill-suite package."""

from __future__ import annotations

import argparse
import re
import stat
from pathlib import Path


REQUIRED_PATHS = [
    "README.md",
    "LICENSE",
    "VERSION",
    "CHANGELOG.md",
    "RELEASE_CHECKLIST.md",
    "workflows/adversarial_rebuttal_loop.md",
    "prompts/upgrade_skill_suite.md",
    "skills/rebuttal-audit/SKILL.md",
    "skills/rebuttal-leak-audit/SKILL.md",
    "scripts/install_skills.sh",
    "scripts/build_release_archive.sh",
    "scripts/run_rebuttal_gates.sh",
    "scripts/aggregate_reviewer_feedback.py",
    "scripts/check_claim_ledger.py",
    "scripts/check_reported_numbers.py",
    "scripts/check_result_table.py",
    "scripts/check_reviewer_issue_map.py",
    "scripts/generate_reviewer_issue_map.py",
    "scripts/check_rebuttal_tone.py",
    "scripts/check_cost_evidence.py",
    "scripts/check_revision_map.py",
    "scripts/check_layout_readiness.py",
    "scripts/check_pdf_visual_density.py",
    "scripts/check_response_text.py",
    "scripts/response_budget_presets.py",
    "scripts/check_revision_promises.py",
    "scripts/check_persona_outputs.py",
    "scripts/run_regression_fixtures.sh",
    "scripts/validate_repo_clean.py",
    "scripts/validate_release_package.py",
    "scripts/validate_suite.sh",
    "schemas/claim_ledger.example.csv",
    "schemas/reported_numbers.example.csv",
    "schemas/result_table_expectations.example.csv",
    "schemas/reviewer_issue_map.example.csv",
    "examples/anonymous_rebuttal.tex",
    "examples/result_summary.csv",
    "examples/issue_map_response_good.md",
    "examples/reviewer_comments_sample.md",
    "examples/tone_good.md",
    "examples/cost_evidence_good.md",
    "examples/revision_map_good.tex",
    "examples/layout_metrics_good.txt",
    "examples/visual_density_good.txt",
    "examples/platform_response_good.md",
    "examples/revision_promises_good.md",
]

PUBLIC_EXTS = {".md", ".tex", ".txt", ".csv", ".yaml", ".yml", ".py", ".sh"}
PRIVATE_PATTERNS = [
    re.compile(r"/home/clashuser|/home/[^.\s]+/G2D|G2D/", re.I),
    re.compile(r"ACMMM|mm2026|qwen|Qwen", re.I),
    re.compile(r"老师|导师|改分|开发者备注"),
    re.compile(r"\b(AC-facing|borderline expert|dangerous reviewer|score increase)\b", re.I),
]
PRIVATE_PATTERN_ALLOWLIST = {
    Path("scripts/validate_release_package.py"),
    Path("skills/rebuttal-leak-audit/SKILL.md"),
    Path("skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py"),
}
SCRIPT_REF_RE = re.compile(r"(?:^|[\s`])((?:scripts|skills)/[A-Za-z0-9_./-]+(?:\.py|\.sh))")
SKILL_REF_RE = re.compile(r"(?:^|[\s`])(skills/[A-Za-z0-9_-]+/SKILL\.md)")


def iter_public_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if rel.parts[:2] == ("examples", "regression_bad"):
            continue
        if path.suffix in PUBLIC_EXTS or path.name in {"VERSION", "LICENSE", ".gitignore"}:
            yield path


def is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


def ref_exists(root: Path, source: Path, ref: str) -> bool:
    if (root / ref).exists():
        return True
    rel = source.relative_to(root)
    if len(rel.parts) >= 3 and rel.parts[0] == "skills" and (source.parent / ref).exists():
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    issues: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_PATHS:
        if not (root / rel).exists():
            issues.append(f"missing required path: {rel}")

    for rel in REQUIRED_PATHS:
        path = root / rel
        if path.suffix in {".py", ".sh"} and path.exists() and not is_executable(path):
            issues.append(f"script is not executable: {rel}")

    version = (root / "VERSION").read_text(encoding="utf-8", errors="replace").strip() if (root / "VERSION").exists() else ""
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8", errors="replace") if (root / "CHANGELOG.md").exists() else ""
    if version and f"## {version}" not in changelog:
        issues.append(f"VERSION {version} has no matching CHANGELOG section")

    for path in iter_public_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root)
        if rel not in PRIVATE_PATTERN_ALLOWLIST:
            for pattern in PRIVATE_PATTERNS:
                if pattern.search(text):
                    issues.append(f"private/project-specific pattern in {rel}: {pattern.pattern}")
        for match in SCRIPT_REF_RE.finditer(text):
            ref = match.group(1).rstrip(".,);]")
            if not ref_exists(root, path, ref):
                warnings.append(f"referenced script missing from {rel}: {ref}")
        for match in SKILL_REF_RE.finditer(text):
            ref = match.group(1).rstrip(".,);]")
            if not ref_exists(root, path, ref):
                warnings.append(f"referenced skill file missing from {rel}: {ref}")

    if issues or warnings:
        print("RELEASE_PACKAGE_CHECK_FAILED" if issues else "RELEASE_PACKAGE_CHECK_WARNINGS")
        for issue in issues:
            print(f"ISSUE\t{issue}")
        for warning in warnings:
            print(f"WARNING\t{warning}")
        return 1 if issues else 0

    print("RELEASE_PACKAGE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
