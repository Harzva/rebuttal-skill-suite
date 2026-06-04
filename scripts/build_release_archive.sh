#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT_DIR/VERSION")"
OUT_DIR="${RELEASE_OUT_DIR:-/tmp/rebuttal-skill-suite-release}"
ARCHIVE_NAME="rebuttal-skill-suite-${VERSION}.tar.gz"
ARCHIVE_PATH="$OUT_DIR/$ARCHIVE_NAME"
STAGE_PARENT="$(mktemp -d)"
STAGE_DIR="$STAGE_PARENT/rebuttal-skill-suite-${VERSION}"
EXTRACT_DIR="$(mktemp -d)"
QUICK_VALIDATE="${QUICK_VALIDATE:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

cleanup() {
  rm -rf "$STAGE_PARENT" "$EXTRACT_DIR"
}
trap cleanup EXIT

mkdir -p "$OUT_DIR"
mkdir -p "$STAGE_DIR"

copy_entry() {
  local entry="$1"
  if [[ -e "$ROOT_DIR/$entry" ]]; then
    mkdir -p "$STAGE_DIR/$(dirname "$entry")"
    cp -a "$ROOT_DIR/$entry" "$STAGE_DIR/$entry"
  fi
}

for entry in \
  README.md LICENSE VERSION CHANGELOG.md RELEASE_CHECKLIST.md Makefile .gitignore .gitattributes \
  docs workflows prompts reviewer_roles schemas examples scripts skills extensions webview .github; do
  copy_entry "$entry"
done

find "$STAGE_DIR" -type d \( -name .git -o -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
find "$STAGE_DIR" -type f \( -name '*.pyc' -o -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.pdf' -o -name '*.synctex.gz' -o -name '*.fls' -o -name '*.fdb_latexmk' -o -name '*.toc' -o -name '*.bbl' -o -name '*.blg' \) -delete

tar -C "$STAGE_PARENT" -czf "$ARCHIVE_PATH" "rebuttal-skill-suite-${VERSION}"

tar -C "$EXTRACT_DIR" -xzf "$ARCHIVE_PATH"
EXTRACTED="$EXTRACT_DIR/rebuttal-skill-suite-${VERSION}"

python3 "$EXTRACTED/scripts/validate_release_package.py" "$EXTRACTED"
python3 "$EXTRACTED/scripts/validate_repo_clean.py" "$EXTRACTED"
python3 "$QUICK_VALIDATE" "$EXTRACTED/skills/rebuttal-audit"
python3 "$QUICK_VALIDATE" "$EXTRACTED/skills/rebuttal-leak-audit"
python3 "$QUICK_VALIDATE" "$EXTRACTED/skills/rebuttal-dashboard-data"
python3 "$QUICK_VALIDATE" "$EXTRACTED/skills/rebuttal-promo-image"
(
  cd "$EXTRACTED"
  bash scripts/run_regression_fixtures.sh
  bash scripts/validate_suite.sh
)

echo "RELEASE_ARCHIVE_OK $ARCHIVE_PATH"
