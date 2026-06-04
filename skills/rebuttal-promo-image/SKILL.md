---
name: rebuttal-promo-image
description: Create public-safe GitHub README promo banners and Xiaohongshu vertical cards for academic rebuttal skill suites. Use when promoting rebuttal-skill-suite, turning GitHub/README/web screenshots into Image2-style marketing graphics, preparing Xiaohongshu copy, or logging Xiaohongshu publication evidence.
---

# Rebuttal Promo Image

Use this skill to promote a rebuttal workflow repository without inventing claims or leaking private paper context.

## Workflow

1. Read repository facts first: `README.md`, `VERSION`, `CHANGELOG.md`, scripts, skills, and release checklist.
2. Capture or collect public-safe evidence screenshots:
   - GitHub README first viewport;
   - validation output reduced to safe status labels such as `SUITE_VALIDATE_OK`;
   - public workflow diagrams, example fixtures, or sanitized UI panels.
3. Generate two assets:
   - README horizontal banner: `1600x900`, stored under `docs/readme-assets/`.
   - Xiaohongshu vertical card: `1242x1660`, stored under the local campaign workspace.
4. Add the horizontal banner near the README first viewport.
5. Prepare Xiaohongshu copy with one core promise, no fake metrics, and no private submission details.
6. Publish through Xiaohongshu MCP only after login check.
7. Record the note locally:
   - `D:\study\code\0ai\产品\09-wemedia\xiaohongshu\<campaign>\note.md`
   - append one JSON line to `D:\study\code\0ai\产品\09-wemedia\xiaohongshu\published-notes.jsonl`

## Visual Direction

Use a bright open-source infographic style:

- warm off-white background;
- bold black Chinese headline;
- gradient repository slug;
- rounded white feature cards;
- blue, green, yellow, purple, and pink accents;
- screenshot-like proof panels, not raw logs;
- GitHub callout at the bottom of the Xiaohongshu card.

Do not copy a reference poster. Reuse only the communication pattern: big hook, product identity, evidence panels, feature cards, and bottom CTA.

## Image2 Prompt Recipe

When using screenshots as references, read `references/image2-prompt-recipes.md`.

Core prompt shape:

```text
Create a clean Xiaohongshu/GitHub infographic poster based on the provided screenshots. Keep the real repository name and supported claims. Use a warm white background, bold black Chinese headline, gradient repo slug, rounded feature cards, screenshot-like proof panels, and a GitHub CTA. Strict layout safety: no underline, neon ring, icon, divider, or decorative stroke may overlap text. All text must stay fully inside boxes with generous padding.
```

## Public Safety

Never publish:

- raw reviewer comments, private paper titles, conference strategy, or score tactics;
- local paths, usernames, API keys, cookies, logs, or terminal prompts;
- unredacted screenshots from private submission systems;
- claims of acceptance, score improvement, benchmarks, stars, downloads, or official status unless there is public evidence.

Use neutral claims such as "helps audit", "checks", "flags", "prepares", and "validates". Avoid "guarantees acceptance" or "improves score".

## Xiaohongshu Copy Rules

Title: 20 Chinese characters or fewer.

Body:

1. Hook: the practical pain.
2. What it is: a GitHub skill suite for rebuttal review loops.
3. What it checks: leakage, evidence consistency, tone, reviewer coverage, layout readiness, and release packaging.
4. Safe CTA: tell readers to search/open the GitHub repository.

Tags: choose 5-8 from `论文写作`, `学术工具`, `GitHub`, `开源项目`, `AI工具`, `Codex`, `科研效率`, `小红书MCP`.

## Acceptance Gate

Before committing or publishing:

- README image path exists and renders at README width.
- Xiaohongshu image path is absolute and opens locally.
- No text is clipped, overlapped, or too small to read.
- README and note claims are backed by repository files.
- `scripts/validate_release_package.py .` and `scripts/validate_repo_clean.py .` pass.
- Local Xiaohongshu publication record is written after publish attempt.
