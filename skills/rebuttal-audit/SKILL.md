---
name: rebuttal-audit
description: Audit and polish one-page academic rebuttals or author responses, especially LaTeX/PDF responses with reviewer IDs, strict page limits, compact evidence tables, reviewer-specific concerns, protocol or label-use ambiguity, cost evidence, negative-case framing, and strict short-tail-line/orphan-word checks. Use when Codex must check formatting, page fullness, orphan lines, reviewer coverage, cited evidence, rebuttal tone, or final submission readiness.
---

# Rebuttal Audit

## Workflow

Use this checklist whenever preparing a final rebuttal PDF.

1. Identify all reviewers, their stance, and the concern most likely to affect the AC.
2. Group overlapping concerns into 4-6 response blocks, but keep reviewer IDs visible.
3. Put the most dangerous concern first, usually protocol, label use, novelty, fairness, cost, or factual consistency.
4. Add a compact evidence table when reviewers need to scan multiple numbers or variants quickly.
5. For high-risk rebuttals, build a reviewer-issue map so every original concern has a response anchor and status.
6. Cite existing main/supplementary tables, figures, or stable artifacts for every important number.
7. Compile the PDF and inspect the rendered page, log, and extracted text.
8. If the final response will be pasted into OpenReview, CMT, or a text box, audit the exact pasted text as well as the PDF.
9. Iterate until the page is exactly one page, visually intentional, and free of obvious orphan words or awkward single-line leftovers.

## Adversarial Reviewer Loop

Use this loop when a rebuttal needs high-stakes iteration or when multiple reviewers disagree.

1. Freeze the current draft and compile the PDF.
2. Run mechanical gates: page count, LaTeX warnings, tail-line audit, reviewer coverage, protocol/cost signals, and internal-note leakage.
3. Ask reviewer personas to critique the rendered PDF first, then source. If detailed role text is needed, load `references/reviewer_roles.md`.
4. Aggregate persona feedback by risk:
   - `P0`: factual contradiction, protocol ambiguity, label-use uncertainty, private-note leakage, evidence mismatch, or anything an AC can use to distrust the response.
   - `P1`: reviewer-specific missing evidence, cost/fairness/negative-case gaps, overclaiming novelty, unclear concessions, or weak support for score movement.
   - `P2`: readability, line breaks, small table density, wording polish, or harmless layout warnings.
5. Apply only the smallest patch that fixes the highest-risk shared concern.
6. Re-run gates after every patch.
7. Stop when P0/P1 issues are resolved or explicitly bounded, no leakage remains, reviewer concerns are mapped, and remaining comments are P2 taste.

Do not let the loop become endless polish. Once the strongest reviewer persona and the AC persona both say submit or only identify optional P2 tweaks, prefer freezing the draft.

## Content Audit

For each reviewer:

- Confirm their name/ID appears at least once.
- Confirm their highest-risk concern is explicitly answered.
- Confirm each original issue maps to a response anchor, status, and evidence pointer or rationale.
- Confirm factual misunderstandings are corrected without sounding defensive.
- Confirm concessions are precise: say what will change and where.
- Confirm the answer is reviewer-facing, not a strategy note about how to influence that reviewer.
- Confirm tone is neutral: no reviewer-blame, unbounded absolute overclaim, casual intensifier, or submission-strategy language.
- Confirm every `we will add/clarify/report/update` promise names a concrete revision location or evidence hook in the same paragraph.
- Confirm limitation, failure-mode, weak-case, and future-work promises name where the bound will appear, e.g. limitation paragraph, discussion section, table caption, appendix, or artifact.

## Protocol and Evidence Audit

When the response includes fixed, tuned, calibrated, routed, or diagnostic variants, build a mental protocol ledger:

- Role: main claim, mechanism, diagnostic, calibrated analysis, ablation, or future work.
- Scope: full benchmark, subset, small diagnostic set, single dataset, or qualitative examples.
- Label use: none, shared global rule, shared pair, validation split, per-dataset tuning, or test-set tuning.
- Evidence pointer: table, figure, appendix, artifact, or planned revision.
- Claim status: deployable result, sensitivity analysis, limitation, or clarification.

