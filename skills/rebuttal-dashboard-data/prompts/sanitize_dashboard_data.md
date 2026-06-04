# Sanitize Dashboard Data

Transform private dashboard data into public demo data.

Required removals:

- Local filesystem paths.
- Real paper titles and project names.
- Author, lab, advisor, or institution identifiers.
- Real reviewer names or platform IDs.
- Submission IDs.
- Raw reviewer quotes longer than a short paraphrase.
- Private experiment logistics.
- AI, Codex, ChatGPT, teacher, advisor, or internal strategy traces unless the repository itself is about the tool.
- Exact project-specific metrics when they are not meant to be public.

Use generic replacements:

`Anonymized Rebuttal Project`

`Method A`

`Baseline B`

`R1/R2/R3/R4`

`ISS-001`

Keep the dashboard structure intact, but paraphrase risky content.
