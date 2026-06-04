#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
MODE="install"

usage() {
  cat <<'USAGE'
Usage: scripts/install_skills.sh [--codex-home PATH] [--dry-run|--check]

Install or compare the suite skills under CODEX_HOME/skills.

Options:
  --codex-home PATH   Target Codex home. Defaults to $CODEX_HOME or ~/.codex.
  --dry-run           Print planned copy operations without changing files.
  --check             Compare installed skills with repo copies and exit nonzero on drift.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home)
      CODEX_HOME_DIR="$2"
      shift 2
      ;;
    --dry-run)
      MODE="dry-run"
      shift
      ;;
    --check)
      MODE="check"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

SKILLS=(rebuttal-audit rebuttal-leak-audit rebuttal-dashboard-data)
TARGET_ROOT="$CODEX_HOME_DIR/skills"

for skill in "${SKILLS[@]}"; do
  src="$ROOT_DIR/skills/$skill"
  dst="$TARGET_ROOT/$skill"
  if [[ ! -f "$src/SKILL.md" ]]; then
    echo "Missing source skill: $src" >&2
    exit 1
  fi

  if [[ "$MODE" == "dry-run" ]]; then
    echo "DRY_RUN copy $src -> $dst"
  elif [[ "$MODE" == "check" ]]; then
    if [[ ! -d "$dst" ]]; then
      echo "SYNC_MISSING $dst" >&2
      exit 1
    fi
    diff -qr "$src" "$dst"
    echo "SYNC_OK $skill"
  else
    mkdir -p "$TARGET_ROOT"
    rm -rf "$dst"
    cp -a "$src" "$dst"
    echo "INSTALLED $skill -> $dst"
  fi
done
