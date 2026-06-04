# Extract Dashboard Issues

Given reviewer comments, a rebuttal draft, and any issue maps or evidence ledgers, create conservative dashboard issue cards.

For each issue, output JSON fields:

`id`: stable ID like `ISS-001`.

`title`: short anonymized concern title.

`theme`: one of `Protocol`, `Evidence`, `Cost`, `Safety`, `Scope`, `Coverage`, `Layout`, `Submission`, or another compact theme.

`reviewers`: reviewer IDs such as `R1`, `R2`, `R3`.

`severity`: `P0`, `P1`, or `P2`.

`status`: `blocking`, `watch`, `open`, or `resolved`.

`summary`: one sentence explaining the issue.

`evidence`: short evidence anchors, not raw private text.

`risk`: one sentence explaining the risk if unresolved.

Rules:

Do not include long reviewer quotes.

Do not include paper title, author names, local paths, submission IDs, or private process notes.

If evidence is missing, write `needs evidence` instead of inventing a table or appendix.
