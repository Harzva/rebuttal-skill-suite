#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUICK_VALIDATE="${QUICK_VALIDATE:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
REAL_REBUTTAL_TEX="${1:-${REBUTTAL_TEX:-}}"
REVIEWERS="${2:-${REBUTTAL_REVIEWERS:-R1,R2,R3,R4}}"
export PYTHONDONTWRITEBYTECODE=1

cd "$ROOT_DIR"
python3 "$QUICK_VALIDATE" skills/rebuttal-audit
python3 "$QUICK_VALIDATE" skills/rebuttal-leak-audit
python3 "$QUICK_VALIDATE" skills/rebuttal-dashboard-data
python3 "$QUICK_VALIDATE" skills/rebuttal-promo-image
TMP_CODEX_HOME="$(mktemp -d)"
TMP_OUT_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_CODEX_HOME" "$TMP_OUT_DIR"' EXIT
bash scripts/install_skills.sh --codex-home "$TMP_CODEX_HOME" >"$TMP_OUT_DIR/install.out"
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-audit"
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-leak-audit"
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-dashboard-data"
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-promo-image"
python3 scripts/check_persona_outputs.py reviewer_roles
python3 scripts/aggregate_reviewer_feedback.py examples/persona_feedback >"$TMP_OUT_DIR/aggregate.md"
python3 scripts/check_claim_ledger.py examples/anonymous_rebuttal.tex --ledger schemas/claim_ledger.example.csv --fail-on P0
python3 scripts/check_reported_numbers.py examples/anonymous_rebuttal.tex --numbers schemas/reported_numbers.example.csv --fail-on P0
python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv --fail-on P0
python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers R1,R2,R3,R4 --fail-on P1
python3 scripts/generate_reviewer_issue_map.py examples/reviewer_comments_sample.md --reviewers R1,R2 >"$TMP_OUT_DIR/issue_map_draft.csv"
python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1
python3 scripts/check_cost_evidence.py examples/cost_evidence_good.md --fail-on P1
python3 scripts/check_revision_map.py examples/revision_map_good.tex --fail-on P1 --require-map
python3 scripts/check_layout_readiness.py examples/layout_metrics_good.txt --fail-on P2
python3 scripts/check_pdf_visual_density.py examples/visual_density_good.txt --fail-on P2
python3 scripts/response_budget_presets.py openreview-750w --shell >"$TMP_OUT_DIR/budget.env"
python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers R1,R2,R3,R4 --require-reviewers --platform openreview --max-words 220 --max-chars 1500 --fail-on P0
python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1
python3 scripts/render_dashboard_views.py >"$TMP_OUT_DIR/dashboard_views.out"
python3 scripts/validate_extensions.py
bash scripts/run_regression_fixtures.sh
python3 scripts/validate_release_package.py .
python3 scripts/validate_repo_clean.py .

if [[ -n "$REAL_REBUTTAL_TEX" ]]; then
  bash scripts/run_rebuttal_gates.sh "$REAL_REBUTTAL_TEX" "$REVIEWERS"
fi

echo "SUITE_VALIDATE_OK"
