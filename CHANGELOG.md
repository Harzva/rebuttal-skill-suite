# Changelog

## 0.23.0

Anonymized dashboard preview pass.

- Added a lightweight static `webview/` dashboard prototype with sanitized sample data for issue coverage, reviewer anchors, and gate status.
- Added `scripts/render_dashboard_views.py` to generate README-safe SVG previews under `docs/images/`.
- Documented the anonymous dashboard views in README while preserving the rule that real paper names, local paths, reviewer identities, and project-specific numbers do not belong in reusable suite demos.
- Extended release validation to include `.html`, `.json`, and `.svg` public files so dashboard assets are scanned for project-specific leakage.

## 0.22.0

Escaped-percent claim/number ledger and temp-output hygiene pass.

- Fixed claim-ledger and reported-number normalization so escaped LaTeX percentages such as `\%` are preserved instead of truncating the rest of the source line.
- Applied the same escaped-percent preservation to the rebuttal tone checker and suppressed the bounded guardrail phrase `never cited as no-label evidence`.
- Updated the anonymous regression fixture so claim/number checks must pass through percentage-heavy LaTeX result sentences.
- Switched suite validation and regression fixtures from fixed `/tmp/rebuttal_suite_*.out` paths to private `mktemp` output directories, avoiding root-owned stale temp-file failures.
- Added `REBUTTAL_CLAIM_WINDOW` to the main gate and moved its pdflatex output to a private temporary directory.
- Disabled Python bytecode writes in validation/gate wrappers so release-clean checks do not fail on self-generated `__pycache__` directories.
- Updated README and audit-skill guidance so project-specific claim and number ledgers can safely audit percentage-heavy one-page rebuttals.

## 0.21.0

Reviewer-map drafting, visual-density, and response-budget helper pass.

- Added `scripts/generate_reviewer_issue_map.py` to draft reviewer-issue CSV maps from review text and optional response anchors.
- Added `scripts/check_pdf_visual_density.py` as a screenshot-style heuristic for crowded tables or dense visual bands in one-page PDFs.
- Added `scripts/response_budget_presets.py` for conference/platform response-box budget presets that can emit shell variables or checker arguments.
- Wired the new helpers into README, workflow guidance, audit-skill guidance, release package validation, suite validation, and regression fixtures while keeping visual density advisory rather than a default hard gate.


## 0.20.0

Layout-readiness gate pass.

- Added `scripts/check_layout_readiness.py` to quantify lower-page whitespace, column-bottom imbalance, and low extracted word density for one-page rebuttal PDFs or metrics fixtures.
- Wired the layout-readiness checker into the main rebuttal gate, suite validation, regression fixtures, release package validation, README, workflow, and audit skill guidance.
- Added good and bad layout metrics fixtures so severe lower-column imbalance remains regression-tested.
- Strengthened the layout-submission persona to distinguish harmless P2 white space from unfinished-looking imbalance and to prefer title/spacing/table-placement fixes over filler.

## 0.19.0

Revision-map consistency gate pass.

- Added `scripts/check_revision_map.py` for compact revision/protocol maps with role, row, label-use, and Avg columns.
- Supported complex LaTeX `tabular` column specifications and in-table title rows such as `Revision map` before the actual header.
- Wired the revision-map checker into the main rebuttal gate, suite validation, regression fixtures, release package validation, README, workflow, and audit skill guidance.
- Added good and bad revision-map fixtures so main/deployable rows, diagnostic/fixed-pair rows, and calibrated/tuned rows cannot silently reuse the wrong label-use wording.
- Strengthened artifact-consistency and threshold/attribution personas to inspect revision-map label-use separation directly.

## 0.18.0

Cost-evidence gate pass.

- Added `scripts/check_cost_evidence.py` for scannable cost answers with memory, latency baseline, route ratio, and relevant baseline-family coverage.
- Preserved numeric percentages such as `100% VLM` while still stripping true LaTeX comments during cost-text normalization.
- Wired the cost checker into the main rebuttal gate, suite validation, regression fixtures, release package validation, README, workflow, and audit skill guidance.
- Added good and bad cost-evidence fixtures so missing latency baseline, route ratio, or baseline-family comparisons remain regression-tested.
- Strengthened protocol/cost and deployment/fairness personas to inspect compressed cost tables for baseline and route-ratio interpretability.

## 0.17.0

Tabular row-level revision-promise pass.