High-risk checks:

- A fixed-pair or threshold claim must state its scope and label-use status.
- Full-set averages and subset diagnostics must not share the same wording.
- A row labeled `none` label use must not secretly depend on a selected pair, validation split, or per-dataset tuning.
- Calibrated/tuned rows should be visually separated from strict zero-shot claims.
- Text, tables, captions, and revision maps must agree after every edit.
- Run a revision-map check when a compact map is present; main/deployable rows should look label-free or preset, diagnostic/fixed-pair rows should state shared/fixed-pair status, and calibrated/tuned rows should not look label-free.
- If the paper has fragile project-specific claims, use a local claim ledger rather than hardcoding those claims into the skill.
- If the rebuttal reports many compact numbers, use an expected-number ledger to catch one-digit drift.
- If the rebuttal depends on a compact result table or appendix CSV/TSV, run a result-table ledger check.
- If the rebuttal has many reviewer concerns, run an issue-map check to catch omitted or only implicit answers.
- If the rebuttal is near final, run a tone check so strong evidence is not weakened by defensive or overclaiming phrasing.
- If the rebuttal contains revision promises, run a promise check so broad commitments do not replace auditable evidence.
- In percentage-heavy LaTeX paragraphs, ensure promise checks preserve escaped percentages such as `\%`; an escaped result number must not be treated as the start of a source comment.
- Treat `we will state this limitation` as incomplete unless it identifies the revised-paper location where the limitation, failure mode, or future-work boundary will be auditable.
- For compact revision-map tables, audit each row independently: a `Where` cell in one row must not be used to excuse an unauditable promise in another row.

## Cost and Negative-Case Audit

For cost-sensitive reviewers, look for a compact comparison across the relevant baselines:

- CLIP-only or proposal-only.
- VLM-only or generator-only.
- Verifier-only or mechanism-isolation row.
- Routed or hybrid method.

The comparison should state memory class, latency relative to a named baseline, and route ratio when applicable. If a method has weak cases, classify them as accuracy-negative, cost-negative, routing-sensitive, prompt-sensitive, or prior-sensitive rather than hand-waving.
Run the cost-evidence checker when a response mentions cost or deployment overhead; missing memory, latency baseline, route ratio, or relevant baseline-family coverage is a P1 for cost-sensitive reviewers.

## Reviewer Persona Pass

When asked to simulate reviewers, run separate passes instead of one blended critique:

- Protocol/cost expert: label use, fixed-vs-tuned confusion, validation leakage, runtime/memory/route-ratio gaps, unsupported averages.
- Artifact-consistency auditor: whether every number/scope/table/prose claim matches the cited artifact.
- Deployment/fairness reviewer: reliability of proposal model, negative cases, broader use, objective comparisons, fairness against baselines.
- Threshold/attribution reviewer: threshold setting, candidate-space verification, mechanism isolation, exact-match evaluation.
- Layout/submission auditor: one-page visual fullness, table density, orphan lines, title/spacing, hidden overflow.
- Supportive-but-concerned reviewer: whether clarification is enough to justify score improvement without bloating the page.
- AC synthesizer: whether reviewer conflicts are resolved and the main claim is credible, bounded, and auditable.

For each persona, output P0/P1/P2 findings first, then proposed minimal fixes. Never ask personas to rewrite the whole rebuttal unless the structure is failing.

## Layout Audit

Visually inspect the rendered PDF, not only the LaTeX source.

- The response must be exactly one page.
- It should look intentionally full: avoid large empty lower halves, especially the right column.
- Avoid orphan words or short phrases alone on a final line, e.g. `and cost.`
- For dense one-page rebuttals, judge tail lines visually: a paragraph tail should occupy roughly 4/5 of its column. Seven visible words can be acceptable when the words are long and the line is visually full; obvious one-word/few-word tails remain defects.
- Check PDF layout with `pdftotext -bbox-layout` or `pdftotext -layout`, because normal `pdftotext` and LaTeX source lines can hide visually short tail lines.
- Avoid headings split from their paragraph.
- Avoid text that appears in extracted PDF text but not in the rendered image; that means content may be outside the visible page box.
- Prefer compact tables over dense walls of text when numbers are central.
- Use layout-readiness checks to distinguish harmless white space from severe lower-column imbalance.
- Use screenshot-style visual-density checks when compact tables may be technically inside the page but visually over-compressed.
- Do not add weak filler just to fill whitespace; a title, spacing adjustment, or compact evidence table is safer.

