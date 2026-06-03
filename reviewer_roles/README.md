# Reviewer Role Prompts

Use these prompts as separate critique passes over the rendered PDF and source TeX. Do not blend them into one generic editor voice.

Recommended order:

1. `protocol_cost_reviewer.md`
2. `evidence_artifact_consistency.md`
3. `deployment_fairness_reviewer.md`
4. `threshold_attribution_reviewer.md`
5. `layout_submission_auditor.md`
6. `supportive_clarity_reviewer.md`
7. `AC_synthesizer.md`

Each role must output:

- P0 findings
- P1 findings
- P2 polish
- Minimal recommended patch
- Submit / revise recommendation

Persona discipline:

- Findings first, prose second.
- Prefer concrete file/line/table references when available.
- Do not reward longer rebuttals unless the added evidence changes reviewer trust.
- Flag internal strategy language as P0/P1 even if the scientific content is useful.
