# Rebuttal Skill Suite

A reusable Codex skill suite for high-stakes academic rebuttals. It turns author response writing into a closed loop:

1. Generate a candidate response.
2. Attack it with reviewer and AC personas.
3. Aggregate feedback into P0/P1/P2 risks.
4. Apply the smallest evidence-backed patch.
5. Re-run mechanical gates.
6. Stop when remaining issues are optional polish.

## Contents

- `skills/rebuttal-audit/`: one-page rebuttal audit skill with layout, reviewer coverage, protocol, cost, and adversarial iteration checks.
- `skills/rebuttal-leak-audit/`: leakage audit skill for internal notes, local paths, tool traces, private experiment logistics, and tactical wording.
- `reviewer_roles/`: independent reviewer, AC, artifact-consistency, and layout-auditor prompts.
- `workflows/adversarial_rebuttal_loop.md`: the end-to-end iteration protocol.
- `prompts/upgrade_skill_suite.md`: a paste-ready prompt for repeated suite upgrades from real rebuttal experience.
- `scripts/run_rebuttal_gates.sh`: compile + high-risk leak audit + layout/content audit.
- `scripts/install_skills.sh`: install, dry-run, or sync-check the two skills under a target `CODEX_HOME`.
- `scripts/build_release_archive.sh`: build and validate a distributable tarball without polluting the repo.
- `scripts/aggregate_reviewer_feedback.py`: group reviewer-persona feedback into P0/P1/P2 buckets.
- `scripts/check_claim_ledger.py`: optional project-specific claim ledger for evidence/scope/label-use checks.
- `scripts/check_reported_numbers.py`: optional expected-number ledger for accuracy/result drift checks.
- `scripts/check_result_table.py`: optional structured CSV/TSV result-table checker.
- `scripts/check_reviewer_issue_map.py`: optional reviewer-issue coverage checker for mapping original concerns to response anchors.
- `scripts/check_rebuttal_tone.py`: optional tone-risk checker for defensive, overclaiming, casual, or strategy-like wording.
- `scripts/check_cost_evidence.py`: optional cost-evidence checker for memory, latency baseline, route ratio, and relevant baseline families.
- `scripts/check_revision_map.py`: optional revision/protocol-map checker for role and label-use consistency.
- `scripts/check_layout_readiness.py`: optional layout-readiness checker for lower-page whitespace and column-bottom balance.
- `scripts/check_response_text.py`: optional pasted-response checker for OpenReview/CMT/plain text-box submissions.
- `scripts/check_revision_promises.py`: optional checker for concrete, auditable revision promises.
- `scripts/check_persona_outputs.py`: validates reviewer personas and persona outputs keep the P0/P1/P2 structure.
- `scripts/run_regression_fixtures.sh`: proves good fixtures pass and intentionally bad fixtures fail.
- `scripts/validate_release_package.py`: checks required files, executable scripts, version/changelog alignment, references, and private/project-specific text leakage.
- `scripts/validate_suite.sh`: release validation wrapper.
- `scripts/validate_repo_clean.py`: release hygiene check for generated artifacts.
- `schemas/claim_ledger.example.csv`: example claim-ledger schema.
- `schemas/reported_numbers.example.csv`: example expected-number schema.
- `schemas/result_table_expectations.example.csv`: example structured result-table expectation schema.
- `examples/`: anonymous toy rebuttal and persona-feedback fixtures.

## Install Locally

Copy the skills into your Codex skills directory:

```bash
bash scripts/install_skills.sh
```

Check installed copies match the repository:

```bash
bash scripts/install_skills.sh --check
```

## Run Mechanical Gates

```bash
bash scripts/run_rebuttal_gates.sh \
  /path/to/rebuttal.tex \
  FEoB,bCeM,y76H,MekP
```

The gate compiles the TeX, fails on high-severity public-facing leaks, checks reviewer coverage, page count, LaTeX warnings, short visual tail lines, protocol/cost consistency signals, and one-page fullness.

To add paper-specific claim checks without hardcoding them into the suite:

```bash
REBUTTAL_CLAIM_LEDGER=/path/to/claim_ledger.csv \
  bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

To also check reported numbers:

```bash
REBUTTAL_NUMBER_LEDGER=/path/to/reported_numbers.csv \
  bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

To check a structured result summary table:

```bash
REBUTTAL_RESULT_TABLE=/path/to/result_summary.csv \
REBUTTAL_RESULT_EXPECTATIONS=/path/to/result_table_expectations.csv \
  bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

To check that every original reviewer issue maps to a concrete response anchor:

```bash
REBUTTAL_ISSUE_MAP=/path/to/reviewer_issue_map.csv \
  bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