## Evidence Table Pattern

Use a small table near the top when reviewers ask for protocol, cost, or fairness clarity:

```latex
\begin{center}
\scriptsize
\setlength{\tabcolsep}{2.2pt}
\renewcommand{\arraystretch}{0.93}
\begin{tabular}{@{}p{0.22\columnwidth}p{0.49\columnwidth}p{0.22\columnwidth}@{}}
\toprule
Issue & Evidence / clarification & Where \\
\midrule
Strict protocol & Fixed threshold, no labels, main number & Appx. table \\
Diagnostic & Shared pair, full benchmark, not main claim & Supp. table \\
Cost & mem / latency vs baseline / route ratio & Revision \\
\bottomrule
\end{tabular}
\end{center}
```

If a column is narrow, use ragged-right `p{}` columns to avoid ugly justification.

## Tooling

Run `scripts/audit_rebuttal.py` for a quick mechanical check. It does not replace visual inspection.

```bash
python3 /root/.codex/skills/rebuttal-audit/scripts/audit_rebuttal.py \
  --tex path/to/rebuttal.tex \
  --pdf path/to/rebuttal.pdf \
  --log path/to/rebuttal.log \
  --reviewers FEoB,bCeM,y76H,MekP \
  --min-tail-words 7 \
  --min-tail-fill 0.80
```

The script checks page count, reviewer coverage, warning patterns, rough PDF fullness, PDF-layout tail lines, and common protocol/cost consistency signals.

For paper-specific consistency checks, run a claim ledger:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_claim_ledger.py \
  path/to/rebuttal.tex \
  --ledger path/to/claim_ledger.csv \
  --fail-on P0
```

For reported-number checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_reported_numbers.py \
  path/to/rebuttal.tex \
  --numbers path/to/reported_numbers.csv \
  --fail-on P0
```

For structured result-table checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_result_table.py \
  path/to/result_summary.csv \
  --expect path/to/result_table_expectations.csv \
  --fail-on P0
```

For reviewer-issue coverage checks, first draft the map if needed and then gate the verified CSV:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/generate_reviewer_issue_map.py \
  path/to/reviews.md \
  --response path/to/rebuttal.tex \
  --reviewers R1,R2,R3 \
  --output path/to/reviewer_issue_map.draft.csv

python3 /path/to/rebuttal-skill-suite/scripts/check_reviewer_issue_map.py \
  path/to/rebuttal.tex \
  --map path/to/reviewer_issue_map.csv \
  --reviewers FEoB,bCeM,y76H,MekP \
  --fail-on P1
```

For tone-risk checks, allow bounded negations such as `does not assume X is always reliable`:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_rebuttal_tone.py \
  path/to/rebuttal.tex \
  --fail-on P1
```

For cost-evidence checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_cost_evidence.py \
  path/to/rebuttal.tex \
  --fail-on P1
```

For revision/protocol-map consistency checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_revision_map.py \
  path/to/rebuttal.tex \
  --fail-on P1
```

For layout-readiness and screenshot-style density checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_layout_readiness.py \
  path/to/rebuttal.pdf \
  --fail-on P1

python3 /path/to/rebuttal-skill-suite/scripts/check_pdf_visual_density.py \
  path/to/rebuttal.pdf \
  --fail-on P1
```

For final pasted-response checks, select a budget preset before checking the exact pasted text:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/response_budget_presets.py openreview-750w --args

python3 /path/to/rebuttal-skill-suite/scripts/check_response_text.py \
  path/to/final_response.md \
  --reviewers FEoB,bCeM,y76H,MekP \
  --require-reviewers \
  --platform openreview \
  --max-words 750 \
  --fail-on P0
```

For revision-promise checks:

```bash
python3 /path/to/rebuttal-skill-suite/scripts/check_revision_promises.py \
  path/to/rebuttal.tex \
  --fail-on P1
```
