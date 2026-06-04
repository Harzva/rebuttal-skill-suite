#!/usr/bin/env python3
"""Build local skill-suite registry data for the static dashboard."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / ".local" / "skill_registry_data.json"
DEFAULT_WEBVIEW_COPY = ROOT / "webview" / "skill_registry.local.json"
DEFAULT_SAMPLE = ROOT / "webview" / "skill_registry.sample.json"

IGNORE_NAMES = {"__pycache__", ".DS_Store"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_version() -> str:
    path = ROOT / "VERSION"
    return path.read_text(encoding="utf-8", errors="replace").strip() if path.exists() else "unknown"


def parse_skill(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {"name": path.parent.name, "description": ""}
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    if key in {"name", "description"}:
                        meta[key] = value
    return meta


def dir_hash(path: Path) -> str:
    digest = hashlib.sha256()
    if not path.exists():
        return ""
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = item.relative_to(path)
        if any(part in IGNORE_NAMES for part in rel.parts) or item.suffix in IGNORE_SUFFIXES:
            continue
        digest.update(str(rel).encode("utf-8"))
        digest.update(b"\0")
        digest.update(item.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def display_codex_home(path: Path) -> str:
    home = Path.home()
    try:
        return "~" + str(path.resolve()).removeprefix(str(home.resolve()))
    except Exception:
        return "~/.codex"


def installed_status(src: Path, dst: Path) -> str:
    if not dst.exists():
        return "missing"
    return "synced" if dir_hash(src) == dir_hash(dst) else "drift"


def parse_manifest(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"name": path.parent.name, "version": "unknown", "description": "", "extension_types": []}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(" ") and current == "extension_types":
            item = raw.strip()
            if item.startswith("- "):
                data["extension_types"].append(item[2:].strip().strip('"'))
            continue
        current = None
        if raw.endswith(":"):
            current = raw[:-1].strip()
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            if key in {"name", "version", "description"}:
                data[key] = value
    return data


def extension_status(ext_dir: Path) -> str:
    manifest = ext_dir / "manifest.yaml"
    if not manifest.exists():
        return "invalid"
    text = manifest.read_text(encoding="utf-8", errors="replace")
    refs = re.findall(r"^\s*-\s+([^'\"!][^\n]+)$", text, flags=re.M)
    missing = []
    for ref in refs:
        ref = ref.strip().strip('"')
        if ref.startswith("python3 ") or ref.startswith("bash ") or ref.startswith("! "):
            continue
        if "/" in ref and not (ext_dir / ref).exists():
            missing.append(ref)
    return "invalid" if missing else "present"


def build(codex_home: Path, include_sample_note: bool = False) -> dict[str, Any]:
    skills = []
    target_root = codex_home / "skills"
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        meta = parse_skill(skill_file)
        dst = target_root / skill_dir.name
        status = installed_status(skill_dir, dst)
        skills.append({
            "name": meta["name"],
            "directory": skill_dir.name,
            "description": meta["description"],
            "repo_status": "available",
            "install_status": status,
            "installed_display": f"{display_codex_home(target_root)}/{skill_dir.name}",
            "commands": [
                "bash scripts/install_skills.sh",
                "bash scripts/install_skills.sh --check",
            ],
        })

    extensions = []
    ext_root = ROOT / "extensions"
    if ext_root.exists():
        for ext_dir in sorted(p for p in ext_root.iterdir() if p.is_dir()):
            manifest = ext_dir / "manifest.yaml"
            meta = parse_manifest(manifest) if manifest.exists() else {"name": ext_dir.name, "version": "unknown", "description": "missing manifest", "extension_types": []}
            extensions.append({
                "name": meta["name"],
                "directory": ext_dir.name,
                "version": meta["version"],
                "description": meta["description"],
                "extension_types": meta.get("extension_types", []),
                "status": extension_status(ext_dir),
                "commands": ["python3 scripts/validate_extensions.py"],
            })

    counts = {
        "skills_total": len(skills),
        "skills_synced": sum(1 for s in skills if s["install_status"] == "synced"),
        "skills_missing": sum(1 for s in skills if s["install_status"] == "missing"),
        "skills_drift": sum(1 for s in skills if s["install_status"] == "drift"),
        "extensions_total": len(extensions),
        "extensions_present": sum(1 for e in extensions if e["status"] == "present"),
    }
    notes = [
        "Skill registry data describes suite capabilities and local installation status; it does not include paper, review, or rebuttal content.",
        "Installed paths are displayed with a home-relative prefix to avoid exposing full local paths.",
        "Static dashboard buttons show safe commands; use the local server with explicit actions for executable controls.",
    ]
    if include_sample_note:
        notes.append("This is public sample registry data; local install status may differ on your machine.")
    return {
        "title": "Rebuttal Skill Suite Control Center",
        "generated_at": now(),
        "repo_version": read_version(),
        "codex_home_display": display_codex_home(codex_home),
        "counts": counts,
        "skills": skills,
        "extensions": extensions,
        "commands": [
            {"label": "Install skills", "command": "bash scripts/install_skills.sh", "kind": "mutating"},
            {"label": "Check installed skills", "command": "bash scripts/install_skills.sh --check", "kind": "read-only"},
            {"label": "Validate extensions", "command": "python3 scripts/validate_extensions.py", "kind": "read-only"},
            {"label": "Validate suite", "command": "bash scripts/validate_suite.sh", "kind": "long-running"},
            {"label": "Build project dashboard data", "command": "python3 scripts/build_dashboard_data.py --reviews reviews.md --rebuttal rebuttal.tex", "kind": "private-data"},
        ],
        "server_preview": {
            "script": "python3 scripts/serve_dashboard.py",
            "safe_default": "Serves static dashboard and read-only registry refresh endpoints on 127.0.0.1.",
            "actions_flag": "Use --enable-actions to allow controlled POST endpoints for install/check/validate commands.",
        },
        "notes": notes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--webview-copy", type=Path, default=DEFAULT_WEBVIEW_COPY)
    parser.add_argument("--sample", action="store_true", help="Also write webview/skill_registry.sample.json with public sample status.")
    args = parser.parse_args()

    data = build(args.codex_home)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.webview_copy:
        args.webview_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.out, args.webview_copy)
    print(f"WROTE_SKILL_REGISTRY {args.out}")
    if args.webview_copy:
        print(f"WROTE_WEBVIEW_SKILL_REGISTRY {args.webview_copy}")
    if args.sample:
        sample = build(args.codex_home, include_sample_note=True)
        public_descriptions = {
            "rebuttal-audit": "Audit one-page academic rebuttals for reviewer coverage, evidence support, layout readiness, and final submission clarity.",
            "rebuttal-leak-audit": "Check public-facing rebuttal drafts for accidental private-process exposure and reviewer-facing wording risks.",
            "rebuttal-dashboard-data": "Build private and sanitized dashboard data from rebuttal projects, ledgers, gates, and reviewer issue maps.",
        }
        for skill in sample["skills"]:
            skill["install_status"] = "sample"
            skill["installed_display"] = "~/.codex/skills/<skill>"
            skill["description"] = public_descriptions.get(skill["name"], "Public-safe skill summary for the Rebuttal Skill Suite.")
        sample["counts"]["skills_synced"] = 0
        sample["counts"]["skills_missing"] = 0
        sample["counts"]["skills_drift"] = 0
        DEFAULT_SAMPLE.write_text(json.dumps(sample, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"WROTE_SAMPLE_SKILL_REGISTRY {DEFAULT_SAMPLE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
