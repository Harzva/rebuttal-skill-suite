#!/usr/bin/env python3
"""Validate lightweight rebuttal skill-suite extensions."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
EXTENSIONS = ROOT / "extensions"
REQUIRED_SCALARS = {"name", "version", "description"}
PATH_SECTIONS = {"prompts", "checks", "schemas", "fixtures"}
LIST_SECTIONS = PATH_SECTIONS | {"extension_types", "validation_commands"}
ALLOWED_TYPES = {"prompt", "checker", "schema"}
ALLOWED_SEVERITIES = {"P0", "P1", "P2"}


def parse_manifest(path: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    scalars: dict[str, str] = {}
    lists: dict[str, list[str]] = {}
    current: str | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(" ") or raw.startswith("\t"):
            item = raw.strip()
            if item.startswith("- ") and current:
                lists.setdefault(current, []).append(item[2:].strip().strip("\"'"))
            continue
        current = None
        if raw.endswith(":"):
            key = raw[:-1].strip()
            if key in LIST_SECTIONS:
                current = key
                lists.setdefault(key, [])
            continue
        if ":" in raw:
            key, value = raw.split(":", 1)
            scalars[key.strip()] = value.strip().strip("\"'")
    return scalars, lists


def safe_child(base: Path, rel: str) -> Path:
    candidate = (base / rel).resolve()
    if not candidate.is_relative_to(base.resolve()):
        raise ValueError(f"path escapes extension directory: {rel}")
    return candidate


def run_command(ext_dir: Path, command: str) -> list[str]:
    expect_fail = command.startswith("! ")
    actual = command[2:].strip() if expect_fail else command
    result = subprocess.run(actual, cwd=ext_dir, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if expect_fail and result.returncode == 0:
        return [f"expected command to fail but it passed: {command}"]
    if not expect_fail and result.returncode != 0:
        return [f"command failed: {command}\n{result.stdout.strip()}"]
    return []


def validate_extension(ext_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest = ext_dir / "manifest.yaml"
    if not manifest.exists():
        return ["missing manifest.yaml"]

    scalars, lists = parse_manifest(manifest)
    for field in REQUIRED_SCALARS:
        if not scalars.get(field):
            errors.append(f"missing required field: {field}")

    severity = scalars.get("severity_default_fail_on", "P1")
    if severity not in ALLOWED_SEVERITIES:
        errors.append(f"severity_default_fail_on must be one of P0/P1/P2, got {severity}")

    for ext_type in lists.get("extension_types", []):
        if ext_type not in ALLOWED_TYPES:
            errors.append(f"unknown extension type: {ext_type}")

    if not any(lists.get(section) for section in PATH_SECTIONS):
        errors.append("extension must reference at least one prompt, check, schema, or fixture")

    for section in PATH_SECTIONS:
        for rel in lists.get(section, []):
            try:
                path = safe_child(ext_dir, rel)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if not path.exists():
                errors.append(f"missing referenced {section[:-1]}: {rel}")
            elif path.is_dir():
                errors.append(f"referenced {section[:-1]} is a directory, expected file: {rel}")

    if not errors:
        for command in lists.get("validation_commands", []):
            errors.extend(run_command(ext_dir, command))

    return errors


def main() -> int:
    if not EXTENSIONS.exists():
        print("No extensions directory found; skipping.")
        return 0

    extension_dirs = sorted(path for path in EXTENSIONS.iterdir() if path.is_dir())
    if not extension_dirs:
        print("No extensions found; skipping.")
        return 0

    failed = False
    for ext_dir in extension_dirs:
        errors = validate_extension(ext_dir)
        if errors:
            failed = True
            print(f"EXTENSION_INVALID {ext_dir.relative_to(ROOT)}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"EXTENSION_OK {ext_dir.relative_to(ROOT)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
