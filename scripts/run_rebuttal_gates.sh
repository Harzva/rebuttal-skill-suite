#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/rebuttal.tex [reviewer_ids_csv]" >&2
  exit 2
fi

TEX_PATH="$1"
REVIEWERS="${2:-FEoB,bCeM,y76H,MekP}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEX_DIR="$(cd "$(dirname "$TEX_PATH")" && pwd)"
TEX_FILE="$(basename "$TEX_PATH")"
BASE_NAME="${TEX_FILE%.tex}"
PDF_PATH="$TEX_DIR/$BASE_NAME.pdf"
LOG_PATH="$TEX_DIR/$BASE_NAME.log"
LEAK_FAIL_ON="${REBUTTAL_LEAK_FAIL_ON:-High}"
MIN_TAIL_WORDS="${REBUTTAL_MIN_TAIL_WORDS:-7}"
MIN_TAIL_FILL="${REBUTTAL_MIN_TAIL_FILL:-0.80}"
CLAIM_LEDGER="${REBUTTAL_CLAIM_LEDGER:-}"
CLAIM_FAIL_ON="${REBUTTAL_CLAIM_FAIL_ON:-P0}"
NUMBER_LEDGER="${REBUTTAL_NUMBER_LEDGER:-}"
NUMBER_FAIL_ON="${REBUTTAL_NUMBER_FAIL_ON:-P0}"
RESULT_TABLE="${REBUTTAL_RESULT_TABLE:-}"
RESULT_EXPECTATIONS="${REBUTTAL_RESULT_EXPECTATIONS:-}"
RESULT_FAIL_ON="${REBUTTAL_RESULT_FAIL_ON:-P0}"
ISSUE_MAP="${REBUTTAL_ISSUE_MAP:-}"
ISSUE_MAP_REVIEWERS="${REBUTTAL_ISSUE_MAP_REVIEWERS:-$REVIEWERS}"
ISSUE_MAP_FAIL_ON="${REBUTTAL_ISSUE_MAP_FAIL_ON:-P1}"
TONE_CHECK="${REBUTTAL_TONE_CHECK:-1}"
TONE_FAIL_ON="${REBUTTAL_TONE_FAIL_ON:-P0}"
RESPONSE_TEXT="${REBUTTAL_RESPONSE_TEXT:-}"
RESPONSE_REVIEWERS="${REBUTTAL_RESPONSE_REVIEWERS:-$REVIEWERS}"
RESPONSE_MAX_WORDS="${REBUTTAL_RESPONSE_MAX_WORDS:-}"
RESPONSE_MAX_CHARS="${REBUTTAL_RESPONSE_MAX_CHARS:-}"
RESPONSE_PLATFORM="${REBUTTAL_RESPONSE_PLATFORM:-plain}"
RESPONSE_FAIL_ON="${REBUTTAL_RESPONSE_FAIL_ON:-P0}"
RESPONSE_REQUIRE_REVIEWERS="${REBUTTAL_RESPONSE_REQUIRE_REVIEWERS:-1}"
PROMISE_CHECK="${REBUTTAL_PROMISE_CHECK:-1}"
PROMISE_FAIL_ON="${REBUTTAL_PROMISE_FAIL_ON:-P0}"
COST_CHECK="${REBUTTAL_COST_CHECK:-1}"
COST_FAIL_ON="${REBUTTAL_COST_FAIL_ON:-P0}"
COST_REQUIRE="${REBUTTAL_COST_REQUIRE:-0}"
COST_REQUIRE_FAMILIES="${REBUTTAL_COST_REQUIRE_FAMILIES:-1}"
REVISION_MAP_CHECK="${REBUTTAL_REVISION_MAP_CHECK:-1}"
REVISION_MAP_FAIL_ON="${REBUTTAL_REVISION_MAP_FAIL_ON:-P0}"
REVISION_MAP_REQUIRE="${REBUTTAL_REVISION_MAP_REQUIRE:-0}"
LAYOUT_READINESS_CHECK="${REBUTTAL_LAYOUT_READINESS_CHECK:-1}"
LAYOUT_READINESS_FAIL_ON="${REBUTTAL_LAYOUT_READINESS_FAIL_ON:-P0}"

cd "$TEX_DIR"
if ! pdflatex -interaction=nonstopmode -halt-on-error -file-line-error "$TEX_FILE" >/tmp/rebuttal_gate_pdflatex.log 2>&1; then
  echo "PDFLATEX_FAILED: see /tmp/rebuttal_gate_pdflatex.log" >&2
  tail -n 40 /tmp/rebuttal_gate_pdflatex.log >&2 || true
  exit 1
fi

