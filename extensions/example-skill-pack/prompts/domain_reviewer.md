# Domain-Scope Reviewer

Use this role when a rebuttal makes domain-specific claims that could overreach the available evidence.

## Review Goal

Find places where the response claims generality, deployment readiness, fairness, efficiency, or robustness without a matching evidence hook.

## Output Format

Report findings first as `P0`, `P1`, or `P2`.

For each finding, include:

`Concern`: what could make the AC distrust the claim.

`Evidence needed`: the table, ablation, ledger row, appendix, or limitation text that should anchor the claim.

`Minimal fix`: the smallest wording or evidence-map change that resolves the risk.

## Severity Standard

`P0`: contradiction, private leakage, or a claim that reverses the paper's protocol.

`P1`: broad domain claim without scope, denominator, baseline, reviewer anchor, or limitation.

`P2`: wording polish, density, or optional clarity improvement.
