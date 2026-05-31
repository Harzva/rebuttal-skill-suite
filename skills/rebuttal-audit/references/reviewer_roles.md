# Reviewer Role Reference

Load this only when running adversarial reviewer simulation.

## Required Persona Output

Each persona should return:

- `P0 findings`: trust-breaking issues, contradictions, leakage, or protocol ambiguity.
- `P1 findings`: missing evidence, fairness/cost/negative-case gaps, attribution problems, or overclaiming.
- `P2 polish`: optional wording, density, layout, or table tweaks.
- `Minimal patch`: the smallest text/table change that resolves the highest-risk issue.
- `Recommendation`: submit as-is, minor revise, or revise before submission.

## Persona Set

- Protocol/cost expert: attack label use, fixed-vs-tuned wording, validation leakage, cost baselines, route ratios, unsupported averages.
- Artifact-consistency auditor: cross-check every number, scope, table reference, artifact name, and revision-map row.
- Deployment/fairness reviewer: test practical reliability, negative cases, broader use, and fairness against baselines.
- Threshold/attribution reviewer: isolate threshold selection, candidate verification, mechanism contribution, and exact-match evaluation.
- Layout/submission auditor: inspect one-page visual fullness, short tails, title/spacing, overfull/underfull warnings, and hidden overflow.
- Supportive reviewer: decide whether the clarification is enough for score improvement without creating bloat.
- AC synthesizer: judge whether the response is credible, bounded, and ready after seeing all reviewer concerns.

## Persona Discipline

Do not ask personas for generic copyediting first. They must find risks before proposing prose. They should be skeptical enough to catch a contradiction that the authors would rather not see, but their patch should still be minimal and evidence-preserving.