python3 "$ROOT_DIR/skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py" "$TEX_PATH" --fail-on "$LEAK_FAIL_ON"
python3 "$ROOT_DIR/skills/rebuttal-audit/scripts/audit_rebuttal.py" \
  --tex "$TEX_PATH" \
  --pdf "$PDF_PATH" \
  --log "$LOG_PATH" \
  --reviewers "$REVIEWERS" \
  --min-tail-words "$MIN_TAIL_WORDS" \
  --min-tail-fill "$MIN_TAIL_FILL"

if [[ "$LAYOUT_READINESS_CHECK" != "0" ]]; then
  python3 "$ROOT_DIR/scripts/check_layout_readiness.py" "$PDF_PATH" --fail-on "$LAYOUT_READINESS_FAIL_ON"
fi

if [[ -n "$CLAIM_LEDGER" ]]; then
  python3 "$ROOT_DIR/scripts/check_claim_ledger.py" "$TEX_PATH" --ledger "$CLAIM_LEDGER" --fail-on "$CLAIM_FAIL_ON"
fi

if [[ -n "$NUMBER_LEDGER" ]]; then
  python3 "$ROOT_DIR/scripts/check_reported_numbers.py" "$TEX_PATH" --numbers "$NUMBER_LEDGER" --fail-on "$NUMBER_FAIL_ON"
fi

if [[ -n "$RESULT_TABLE" || -n "$RESULT_EXPECTATIONS" ]]; then
  if [[ -z "$RESULT_TABLE" || -z "$RESULT_EXPECTATIONS" ]]; then
    echo "Both REBUTTAL_RESULT_TABLE and REBUTTAL_RESULT_EXPECTATIONS are required for result-table checks." >&2
    exit 2
  fi
  python3 "$ROOT_DIR/scripts/check_result_table.py" "$RESULT_TABLE" --expect "$RESULT_EXPECTATIONS" --fail-on "$RESULT_FAIL_ON"
fi

if [[ -n "$ISSUE_MAP" ]]; then
  python3 "$ROOT_DIR/scripts/check_reviewer_issue_map.py" "$TEX_PATH" --map "$ISSUE_MAP" --reviewers "$ISSUE_MAP_REVIEWERS" --fail-on "$ISSUE_MAP_FAIL_ON"
fi

if [[ "$TONE_CHECK" != "0" ]]; then
  python3 "$ROOT_DIR/scripts/check_rebuttal_tone.py" "$TEX_PATH" --fail-on "$TONE_FAIL_ON"
fi

if [[ "$COST_CHECK" != "0" ]]; then
  cost_cmd=(python3 "$ROOT_DIR/scripts/check_cost_evidence.py" "$TEX_PATH" --fail-on "$COST_FAIL_ON")
  if [[ "$COST_REQUIRE" != "0" ]]; then
    cost_cmd+=(--require-cost)
  fi
  if [[ "$COST_REQUIRE_FAMILIES" == "0" ]]; then
    cost_cmd+=(--no-require-baseline-families)
  fi
  "${cost_cmd[@]}"
fi

if [[ "$REVISION_MAP_CHECK" != "0" ]]; then
  revision_map_cmd=(python3 "$ROOT_DIR/scripts/check_revision_map.py" "$TEX_PATH" --fail-on "$REVISION_MAP_FAIL_ON")
  if [[ "$REVISION_MAP_REQUIRE" != "0" ]]; then
    revision_map_cmd+=(--require-map)
  fi
  "${revision_map_cmd[@]}"
fi

if [[ -n "$RESPONSE_TEXT" ]]; then
  response_cmd=(python3 "$ROOT_DIR/scripts/check_response_text.py" "$RESPONSE_TEXT" --platform "$RESPONSE_PLATFORM" --fail-on "$RESPONSE_FAIL_ON")
  if [[ -n "$RESPONSE_REVIEWERS" ]]; then
    response_cmd+=(--reviewers "$RESPONSE_REVIEWERS")
  fi
  if [[ "$RESPONSE_REQUIRE_REVIEWERS" != "0" ]]; then
    response_cmd+=(--require-reviewers)
  fi
  if [[ -n "$RESPONSE_MAX_WORDS" ]]; then
    response_cmd+=(--max-words "$RESPONSE_MAX_WORDS")
  fi
  if [[ -n "$RESPONSE_MAX_CHARS" ]]; then
    response_cmd+=(--max-chars "$RESPONSE_MAX_CHARS")
  fi
  "${response_cmd[@]}"
fi

if [[ "$PROMISE_CHECK" != "0" ]]; then
  python3 "$ROOT_DIR/scripts/check_revision_promises.py" "$TEX_PATH" --fail-on "$PROMISE_FAIL_ON"
fi

echo "GATES_OK $PDF_PATH"
