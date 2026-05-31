#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

expect_pass() {
  local name="$1"
  shift
  if "$@" >/tmp/rebuttal_suite_${name}.out 2>&1; then
    echo "PASS_EXPECTED $name"
  else
    echo "REGRESSION_UNEXPECTED_FAIL $name" >&2
    cat /tmp/rebuttal_suite_${name}.out >&2 || true
    return 1
  fi
}

expect_fail() {
  local name="$1"
  shift
  if "$@" >/tmp/rebuttal_suite_${name}.out 2>&1; then
    echo "REGRESSION_UNEXPECTED_PASS $name" >&2
    cat /tmp/rebuttal_suite_${name}.out >&2 || true
    return 1
  else
    echo "FAIL_EXPECTED $name"
  fi
}

expect_pass claim_good python3 scripts/check_claim_ledger.py examples/anonymous_rebuttal.tex --ledger schemas/claim_ledger.example.csv --fail-on P0
expect_pass numbers_good python3 scripts/check_reported_numbers.py examples/anonymous_rebuttal.tex --numbers schemas/reported_numbers.example.csv --fail-on P0
expect_pass table_good python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv --fail-on P0
expect_pass issue_map_good python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers FEoB,bCeM,y76H,MekP --fail-on P1
expect_pass issue_map_draft python3 scripts/generate_reviewer_issue_map.py examples/reviewer_comments_sample.md --reviewers R1,R2
expect_pass tone_good python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1
expect_pass cost_good python3 scripts/check_cost_evidence.py examples/cost_evidence_good.md --fail-on P1
expect_pass revision_map_good python3 scripts/check_revision_map.py examples/revision_map_good.tex --fail-on P1 --require-map
expect_pass layout_good python3 scripts/check_layout_readiness.py examples/layout_metrics_good.txt --fail-on P2
expect_pass visual_density_good python3 scripts/check_pdf_visual_density.py examples/visual_density_good.txt --fail-on P2
expect_pass budget_preset python3 scripts/response_budget_presets.py openreview-750w --shell
expect_pass response_good python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers FEoB,bCeM,y76H,MekP --require-reviewers --platform openreview --max-words 220 --max-chars 1500 --fail-on P0
expect_pass promises_good python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1
expect_pass persona_good python3 scripts/check_persona_outputs.py reviewer_roles
expect_pass aggregate_good python3 scripts/aggregate_reviewer_feedback.py examples/persona_feedback
expect_fail leak_bad python3 skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py examples/regression_bad/leaky_rebuttal.tex --fail-on High
expect_fail claim_bad python3 scripts/check_claim_ledger.py examples/regression_bad/bad_claim_rebuttal.tex --ledger schemas/claim_ledger.example.csv --fail-on P0
expect_fail numbers_bad python3 scripts/check_reported_numbers.py examples/regression_bad/bad_numbers_rebuttal.tex --numbers schemas/reported_numbers.example.csv --fail-on P0
expect_fail table_bad python3 scripts/check_result_table.py examples/regression_bad/bad_result_summary.csv --expect schemas/result_table_expectations.example.csv --fail-on P0
expect_fail issue_map_bad python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map examples/regression_bad/bad_reviewer_issue_map.csv --reviewers FEoB,bCeM,y76H,MekP --fail-on P1
expect_fail tone_bad python3 scripts/check_rebuttal_tone.py examples/regression_bad/bad_tone_response.md --fail-on P1
expect_fail cost_bad python3 scripts/check_cost_evidence.py examples/regression_bad/bad_cost_evidence.md --fail-on P1
expect_fail revision_map_bad python3 scripts/check_revision_map.py examples/regression_bad/bad_revision_map.tex --fail-on P1 --require-map
expect_fail layout_bad python3 scripts/check_layout_readiness.py examples/regression_bad/bad_layout_metrics.txt --fail-on P2
expect_fail visual_density_bad python3 scripts/check_pdf_visual_density.py examples/regression_bad/bad_visual_density.txt --fail-on P2
expect_fail response_bad python3 scripts/check_response_text.py examples/regression_bad/bad_platform_response.md --reviewers FEoB,bCeM,y76H,MekP --require-reviewers --platform openreview --max-words 220 --max-chars 1500 --fail-on P0
expect_fail promises_bad python3 scripts/check_revision_promises.py examples/regression_bad/bad_revision_promises.md --fail-on P1
expect_fail persona_bad python3 scripts/check_persona_outputs.py examples/regression_bad/bad_persona_feedback.md

echo "REGRESSION_FIXTURES_OK"
