#!/usr/bin/env python3
"""Render anonymized SVG dashboard previews for README documentation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "images"


STYLE = """
  <style>
    .bg{fill:#f5f6f8}.panel{fill:#fff;stroke:#d7dde5;stroke-width:1}
    .ink{fill:#202833}.muted{fill:#657180}.green{fill:#0b6b3a}.red{fill:#9b1c1c}.blue{fill:#245d8f}.amber{fill:#8a5a00}
    .soft-green{fill:#e8f4ee}.soft-red{fill:#f7e5e5}.soft-blue{fill:#e9eff7}.soft-amber{fill:#fff4d6}.line{stroke:#d7dde5;stroke-width:1}
    text{font-family:Inter,Arial,sans-serif}.title{font-size:26px;font-weight:800}.h{font-size:16px;font-weight:800}.body{font-size:13px}.small{font-size:11px;font-weight:700}.stat{font-size:24px;font-weight:900}
  </style>
"""


def pill(x: int, y: int, w: int, label: str, cls: str = "soft-blue", text_cls: str = "blue") -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="12" class="{cls}"/>'
        f'<text x="{x + 10}" y="{y + 16}" class="small {text_cls}">{label}</text>'
    )


def frame(title: str, subtitle: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
  {STYLE}
  <rect width="1200" height="760" class="bg"/>
  <text x="36" y="48" class="title ink">{title}</text>
  <text x="36" y="72" class="body muted">{subtitle}</text>
  <line x1="36" y1="96" x2="1164" y2="96" class="line"/>
  {body}
</svg>
"""


def overview() -> str:
    stats = [
        ("4", "Reviewers"),
        ("6", "Issue Cards"),
        ("0", "P0 Open"),
        ("2", "P1 Watch"),
    ]
    chunks = []
    for i, (value, label) in enumerate(stats):
        x = 36 + i * 286
        chunks.append(f'<rect x="{x}" y="122" width="260" height="92" rx="8" class="panel"/>')
        chunks.append(f'<text x="{x + 18}" y="166" class="stat ink">{value}</text>')
        chunks.append(f'<text x="{x + 18}" y="190" class="small muted">{label}</text>')
    chunks.extend([
        '<rect x="36" y="244" width="545" height="270" rx="8" class="panel"/>',
        '<text x="58" y="282" class="h ink">Gate Timeline</text>',
        pill(58, 306, 88, "Leak pass", "soft-green", "green"),
        pill(160, 306, 102, "Claims pass", "soft-green", "green"),
        pill(276, 306, 112, "Numbers pass", "soft-green", "green"),
        pill(402, 306, 92, "Layout watch", "soft-amber", "amber"),
        '<line x1="58" y1="362" x2="540" y2="362" class="line"/>',
        '<text x="58" y="398" class="body ink">The dashboard is advisory: it visualizes gate outputs and issue coverage.</text>',
        '<text x="58" y="424" class="body muted">It does not replace claim, number, leak, or layout checks.</text>',
        '<rect x="615" y="244" width="549" height="270" rx="8" class="panel"/>',
        '<text x="637" y="282" class="h ink">Coverage Summary</text>',
        '<text x="637" y="326" class="body ink">R1: protocol clarity and table semantics covered.</text>',
        '<text x="637" y="358" class="body ink">R2: attribution, cost, and baseline-family evidence covered.</text>',
        '<text x="637" y="390" class="body ink">R3: weak cases and deployment boundaries covered.</text>',
        '<text x="637" y="422" class="body ink">R4: revision-map and wording auditability covered.</text>',
        '<text x="637" y="468" class="body muted">All labels and numbers here are anonymized examples.</text>',
        '<rect x="36" y="548" width="1128" height="108" rx="8" class="panel"/>',
        '<text x="58" y="586" class="h ink">Sanitization Contract</text>',
        '<text x="58" y="620" class="body ink">Use reviewer IDs like R1/R2/R3/R4, method placeholders, and generic metric names in public demos.</text>',
    ])
    return frame("Dashboard Preview: Overview", "Anonymous demo data; no paper names, local paths, or real reviewer IDs.", "\n  ".join(chunks))


def issue_board() -> str:
    cards = [
        ("I1", "Protocol Separation", "P0", "answered", "Separate deployable claims from calibrated diagnostics.", "Do not cite calibrated rows as no-label evidence."),
        ("I2", "Mechanism Attribution", "P1", "answered", "Show same-model baseline, verifier-only row, and routed row.", "Do not overclaim compute-identical fairness."),
        ("I3", "Cost Evidence", "P1", "watch", "Report memory class, latency baseline, and route ratio.", "Avoid universal speedup language."),
        ("I4", "Weak Cases", "P1", "answered", "Diagnose routing, prompt, and prior-reliability boundaries.", "Do not invent new evidence."),
    ]
    chunks = []
    for i, card in enumerate(cards):
        x = 36 + (i % 2) * 582
        y = 128 + (i // 2) * 232
        issue_id, title, sev, status, summary, risk = card
        chunks.append(f'<rect x="{x}" y="{y}" width="546" height="200" rx="8" class="panel"/>')
        chunks.append(f'<text x="{x + 20}" y="{y + 36}" class="h ink">{issue_id}: {title}</text>')
        chunks.append(pill(x + 20, y + 54, 54, sev, "soft-red" if sev == "P0" else "soft-blue", "red" if sev == "P0" else "blue"))
        chunks.append(pill(x + 84, y + 54, 92, status, "soft-green" if status == "answered" else "soft-amber", "green" if status == "answered" else "amber"))
        chunks.append(f'<text x="{x + 20}" y="{y + 112}" class="body ink">{summary}</text>')
        chunks.append(f'<text x="{x + 20}" y="{y + 152}" class="body muted">Risk: {risk}</text>')
    return frame("Dashboard Preview: Issue Board", "Each card maps reviewer concerns to evidence and risk boundaries.", "\n  ".join(chunks))


def reviewer_map() -> str:
    rows = [
        ("R1", "supportive", "I1, I5, I6", "Protocol and table semantics"),
        ("R2", "skeptical", "I1, I2, I3, I5, I6", "Attribution, cost, and baseline-family evidence"),
        ("R3", "concerned", "I3, I4, I5, I6", "Weak cases and deployment boundaries"),
        ("R4", "supportive", "I5, I6", "Revision map and final wording auditability"),
    ]
    chunks = [
        '<rect x="36" y="124" width="1128" height="470" rx="8" class="panel"/>',
        '<text x="58" y="164" class="h ink">Reviewer-Issue Matrix</text>',
        '<line x1="58" y1="188" x2="1142" y2="188" class="line"/>',
        '<text x="58" y="224" class="small muted">Reviewer</text>',
        '<text x="230" y="224" class="small muted">Stance</text>',
        '<text x="430" y="224" class="small muted">Anchors</text>',
        '<text x="680" y="224" class="small muted">Concern Cluster</text>',
    ]
    for i, (rid, stance, anchors, concern) in enumerate(rows):
        y = 252 + i * 78
        chunks.append(f'<line x1="58" y1="{y - 32}" x2="1142" y2="{y - 32}" class="line"/>')
        chunks.append(f'<text x="58" y="{y}" class="h ink">{rid}</text>')
        chunks.append(pill(230, y - 20, 112, stance, "soft-blue", "blue"))
        chunks.append(f'<text x="430" y="{y}" class="body ink">{anchors}</text>')
        chunks.append(f'<text x="680" y="{y}" class="body ink">{concern}</text>')
    chunks.extend([
        '<rect x="36" y="626" width="1128" height="72" rx="8" class="panel"/>',
        '<text x="58" y="668" class="body muted">Public README previews should use anonymized IDs and generic concern clusters.</text>',
    ])
    return frame("Dashboard Preview: Reviewer Map", "A compact matrix checks whether each reviewer has visible response anchors.", "\n  ".join(chunks))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "dashboard-overview.svg": overview(),
        "dashboard-issue-board.svg": issue_board(),
        "dashboard-reviewer-map.svg": reviewer_map(),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT / name}")


if __name__ == "__main__":
    main()
