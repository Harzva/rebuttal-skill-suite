#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUICK_VALIDATE="${QUICK_VALIDATE:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
REAL_REBUTTAL_TEX="${1:-${REBUTTAL_TEX:-}}"
REVIEWERS="${2:-${REBUTTAL_REVIEWERS:-FEoB,bCeM,y76H,MekP}}"

cd "$ROOT_DIR"
python3 "$QUICK_VALIDATE" skills/rebuttal-audit
python3 "$QUICK_VALIDATE" skills/rebuttal-leak-audit
TMP_CODEX_HOME="$(mktemp -d)"
trap 'rm -rf "$TMP_CODEX_HOME"' EXIT
bash scripts/install_skills.sh --codex-home "$TMP_CODEX_HOME" >/tmp/rebuttal_suite_install.out
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-audit"
python3 "$QUICK_VALIDATE" "$TMP_CODEX_HOME/skills/rebuttal-leak-audit"
python3 scripts/check_persona_outputs.py reviewer_roles
python3 scripts/aggregate_reviewer_feedback.py examples/persona_feedback >/tmp/rebuttal_suite_aggregate.md
python3 scripts/check_claim_ledger.py examples/anonymous_rebuttal.tex --ledger schemas/claim_ledger.example.csv --fail-on P0
python3 scripts/check_reported_numbers.py examples/anonymous_rebuttal.tex --numbers schemas/reported_numbers.example.csv --fail-on P0
python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv --fail-on P0
python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers FEoB,bCeM,y76H,MekP --fail-on P1
python3 scripts/generate_reviewer_issue_map.py examples/reviewer_comments_sample.md --reviewers R1,R2 >/tmp/rebuttal_suite_issue_map_draft.csv
python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1
python3 scripts/check_cost_evidence.py examples/cost_evidence_good.md --fail-on P1
python3 scripts/check_revision_map.py examples/revision_map_good.tex --fail-on P1 --require-map
python3 scripts/check_layout_readiness.py examples/layout_metrics_good.txt --fail-on P2
python3 scripts/check_pdf_visual_density.py examples/visual_density_good.txt --fail-on P2
python3 scripts/response_budget_presets.py openreview-750w --shell >/tmp/rebuttal_suite_budget.env
python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers FEoB,bCeM,y76H,MekP --require-reviewers --platform openreview --max-words 220 --max-chars 1500 --fail-on P0
python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1
bash scripts/run_regression_fixtures.sh
python3 scripts/validate_release_package.py .
python3 scripts/validate_repo_clean.py .

if [[ -n "$REAL_REBUTTAL_TEX" ]]; then
  bash scripts/run_rebuttal_gates.sh "$REAL_REBUTTAL_TEX" "$REVIEWERS"
fi

echo "SUITE_VALIDATE_OK"