- Made the revision-promise checker flatten LaTeX `tabular` environments into row-level contexts before scanning promises.
- Added good and bad fixtures for compact revision-map rows with `Evidence / clarification` and `Where` cells.
- Updated README, workflow, audit-skill guidance, and artifact-consistency persona guidance so one row's `Where` cell cannot justify another row's promise.
- Preserved paragraph-level checking outside tables while making compact one-page revision maps safer to audit.

## 0.16.0

Limitation-promise specificity pass.

- Added explicit detection for limitation, failure-mode, weak-case, and future-work promises that lack a concrete revised-paper location.
- Added good and bad fixtures for `we will state this limitation...` style promises.
- Updated README, workflow, audit-skill guidance, and AC/deployment-fairness personas so limitation promises name the paragraph, section, caption, appendix, or artifact where the bound becomes auditable.
- Preserved the generic promise checker while making negative-case and limitation feedback more actionable for reviewer-facing repair.

## 0.15.0

LaTeX escaped-percent revision-promise pass.

- Fixed the revision-promise checker so escaped LaTeX percentages such as `\%` are preserved instead of being treated as source comments.
- Added a good fixture where a compact result sentence reports a percentage before the same-paragraph revised-table location.
- Updated README, workflow, and audit-skill guidance for percentage-heavy rebuttal paragraphs.
- Removed a real false-positive class where result-heavy protocol paragraphs were truncated before their revision-location text.

## 0.14.0

Paragraph-level revision-promise context pass.

- Upgraded the revision-promise checker from same/next-sentence context to same-paragraph context.
- Added a long-clause good fixture that mirrors real rebuttal wording where the promise and revised-table/caption location are separated by intervening clauses.
- Updated README, workflow, and audit-skill guidance to state the same-paragraph promise rule.
- Preserved strict failures for broad promises whose paragraph still lacks a concrete location or evidence hook.

## 0.13.0

Revision-promise context refinement pass.

- Made the revision-promise checker consider the immediately following sentence when looking for revision locations and evidence hooks.
- Added a good fixture for split promise/location wording, where the promise sentence is followed by a concrete revised-table/caption location.
- Updated README, workflow, and audit-skill guidance to state the same-or-next-sentence rule.
- Preserved strict failures for broad promises whose neighboring text still lacks concrete locations or evidence hooks.

## 0.12.0

Tone-checker context refinement pass.

- Made the tone checker suppress absolute-term matches in nearby negated or bounded caveats, such as `does not assume X is always reliable`.
- Removed `clearly` from the casual-language trigger because it is often legitimate in neutral clarification sentences.
- Expanded the good tone fixture with the real false-positive pattern from final-gate auditing.
- Updated README, workflow, and audit-skill guidance to distinguish unbounded overclaims from negative reliability caveats.

## 0.11.0

Tone-risk audit pass.

- Added a rebuttal tone checker for defensive reviewer-blame, misunderstanding framing, absolute overclaims, casual intensifiers, and submission-strategy wording.
- Added good and bad tone fixtures so harmful tone remains regression-tested.
- Wired tone checks into the main gate, suite validation, regression fixtures, release package validation, Makefile, README, workflow, release checklist, upgrade prompt, and audit skill guidance.
- Strengthened AC and supportive-reviewer personas to judge whether wording supports trust rather than merely conveying facts.

## 0.10.0

Reviewer-issue coverage map pass.

- Added a reviewer-issue map checker that verifies each original concern has a reviewer ID, issue ID, response anchor, status, and evidence pointer or rationale where needed.
- Added an anonymous issue-map schema, good response fixture, and bad regression fixture.
- Wired issue-map checks into the main gate through environment variables, suite validation, regression fixtures, release package validation, Makefile, README, workflow, release checklist, upgrade prompt, and audit skill guidance.
- Strengthened AC and artifact-consistency personas to look for issue coverage rather than only reviewer-name coverage.

## 0.9.0

Revision-promise audit pass.

- Added a revision-promise checker for `we will add/clarify/report/update` commitments.
- Added good and bad promise fixtures so vague, unauditable promises remain a regression-tested failure mode.
- Wired promise checks into the main gate, suite validation, regression fixtures, release package validation, Makefile, README, workflow, release checklist, upgrade prompt, and audit skills.
- Kept real-gate promise failures nonblocking by default unless configured, while preserving strict fixture validation.

## 0.8.0

Platform pasted-response validation pass.

