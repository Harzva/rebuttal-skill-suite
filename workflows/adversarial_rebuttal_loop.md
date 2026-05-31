# Adversarial Rebuttal Loop

This workflow is for rebuttals where a single polished response must satisfy reviewers with different concerns under a strict page limit.

## Loop

1. **Freeze a candidate draft.** Compile the PDF and keep the TeX/PDF/log trio together.
2. **Run mechanical gates.** Use `scripts/run_rebuttal_gates.sh` to check compile status, page count, reviewer coverage, leakage, layout tails, and protocol/cost signals.
3. **Run reviewer personas independently.** Use prompts from `reviewer_roles/`. Do not merge personas into one generic critique; disagreement is useful evidence.
4. **Aggregate findings.** Use `scripts/aggregate_reviewer_feedback.py` and preserve source persona names.
5. **Patch minimally.** Fix the highest-risk shared concern with the smallest evidence-backed edit.
6. **Check issue coverage.** For high-risk rebuttals, map each original reviewer issue to a response anchor and status.
7. **Re-run gates.** Every patch can create a new leak, line break, contradiction, table/prose mismatch, issue-map gap, or pasted-response problem.
8. **Check platform text.** If the final answer will be pasted into OpenReview, CMT, or another text box, run the pasted-response checker before freezing.
9. **Freeze when done.** If the harshest skeptic and the AC persona both say submit or only P2 issues remain, stop.

## Severity Standard

- `P0`: factual contradiction, protocol ambiguity, label-use confusion, private-note leakage, evidence mismatch, or AC trust risk.
- `P1`: missing reviewer-specific evidence, cost/fairness/negative-case gap, unclear attribution, overclaiming, or weak support for score movement.
- `P2`: density, wording, minor tail lines, table polish, harmless warnings, or taste-level preference.

## Protocol Ledger

When a rebuttal involves tuned, calibrated, fixed, or diagnostic variants, create a compact ledger in prose or table form. For each key row, track:

- Role: main claim, mechanism, diagnostic, calibrated analysis, ablation, or future work.
- Scope: full benchmark, subset, small diagnostic set, single dataset, or qualitative case.
- Label use: none, shared global rule, shared pair, validation split, per-dataset tuning, or test-set tuning.
- Evidence pointer: main table, supplement table, appendix figure, released artifact, or statement to add in revision.
- Claim status: deployable result, sensitivity analysis, limitation, or planned clarification.

If any row changes during iteration, update every mention in prose, tables, captions, and revision maps.
Run `scripts/check_revision_map.py` on compact revision or protocol maps. Main/deployable rows should look label-free or preset, diagnostic/fixed-pair rows should say shared/fixed pair, and calibrated/tuned rows should not look label-free.

For project-specific risks, encode the ledger as CSV and run `scripts/check_claim_ledger.py`. Keep the generic suite free of paper-specific claims; put paper-specific patterns in a local ledger that is not reviewer-facing.

For fragile result numbers, encode expected values in `scripts/check_reported_numbers.py` format. This is useful when a rebuttal contains many compact accuracy, cost, or ablation numbers and a one-digit drift could damage trust.

For structured appendix, one-liner, or summary tables, run `scripts/check_result_table.py` against the CSV/TSV table. This catches cases where prose and machine-readable tables silently diverge.

## Reviewer-Issue Coverage Rule

When reviewers raise several distinct concerns, keep a compact issue map. Each row should include:

- Reviewer ID and issue ID.
- Severity or priority.
- Original concern in neutral language.
- Response anchor: exact phrase or compact heading present in the rebuttal.
- Status: `answered`, `bounded`, `merged`, `nonfix`, `revision-promised`, or `deferred`.
- Evidence pointer or rationale when the status is not a direct answer.

Run `scripts/check_reviewer_issue_map.py` before freezing. Missing reviewer rows, unresolved statuses, absent anchors, or evidence-free high-priority answers are AC trust risks.

## Cost Evidence Rule

If reviewers ask about cost, give a scannable answer. When relevant, compare:

- CLIP-only: memory class, latency class, route ratio N/A.
- VLM-only: memory class, latency baseline, route ratio 100 percent VLM.
- Verifier-only: same VLM/verifier cost but no routing shortcut.
- Routed method: memory, latency relative to stated baseline, and route ratio.

A cost paragraph without memory, latency, and route-ratio evidence is usually too weak for a skeptical systems or deployment reviewer.
Run `scripts/check_cost_evidence.py` when cost appears in the response. Treat missing latency baseline or missing baseline-family comparisons as P1 unless the rebuttal explicitly says the reviewer did not request cost evidence.

## Negative-Case Rule

Do not hide weak cases. Classify them precisely:

- Accuracy-negative: the method is worse under the stated metric.
- Cost-negative: accuracy is acceptable but inference cost is too high.
- Routing-sensitive: threshold or confidence route changes behavior.
- Prompt-sensitive: templates or candidate descriptions change behavior.
- Prior-sensitive: proposal model misses the correct class before verification.

The fix is often one sentence, not a new table.

