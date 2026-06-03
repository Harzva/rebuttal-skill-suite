# Release Checklist

Before publishing this repository:

- Run skill validation for both skills.
- Run `scripts/run_rebuttal_gates.sh` on at least one real rebuttal.
- Run `scripts/aggregate_reviewer_feedback.py` on at least one persona-feedback directory or role-prompt directory as a syntax sanity check.
- Run `scripts/check_persona_outputs.py reviewer_roles`.
- Run `scripts/check_claim_ledger.py` on the anonymous fixture and any project-specific ledger used for the rebuttal.
- Run `scripts/check_reported_numbers.py` when the rebuttal contains compact result numbers.
- Run `scripts/check_result_table.py` when the rebuttal or supplement includes compact summary CSV/TSV tables.
- Run `scripts/check_reviewer_issue_map.py` when reviewer concerns have been decomposed into a checklist or coverage matrix.
- Run `scripts/check_rebuttal_tone.py` before final submission to catch defensive, overclaiming, casual, or strategy-like wording.
- Run `scripts/check_response_text.py` on the final pasted response when submitting through OpenReview, CMT, or a plain text box.
- Run `scripts/check_revision_promises.py` when the response contains `we will add/clarify/report/update` revision commitments.
- Run `scripts/render_dashboard_views.py` when README dashboard preview assets may have changed.
- Run `scripts/run_regression_fixtures.sh` to ensure known bad examples fail.
- Run `scripts/validate_suite.sh` before tagging.
- Run `scripts/validate_release_package.py .`.
- Run `scripts/build_release_archive.sh` and validate the extracted archive.
- Run `scripts/validate_repo_clean.py .` to reject generated PDFs, logs, aux files, bytecode, and cache directories.
- Confirm installed skills and repository skill copies match with `scripts/install_skills.sh --check`.
- Confirm reviewer-role prompts do not contain project-specific claims, private paths, or internal strategy wording.
- Confirm README install instructions work from a fresh clone.
- Tag the release after validation passes.

Validation commands:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/rebuttal-audit
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/rebuttal-leak-audit
bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex R1,R2,R3,R4
python3 scripts/aggregate_reviewer_feedback.py reviewer_roles
python3 scripts/check_persona_outputs.py reviewer_roles
python3 scripts/check_claim_ledger.py examples/anonymous_rebuttal.tex --ledger schemas/claim_ledger.example.csv
python3 scripts/check_reported_numbers.py examples/anonymous_rebuttal.tex --numbers schemas/reported_numbers.example.csv
python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv
python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers R1,R2,R3,R4 --fail-on P1
python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1
python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers R1,R2,R3,R4 --require-reviewers --platform openreview --max-words 220 --max-chars 1500
python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1
python3 scripts/render_dashboard_views.py
python3 scripts/run_regression_fixtures.sh
python3 scripts/validate_release_package.py .
RELEASE_OUT_DIR=/tmp/rebuttal-release bash scripts/build_release_archive.sh
REBUTTAL_CLAIM_LEDGER=schemas/claim_ledger.example.csv bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex R1,R2,R3,R4
REBUTTAL_NUMBER_LEDGER=schemas/reported_numbers.example.csv bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex R1,R2,R3,R4
REBUTTAL_RESULT_TABLE=examples/result_summary.csv REBUTTAL_RESULT_EXPECTATIONS=schemas/result_table_expectations.example.csv bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex R1,R2,R3,R4
bash scripts/validate_suite.sh /path/to/rebuttal.tex R1,R2,R3,R4
bash scripts/install_skills.sh --check
python3 scripts/validate_repo_clean.py .
```

Release blockers:

- Any P0 persona finding without a documented fix or explicit non-fix rationale.
- Any high-severity leak in reviewer-facing content.
- Any full-set vs subset, fixed-vs-tuned, or label-use contradiction.
- Any missing script referenced by README, workflow, or SKILL.md.
- Any generated PDF/log/aux/cache artifact in the repository.
- Any reviewer persona or persona output missing P0/P1/P2, minimal patch, and recommendation sections.
- Any known-bad regression fixture that unexpectedly passes.
- Any reported-number ledger mismatch at the configured failure severity.
- Any structured result-table mismatch at the configured failure severity.
- Any reviewer issue map with missing reviewer rows, unresolved statuses, absent response anchors, or missing evidence pointers for answered high-priority issues.
- Any defensive reviewer-blame, absolute overclaim, casual intensifier, or submission-strategy language in reviewer-facing text.
- Any final pasted response with missing required reviewer IDs, unresolved placeholders, local paths, or platform-unsafe LaTeX-only commands.
- Any broad revision promise that lacks a concrete location or evidence hook.
- Any missing required release file, non-executable script, stale changelog version, or public prompt containing private/project-specific text.
- Any release archive that fails validation after extraction.
