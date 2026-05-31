---
name: rebuttal-leak-audit
description: Audit academic rebuttals, author responses, LaTeX/PDF text, Markdown drafts, and OpenReview replies for leaked internal/developer notes, local paths, tool traces, private experiment logistics, advisor or AI feedback traces, non-reviewer-facing remarks, and wording that should be rewritten before showing reviewers or ACs. Use when checking whether rebuttal content accidentally exposes Codex/ChatGPT/Claude notes, teacher/advisor comments, TODOs, logs, shell commands, filesystem paths, “AC-facing” meta-language, draft-only reasoning, or score-strategy language.
---

# Rebuttal Leak Audit

## Workflow

1. Identify the public artifact to audit, usually `rebuttal.tex`, reviewer reply `.md` files, or pasted response text.
2. Run `scripts/audit_rebuttal_leaks.py` on the file or directory when local files are available.
3. Read flagged lines in context and classify each as:
   - `Remove`: private implementation detail, local path, tool output, TODO, internal comment, or non-public note.
   - `Rewrite`: useful point expressed in internal language; convert to reviewer-facing prose.
   - `Keep`: false positive or acceptable public wording.
4. Check audience alignment even if the script finds nothing.
5. Report findings with file/line references, severity, and exact replacement guidance.

## Closed-Loop Gate Placement

Run this audit at three points in an adversarial rebuttal loop:

1. Before reviewer-persona critique, so personas do not optimize text that should be deleted.
2. After each patch, because local paths, tool outputs, and strategy language often enter during fast iteration.
3. Before final submission, paired with PDF layout and reviewer-coverage checks.
4. Before pasting into a platform text box, because copy/paste versions can expose placeholders, local Markdown links, or LaTeX-only commands that were invisible in the rendered PDF.

Treat any high-risk leak as a blocking P0 issue. Do not balance it against content gains; remove or rewrite it first.

## What To Flag

Treat these as high-risk leakage in a reviewer/AC-facing response:

- Absolute or user-specific paths: `/home/...`, `/Users/...`, `/tmp/...`, drive letters, `.sock`, local output folders.
- Tool/process traces: `Ran`, `Running command`, `tmux`, `nvidia-smi`, `sleep`, `tail`, `pdflatex log`, raw shell output, shard/partial status.
- AI/developer traces: `Codex`, `ChatGPT`, `Claude`, `Opus`, `developer`, `system prompt`, `tool call`, `IDE setup`, `open tabs`.
- Advisor/internal traces: `teacher`, `advisor`, `PI suggested`, draft-only comments, or non-public Chinese notes such as `老师`, `备注`, `改分`.
- Meta-audience wording: `AC-facing`, `reviewer-specific`, `triage`, `borderline expert`, `score increase`, or any phrasing that explains persuasion strategy rather than substance.
- Private experiment logistics: raw log paths, output directories, server readiness, cache stages, merge stages, failed dataset files, local backup names.
- Informal uncertainty: `probably`, `maybe`, `I think`, `not sure`, unless rewritten as a formal limitation or assumption.

## Reviewer-Facing Rewrite Rules

Convert internal logistics into public evidence:

- Replace local paths with artifact names, appendix references, or anonymous repository references.
- Replace `we ran X and logs are at Y` with `We will report the completed run and its resulting accuracy in Appendix A.`
- Replace `AC-facing map` with `Revision map` or `Protocol summary`.
- Replace `the dangerous reviewer` with `the protocol and cost concerns`.
- Replace advisor or AI attribution with no attribution; just state the improved scientific point.
- Keep only evidence reviewers can evaluate from the rebuttal, paper, supplement, or anonymized repository.
- Replace vague private-task language such as `fix later` or `add more experiments` with a bounded reviewer-facing revision promise that names the table, caption, appendix, artifact, or paper location.

## Output Format

Start with the most severe leaks. For each issue, include:

- Severity: `High`, `Medium`, or `Low`
- Location: clickable file path and line number when available
- Problem: why this is not reviewer-facing
- Fix: delete or replacement text

End with a short readiness statement:

- `Ready`: no public-facing leaks found.
- `Needs cleanup`: leaks remain, but fixes are straightforward.
- `Do not submit yet`: high-risk private notes or paths remain.

## Script

Use the bundled scanner:

```bash
python3 /root/.codex/skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py path/to/rebuttal.tex
python3 /root/.codex/skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py path/to/rebuttal-dir --ext .tex .md .txt
python3 /root/.codex/skills/rebuttal-leak-audit/scripts/audit_rebuttal_leaks.py path/to/rebuttal.tex --fail-on High
```

The script is a first pass only. Always review context before deciding whether a flag is real.
