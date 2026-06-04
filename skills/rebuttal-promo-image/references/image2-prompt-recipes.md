# Image2 Prompt Recipes

Use these prompts when turning GitHub/web screenshots into polished README and Xiaohongshu promo images.

## Source Screenshot Checklist

Use 2-5 screenshots when available:

- GitHub README first viewport.
- A clean screenshot of the workflow diagram or feature table.
- A sanitized validation output panel showing status labels, not raw paths.
- A screenshot of example fixtures or public documentation.

Crop out browser bookmarks, local usernames, private paths, tokens, account avatars, and unrelated tabs.

## README Horizontal Prompt

```text
Create a 1600x900 GitHub README promotional banner based on the provided public screenshots.

Subject: Rebuttal Skill Suite, a Codex skill suite for academic rebuttal audit loops.
Main Chinese headline: 把学术 Rebuttal 变成可验证闭环
Repository slug: Harzva/rebuttal-skill-suite
Subtitle: 审稿人格 + 泄漏审计 + 证据门禁 + 发布校验

Visual style: warm off-white background, bold black headline, compact original document/review icon, gradient repository slug, four rounded feature cards, screenshot-like proof panel, blue/green/yellow/purple/pink accents. Keep the composition clean and product-like, inspired by Xiaohongshu developer-tool infographics but not copying any reference image.

Strict layout safety: keep all text fully inside its box with generous padding. No underline, decorative stroke, neon ring, icon, divider, chart, or screenshot element may overlap any text. Yellow underline sits below the headline baseline with clear vertical padding. Shorten text instead of shrinking it below readability.
```

## Xiaohongshu Vertical Prompt

```text
Create a 1242x1660 vertical Xiaohongshu cover card based on the provided public GitHub screenshots.

Subject: Rebuttal Skill Suite.
Main Chinese headline: 投稿回复 先过一轮审稿
Repository slug: rebuttal-skill-suite
Subtitle: 把作者回复变成 P0 / P1 / P2 闭环
Feature cards: 高危先拦, 审稿人格, 机械门禁, 版面就绪
Proof panel labels: SUITE_VALIDATE_OK, 泄漏审计, 证据一致, 语气收敛, 发布打包
Bottom CTA: GitHub: Harzva/rebuttal-skill-suite

Visual style: bright warm-white developer infographic, bold black Chinese text, gradient repo slug, rounded white cards, colorful small icons, screenshot-like proof panels, clean GitHub CTA footer. Use the screenshots as factual inspiration, not as raw UI pasted into the poster.

Strict layout safety: every text box must have enough padding; no decoration crosses text; no card text clips; no raw private paths; no fake statistics or acceptance claims.
```

## Regeneration Temperature

Use this sequence when the first generated image is close but flawed:

1. Text overlap or clipping: shorten copy by 30-50%, increase whitespace, remove one decorative element.
2. Too generic: add exact repo slug, exact feature labels, and one screenshot-like proof panel.
3. Too noisy: remove confetti, reduce icon count, keep only four feature cards.
4. Too much like a raw screenshot: ask for "screenshot-like proof panels, not pasted screenshots".
5. Too much like a copied reference: change layout rhythm, icon shape, and headline while preserving the big-hook/card/proof/CTA structure.

Reject an image instead of using it if the headline, repo slug, feature labels, or CTA are unreadable at mobile width.