- Added a pasted-response checker for OpenReview, CMT, and plain text-box submissions.
- Added good and bad platform-response fixtures for reviewer coverage, unresolved placeholders, local links, local paths, and LaTeX-only commands.
- Wired response-text checks into gates through environment variables, suite validation, regression fixtures, release package validation, Makefile, README, workflow, release checklist, and audit skill guidance.
- Kept the checker generic so paper-specific response budgets and reviewer IDs stay outside the reusable suite.

## 0.7.0

Release archive and CI validation pass.

- Added release archive builder that copies the publishable package, removes generated artifacts, creates a tarball, extracts it, and validates the extracted archive.
- Added GitHub Actions validation workflow template.
- Wired archive validation into README, release checklist, workflow, Makefile, and package validator.
- Kept archive output outside the repository by default to avoid committing generated release artifacts.

## 0.6.0

Structured result-table consistency pass.

- Added CSV/TSV result-table checker for appendix, one-liner, and summary-result tables.
- Added anonymous result summary fixture and expectation schema.
- Added bad result-summary regression fixture.
- Wired result-table checks into the main gate through environment variables.
- Added a freeform reviewer-feedback fixture to exercise aggregation beyond strict P0/P1/P2 headings.
- Updated validation, release checklist, README, workflow, and audit skill guidance.

## 0.5.0

Install and release-package validation pass.

- Added installer/sync-check script for installing skills into a target `CODEX_HOME`.
- Added release-package validator for required files, executable scripts, version/changelog alignment, stale references, and public private-text leakage.
- Added Makefile targets for validation, regression, package check, and install checks.
- Wired release-package validation into suite validation and release checklist.
- Updated README and workflow to prefer the installer over manual copy.

## 0.4.0

Regression and numeric-consistency pass.

- Added expected-number ledger checker for compact accuracy/result claims.
- Added anonymous reported-number schema and fixture values.
- Added regression-bad fixtures for leakage, claim-ledger failure, number drift, and malformed persona feedback.
- Added regression runner that requires good fixtures to pass and bad fixtures to fail.
- Wired optional reported-number checks into the main rebuttal gate through environment variables.
- Updated suite-level validation to include numeric checks and expected-failure regression tests.
- Expanded README, workflow, release checklist, and audit skill guidance.

## 0.3.0

Release-engineering and fixture pass.

- Added anonymous rebuttal and persona-feedback fixtures.
- Added generic claim-ledger schema and checker for paper-specific consistency checks without hardcoding private project details.
- Added persona-output structure checker for P0/P1/P2, minimal patch, and recommendation sections.
- Added suite-level validation wrapper.
- Wired optional claim-ledger checks into the main rebuttal gate through environment variables.
- Expanded README, workflow, and release checklist with validation commands and suite-upgrade loop.

## 0.2.0

Professionalization pass based on adversarial rebuttal iteration.

- Added stricter protocol-ledger guidance for fixed, diagnostic, calibrated, and tuned claims.
- Added label-use distinctions for none, shared global rule, shared pair, validation split, and per-dataset tuning.
- Added full-set vs subset contradiction checks to the audit skill and script.
- Added cost evidence guidance for memory, latency baseline, and route ratio.
- Added negative-case diagnosis categories.
- Added artifact-consistency and layout-submission reviewer personas.
- Standardized reviewer persona output into P0/P1/P2, minimal patch, and recommendation sections.
- Strengthened AC synthesis and skeptical expert prompts.
- Added reviewer-role reference inside the audit skill.
- Strengthened leak-audit rules for advisor, AI, persona, shell, and private-run traces.
- Updated gate script to fail on high-severity leaks by default.
- Enhanced aggregate script parsing and optional P0 failure behavior.
- Added release hygiene script for generated artifacts.
- Added reusable upgrade prompt for repeated skill-suite improvement.
- Expanded workflow stop rules and layout persuasion checks.
- Updated README with 20 encoded upgrade patterns.

## 0.1.0

Initial publishable release.

- Added `rebuttal-audit` skill with adversarial reviewer loop.
- Added `rebuttal-leak-audit` skill for internal-note and local-path leakage checks.
- Added reviewer/AC role prompts for protocol, cost, deployment, attribution, and synthesis passes.
- Added gate script for compile, leak, reviewer coverage, and layout checks.
- Added feedback aggregation script for P0/P1/P2 triage.
- Added release checklist and reusable workflow documentation.