## Evidence Rules

- Every number should map to a table, appendix, artifact, or explicitly stated calculation.
- Do not use local paths, raw logs, or private run names as reviewer-facing evidence.
- Use neutral artifact names or appendix references.
- Keep calibrated/tuned analysis visually separate from strict zero-shot claims.
- When two reviewers ask adjacent questions, answer both but do not let one reviewer-specific tactic leak into the public response.

## Tone Rule

Reviewer-facing prose should be calm, evidence-backed, and bounded. Rewrite:

- Reviewer-blame such as `the reviewer is wrong` into `we did not make this clear`.
- Misunderstanding framing into a concrete clarification.
- Absolute claims such as `always`, `guarantee`, or `fully solves` into scoped claims with evidence, while keeping negative caveats such as `does not assume X is always reliable`.
- Casual intensifiers such as `obviously`, `basically`, or `huge` into precise technical wording.
- Submission-strategy wording into direct scientific claims.

Use `scripts/check_rebuttal_tone.py` as a mechanical first pass, then make the smallest rewrite that preserves the evidence.

## Revision Promise Rule

Treat every `we will add/clarify/report/update...` sentence as a public commitment. A good promise should name:

- What will change.
- Where it will change: table, caption, figure, appendix, supplement, main text, repository, or artifact, stated in the same paragraph.
- Which evidence, number, protocol status, or limitation the change makes auditable.

Avoid broad promises such as `we will improve the paper` or `we will add more experiments` unless they are tied to a concrete evidence location and bounded scope. Use `scripts/check_revision_promises.py` as a mechanical first pass.
For LaTeX rebuttals with compact accuracy numbers, escaped percentages such as `\%` must be preserved during checking; otherwise the scanner can accidentally truncate the rest of the paragraph and miss the promised revision location.
If the promise concerns a limitation, failure mode, weak case, or future-work boundary, name the exact limitation paragraph, discussion section, table caption, appendix, or artifact where that bound will be visible.
For compact revision-map tables, judge promises at the row level: a `Where` cell should justify only the promise in that same row, not unrelated rows elsewhere in the table.

## Layout and Persuasion Rules

- Compile and inspect the rendered PDF. Source text is not enough.
- One page is necessary but not sufficient; large lower-column blanks can make the response look unfinished.
- A title can improve perceived completeness if it does not crowd the first paragraph.
- Prefer one compact table over a dense paragraph when the reviewer asked for multiple numbers.
- Run `scripts/check_layout_readiness.py` when lower-column whitespace looks suspicious; treat it as a persuasion signal before changing content.
- Avoid adding content only to fill whitespace; weak filler is worse than clean white space.

## Platform Pasted-Response Rule

When the submission system uses a text box, audit the exact pasted text, not only the LaTeX/PDF source. The pasted version should:

- Mention every reviewer ID that the response claims to address.
- Stay within the configured word or character budget.
- Avoid LaTeX-only layout commands such as `\vspace`, `\hspace`, figures, tables, and `\includegraphics`.
- Avoid unresolved placeholders such as `TODO`, `TBD`, `[fill]`, or `??`.
- Avoid local paths, local Markdown links, and attachment-like file references.

Use `scripts/check_response_text.py` for this final gate.

## Stop Rule

Stop when P0 is gone, P1 is resolved or bounded, mechanical gates pass, and new edits mostly trade one subjective P2 issue for another. At that point, freeze the draft rather than overfitting to style feedback.

## Upgrade Loop for the Suite Itself

After each real rebuttal, add one reusable improvement in this order:

1. Convert the lesson into a persona checklist item, script rule, claim-ledger row, or fixture.
2. Add an anonymous fixture if the failure mode is easy to reproduce.
3. Add a bad regression fixture if the failure mode should become a permanent guardrail.
4. Run `scripts/validate_suite.sh` and a real rebuttal gate.
5. Run `scripts/validate_release_package.py .` before treating the repo as publishable.
6. Run `scripts/build_release_archive.sh` before tagging a release; validate the extracted archive, not only the working tree.
7. Add or update issue-map fixtures when a reviewer concern was accidentally omitted or only implicitly answered.
8. Add or update a pasted-response fixture when the real failure mode appears only after copying text out of the PDF.
9. Sync installed skills only after repo validation passes, preferably with `scripts/install_skills.sh`.
10. Record the change in `CHANGELOG.md` and keep private project details out of published prompts.

## Optional helper-tool pass

Use these helpers when the response is close to final but still needs structured review:

- Generate a draft reviewer-issue map from raw review text with `scripts/generate_reviewer_issue_map.py`, then manually verify every anchor and evidence pointer before running `scripts/check_reviewer_issue_map.py`.
- Run `scripts/check_pdf_visual_density.py` on the rendered PDF when compact tables look visually tight; treat P2 output as an inspection cue and P1 output as a reason to revise spacing, row height, table placement, or wording.
- Use `scripts/response_budget_presets.py` to choose conservative text-box limits for the current platform, then pass the emitted arguments to `scripts/check_response_text.py`.