The issue map should include `reviewer`, `issue_id`, `concern`, `response_anchor`, `status`, and optional `evidence_pointer` / `rationale` columns. This is useful for the final checklist pass before freezing.

To check tone risks before final submission:

```bash
python3 scripts/check_rebuttal_tone.py /path/to/rebuttal.tex --fail-on P1
```

This flags defensive reviewer-blame, absolute overclaims, casual intensifiers, and strategy-like wording that should be rewritten into neutral scientific clarification. It suppresses common bounded/negative uses such as `does not assume X is always reliable`.

To check cost evidence before final submission:

```bash
python3 scripts/check_cost_evidence.py /path/to/rebuttal.tex --fail-on P1
```

This flags cost answers that mention cost/routing but omit memory, latency relative to a named baseline, route ratio, or relevant proposal-only / VLM-only / verifier-only / routed-family comparisons. The main gate runs this check nonblocking by default unless `REBUTTAL_COST_FAIL_ON` is raised.

To check a compact revision/protocol map:

```bash
python3 scripts/check_revision_map.py /path/to/rebuttal.tex --fail-on P1
```

This flags rows where a main/deployable claim looks tuned, a diagnostic/fixed-pair row lacks shared-pair wording, or a calibrated/tuned row looks label-free. The main gate runs this check nonblocking by default unless `REBUTTAL_REVISION_MAP_FAIL_ON` is raised.

To check one-page layout readiness:

```bash
python3 scripts/check_layout_readiness.py /path/to/rebuttal.pdf --fail-on P1
```

This flags large lower-page blanks and severe column-bottom imbalance, while recommending safe title/spacing/table-placement changes instead of filler. The main gate runs this check nonblocking by default unless `REBUTTAL_LAYOUT_READINESS_FAIL_ON` is raised.

To check the final text that will be pasted into a platform response box:

```bash
REBUTTAL_RESPONSE_TEXT=/path/to/final_response.md \
REBUTTAL_RESPONSE_MAX_WORDS=750 \
REBUTTAL_RESPONSE_PLATFORM=openreview \
  bash scripts/run_rebuttal_gates.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

This catches missing reviewer IDs, unresolved placeholders, local paths, and LaTeX-only layout commands that may be harmless in a PDF but unsafe in a pasted response.

To check whether promised revisions are concrete enough for reviewers to audit:

```bash
python3 scripts/check_revision_promises.py /path/to/rebuttal.tex --fail-on P1
```

This flags `we will add/clarify/report...` statements that lack a table, figure, appendix, caption, artifact, repository, or revised-paper location in the same paragraph.
The checker is LaTeX-aware enough to preserve escaped percentage signs such as `\%` when scanning compact result paragraphs, so a percentage-heavy sentence does not hide later revision-location text.
Limitation, failure, and weak-case promises are checked explicitly: `we will state this limitation` should name the limitation paragraph, discussion section, table caption, appendix, or artifact where the bound will become auditable.
For compact LaTeX revision maps, `tabular` rows are checked as row-level contexts so a `Where` cell only supports promises in the same row.

## Run Reviewer Personas

Use the prompt files in `reviewer_roles/` as independent passes over the rendered PDF and source TeX:

```text
Use reviewer_roles/bCeM_protocol_cost.md to review rebuttal.pdf and rebuttal.tex.
Find P0/P1/P2 issues first, then propose minimal fixes.
```

Recommended order:

1. `bCeM_protocol_cost.md`
2. `evidence_artifact_consistency.md`
3. `FEoB_deployment_fairness.md`
4. `MekP_threshold_attribution.md`
5. `layout_submission_auditor.md`
6. `y76H_supportive_clarity.md`
7. `AC_synthesizer.md`

After collecting persona outputs, aggregate them:

```bash
python3 scripts/aggregate_reviewer_feedback.py feedback_dir/
```

Check persona outputs preserve the required sections:

```bash
python3 scripts/check_persona_outputs.py feedback_dir/
```

## P0/P1/P2 Severity Standard

- `P0`: factual contradiction, protocol ambiguity, label-use confusion, private leakage, evidence mismatch, or anything that can make the AC distrust the response.
- `P1`: missing reviewer-specific evidence, cost/fairness/negative-case gap, unclear attribution, overclaiming, vague limitation promise, or a table/prose mismatch that weakens score recovery.
- `P2`: density, wording, table polish, optional title/spacing, harmless warnings, or taste-level suggestions.

## Twenty Upgrade Patterns Encoded in 0.2.0

1. Force strict results, diagnostics, and calibrated analyses into separate language.
2. Require threshold and fixed-pair claims to state scope.
3. Treat `none`, `shared pair`, and `per-dataset tuned` label use as different claims.
4. Flag full-set vs subset contradictions.
5. Prefer a protocol ledger or revision map for claim provenance.
6. Require every important number to map to a stable artifact or table.
7. Separate deployable claims from sensitivity analysis.
8. Ask cost reviewers for memory, latency, and route-ratio evidence.
9. Require latency baselines to say what they are relative to.
10. Compare CLIP-only, VLM-only, verifier-only, and routed variants when relevant.
11. Diagnose negative cases as accuracy, cost, routing, prompt, or prior-reliability failures.
12. Bound broader-use claims rather than promising open-ended generality.
13. Detect local paths, logs, tool traces, and private experiment logistics.
14. Detect teacher/advisor/AI/persona feedback leakage.
15. Rewrite tactical AC/reviewer wording into public scientific claims.
16. Inspect rendered PDF layout, not only source text.
17. Treat large lower-column blanks as a persuasion risk, not only a formatting issue.
18. Avoid endless polish once only P2 remains.
19. Aggregate independent persona outputs before patching.
20. Validate repo hygiene before release.

## Release Validation

Run the suite-level validator:

```bash
bash scripts/validate_suite.sh /path/to/rebuttal.tex FEoB,bCeM,y76H,MekP
```

Without an argument, it validates skills, role-prompt structure, anonymous fixtures, and repo hygiene.

The validator includes regression fixtures: good examples must pass, while intentionally bad leak, claim, number, and persona-output examples must fail. This protects the suite from silently weakening over time.

For a release package check:

```bash
python3 scripts/validate_release_package.py .
```

Build and validate a release archive:

```bash
RELEASE_OUT_DIR=/tmp/rebuttal-release bash scripts/build_release_archive.sh
```

## Stop Rule

Stop editing when:

- P0 issues are resolved.
- P1 issues have concrete evidence, explicit bounds, or a deliberate non-fix rationale.
- No internal/developer notes leak.
- PDF is one page and has no obvious layout defects.
- Remaining comments are P2 taste, harmless warnings, or subjective preference.

## Release Hygiene

Before publishing:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/rebuttal-audit
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/rebuttal-leak-audit
python3 scripts/check_persona_outputs.py reviewer_roles
python3 scripts/check_claim_ledger.py examples/anonymous_rebuttal.tex --ledger schemas/claim_ledger.example.csv
python3 scripts/check_reported_numbers.py examples/anonymous_rebuttal.tex --numbers schemas/reported_numbers.example.csv
python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv
python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers FEoB,bCeM,y76H,MekP --fail-on P1
python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1
python3 scripts/check_cost_evidence.py examples/cost_evidence_good.md --fail-on P1
python3 scripts/check_revision_map.py examples/revision_map_good.tex --fail-on P1 --require-map
python3 scripts/check_layout_readiness.py examples/layout_metrics_good.txt --fail-on P2
python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers FEoB,bCeM,y76H,MekP --require-reviewers --platform openreview --max-words 220 --max-chars 1500
python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1
python3 scripts/run_regression_fixtures.sh
python3 scripts/validate_release_package.py .
RELEASE_OUT_DIR=/tmp/rebuttal-release bash scripts/build_release_archive.sh
python3 scripts/validate_repo_clean.py .
```

## Optional drafting and visual helper tools

These helpers are advisory scaffolds for late-stage rebuttal work. They are useful before the final gate, but their output should still be inspected by a human author.

### Draft a reviewer-issue map

```bash
python3 scripts/generate_reviewer_issue_map.py reviews.md \
  --response rebuttal.tex \
  --reviewers R1,R2,R3 \
  --output reviewer_issue_map.draft.csv
```

The generated CSV is a starting point for `scripts/check_reviewer_issue_map.py`; verify each response anchor, status, and evidence pointer before treating it as a gate input.

### Check screenshot-style visual density

```bash
python3 scripts/check_pdf_visual_density.py rebuttal.pdf --fail-on P1
```

This rasterizes the first PDF page with `pdftoppm` when available and reports dense visual bands that can make compact tables look collapsed. It can also read key=value metrics fixtures such as `examples/visual_density_good.txt`.

### Select a response-box budget preset

```bash
python3 scripts/response_budget_presets.py --list
python3 scripts/response_budget_presets.py openreview-750w --args
python3 scripts/response_budget_presets.py openreview-750w --shell
```

Presets are conservative defaults for text-box workflows; always check the current submission instructions before treating a preset as binding.
