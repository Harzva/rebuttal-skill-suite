---
name: rebuttal-dashboard-data
description: Build private and sanitized dashboard data for Rebuttal Skill Suite by scanning a project, paper, reviews, rebuttal drafts, evidence ledgers, gate outputs, and persona feedback, then producing a JSON snapshot that the static webview can load.
---

# Rebuttal Dashboard Data

Use this skill when a user wants to turn their project, paper, reviewer comments, rebuttal draft, evidence ledgers, or gate outputs into data for the Rebuttal Skill Suite dashboard.

The skill has one rule: keep private local dashboard data separate from public demo data.

## Outputs

Private local dashboard data:

```text
.local/dashboard_data.json
webview/dashboard_data.local.json
```

These files may contain project-specific summaries and should not be committed.

Public sanitized dashboard data:

```text
webview/sample_dashboard_data.json
```

This file may be committed only after sanitization and leak checks.

## Data Flow

```text
project + paper + reviews + rebuttal + ledgers + gate outputs
  -> extract reviewer issues, evidence anchors, gates, risks
  -> write private dashboard snapshot
  -> refresh webview locally
  -> optionally sanitize into public sample data
  -> regenerate README SVG previews
```

## Recommended Workflow

1. Locate the project root, paper source, rebuttal draft, reviewer comments, issue map, claim ledger, number ledger, result table, and gate outputs.
2. Prefer existing structured files when available:
   - `schemas/reviewer_issue_map.example.csv`-style issue maps.
   - Claim, number, result-table, and revision-promise ledgers.
   - Gate output logs from `scripts/run_rebuttal_gates.sh` or focused checkers.
3. If reviewer comments are unstructured, read them and group concerns into issue cards with reviewer IDs, themes, severity, status, evidence needs, and risk boundaries.
4. If evidence ledgers exist, summarize coverage counts. If they do not exist, add an access issue instead of inventing coverage.
5. If historical snapshots exist, build a real risk trend. If not, show only a current snapshot note.
6. Write private data with `scripts/build_dashboard_data.py`.
7. Open the dashboard with `scripts/start_dashboard.sh` and click Refresh after rebuilding data.
8. Only after the private dashboard looks correct, create public demo data with `scripts/sanitize_dashboard_data.py`.
9. Regenerate README previews with `scripts/render_dashboard_views.py` after changing public sample data.

## Mechanical Builder

Use the builder when structured inputs already exist or when you want a truthful first snapshot:

```bash
python3 scripts/build_dashboard_data.py \
  --project-root /path/to/project \
  --paper /path/to/paper.tex \
  --rebuttal /path/to/rebuttal.tex \
  --reviews /path/to/reviews.md \
  --reviewer-issue-map /path/to/reviewer_issue_map.csv \
  --claim-ledger /path/to/claim_ledger.csv \
  --number-ledger /path/to/reported_numbers.csv \
  --gate-output /path/to/gate_output.txt
```

By default, this writes `.local/dashboard_data.json` and mirrors it to `webview/dashboard_data.local.json` so the static webview can load it.

## AI-Assisted Extraction

When structured files are missing, use the prompts in `prompts/` to produce a dashboard draft. Keep the extraction conservative:

- Do not quote long reviewer text.
- Summarize reviewer concerns in your own words.
- Use reviewer IDs like `R1/R2/R3/R4`.
- Use `P0` only for trust-breaking risks: contradiction, leakage, protocol ambiguity, evidence mismatch, or unbounded claims.
- Use `P1` for missing evidence, unclear scope, cost/fairness gaps, weak reviewer coverage, or broad promises.
- Use `P2` for layout, wording, density, or optional clarity polish.
- Mark unknown fields as `unknown`, `watch`, or `needs evidence`; never fabricate evidence anchors.

## Sanitization

Before publishing dashboard data or README screenshots, run:

```bash
python3 scripts/sanitize_dashboard_data.py \
  .local/dashboard_data.json \
  webview/sample_dashboard_data.json \
  --project-title "Anonymized Rebuttal Project"
```

Then regenerate README previews:

```bash
python3 scripts/render_dashboard_views.py
```

Public data must not contain local paths, paper names, author names, real reviewer identifiers, submission IDs, private experiment logistics, raw reviewer text, or AI/advisor/internal-process traces.

## Webview Refresh Contract

The dashboard is static HTML/JS. The Refresh button reloads the latest JSON file; it does not execute local scripts from the browser.

To update the dashboard:

```bash
python3 scripts/build_dashboard_data.py ...
```

Then click Refresh in the browser.
