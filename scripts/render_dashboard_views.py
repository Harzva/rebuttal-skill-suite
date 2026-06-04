#!/usr/bin/env python3
"""Render anonymized SVG dashboard previews from the webview demo data."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "webview" / "sample_dashboard_data.json"
OUT = ROOT / "docs" / "images"

STYLE = """
  <style>
    .bg{fill:#f7f3e8}.grid{stroke:#d9ded8;stroke-width:1;opacity:.45}.panel{fill:#fffdf7;stroke:#d7dde5;stroke-width:1}.ink{fill:#071324}.muted{fill:#647084}.green{fill:#16a34a}.red{fill:#ef4444}.orange{fill:#f97316}.amber{fill:#f59e0b}.blue{fill:#1479ff}.teal{fill:#00a88f}.soft-green{fill:#dcfce7}.soft-red{fill:#fee2e2}.soft-orange{fill:#ffedd5}.soft-amber{fill:#fef3c7}.soft-blue{fill:#dbeafe}.line{stroke:#d7dde5;stroke-width:1}.shadow{filter:drop-shadow(0 8px 12px rgba(15,23,42,.12))}
    text{font-family:Avenir Next,Trebuchet MS,Arial,sans-serif}.title{font-size:30px;font-weight:900}.h{font-size:17px;font-weight:900}.body{font-size:13px}.small{font-size:11px;font-weight:800}.stat{font-size:28px;font-weight:900}.tiny{font-size:10px;font-weight:800}
  </style>
"""


def e(value: object) -> str:
    return escape(str(value), quote=True)


def pill(x: int, y: int, w: int, label: str, bg: str = "soft-blue", fg: str = "blue") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="12" class="{bg}"/><text x="{x + 10}" y="{y + 16}" class="small {fg}">{e(label)}</text>'


def base(title: str, subtitle: str, body: str) -> str:
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="760" class="grid"/>' for x in range(0, 1201, 28))
    grid += "".join(f'<line x1="0" y1="{y}" x2="1200" y2="{y}" class="grid"/>' for y in range(0, 761, 28))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760">
  {STYLE}
  <rect width="1200" height="760" class="bg"/>{grid}
  <text x="36" y="48" class="title ink">{e(title)}</text>
  <text x="36" y="74" class="body muted">{e(subtitle)}</text>
  {body}
</svg>
'''


def stats(data: dict, x0: int = 36, y: int = 104) -> str:
    s = data["summary"]
    items = [("Issues", s["issues_total"], "ink"), ("Resolved", s["resolved"], "green"), ("Open", s["open"], "ink"), ("P0 Blocking", s["p0_blocking"], "red"), ("Avg Score", f'{s["score"]}/100', "amber")]
    out = []
    for i, (label, value, cls) in enumerate(items):
        x = x0 + i * 226
        out.append(f'<rect x="{x}" y="{y}" width="206" height="82" rx="14" class="panel shadow"/>')
        out.append(f'<text x="{x+16}" y="{y+38}" class="stat {cls}">{e(value)}</text>')
        out.append(f'<text x="{x+16}" y="{y+62}" class="small muted">{e(label)}</text>')
    return "\n  ".join(out)


def issue_card(x: int, y: int, issue: dict) -> str:
    sev = issue["severity"]
    bg, fg = ("soft-red", "red") if sev == "P0" else ("soft-orange", "orange") if sev == "P1" else ("soft-amber", "amber")
    return f'''<rect x="{x}" y="{y}" width="246" height="94" rx="10" class="panel"/>
  <text x="{x+12}" y="{y+24}" class="small ink">{e(issue["title"][:28])}</text>
  <text x="{x+12}" y="{y+44}" class="tiny muted">{e(issue["id"])} · {e(issue["theme"])}</text>
  {pill(x+12, y+56, 42, sev, bg, fg)}{pill(x+62, y+56, 70, issue["status"], "soft-blue", "blue")}'''


def overview(data: dict) -> str:
    issues = data["issues"]
    lanes = [("P0 阻塞", "P0"), ("P1 高风险", "P1"), ("P2 中风险", "P2"), ("已解决", "resolved")]
    body = [stats(data)]
    body.append('<rect x="36" y="220" width="1128" height="356" rx="18" class="panel shadow"/>')
    body.append('<text x="58" y="258" class="h ink">Issue Board（按风险）</text>')
    for i, (label, key) in enumerate(lanes):
        x = 58 + i * 274
        body.append(f'<rect x="{x}" y="282" width="260" height="250" rx="14" fill="{"#fff1f1" if key == "P0" else "#fff7ed" if key == "P1" else "#fefce8" if key == "P2" else "#ecfdf5"}" stroke="#d7dde5"/>')
        cards = [issue for issue in issues if (issue["severity"] == key and issue["status"] != "resolved") or (key == "resolved" and issue["status"] == "resolved")]
        body.append(f'<text x="{x+12}" y="{282+24}" class="small ink">{e(label)} ({len(cards)})</text>')
        for j, issue in enumerate(cards[:2]):
            body.append(issue_card(x+12, 318 + j * 104, issue))
    body.append('<rect x="36" y="612" width="1128" height="76" rx="16" class="panel shadow"/>')
    body.append('<text x="58" y="648" class="h ink">README Screenshot Contract</text>')
    body.append('<text x="58" y="672" class="body muted">Generated from webview/sample_dashboard_data.json so public previews match the shipped static dashboard modules.</text>')
    return base("Dashboard Preview: Overview", data["subtitle"], "\n  ".join(body))


def issue_board(data: dict) -> str:
    body = [stats(data, y=100)]
    for i, issue in enumerate(data["issues"][:8]):
        x = 36 + (i % 2) * 582
        y = 220 + (i // 2) * 132
        body.append(f'<rect x="{x}" y="{y}" width="546" height="112" rx="14" class="panel shadow"/>')
        body.append(f'<text x="{x+18}" y="{y+30}" class="h ink">{e(issue["id"])} · {e(issue["title"])}</text>')
        body.append(f'<text x="{x+18}" y="{y+56}" class="body muted">{e(issue["summary"][:82])}</text>')
        body.append(pill(x+18, y+72, 42, issue["severity"], "soft-red" if issue["severity"] == "P0" else "soft-orange" if issue["severity"] == "P1" else "soft-amber", "red" if issue["severity"] == "P0" else "orange" if issue["severity"] == "P1" else "amber"))
        body.append(pill(x+68, y+72, 76, issue["status"], "soft-blue", "blue"))
    return base("Dashboard Preview: Issue Board", "Reviewer concerns are grouped by severity, evidence, status, and risk boundary.", "\n  ".join(body))


def reviewer_map(data: dict) -> str:
    body = ['<rect x="36" y="116" width="1128" height="520" rx="18" class="panel shadow"/>', '<text x="58" y="154" class="h ink">Reviewer Coverage Map</text>']
    for i, reviewer in enumerate(data["reviewers"]):
        y = 192 + i * 104
        body.append(f'<circle cx="78" cy="{y+24}" r="24" fill="#d1fae5" stroke="#6ee7b7" stroke-width="3"/><text x="78" y="{y+30}" text-anchor="middle" class="small green">{e(reviewer["id"])}</text>')
        body.append(f'<text x="118" y="{y+16}" class="h ink">{e(reviewer["stance"])}</text>')
        body.append(f'<text x="118" y="{y+40}" class="body muted">{e(" · ".join(reviewer["concerns"]))}</text>')
        body.append(f'<rect x="118" y="{y+56}" width="760" height="10" rx="5" fill="#e5e7eb"/><rect x="118" y="{y+56}" width="{int(760 * reviewer["coverage"] / 100)}" height="10" rx="5" fill="#00a88f"/>')
        body.append(f'<text x="910" y="{y+64}" class="h green">{reviewer["coverage"]}%</text>')
        body.append(f'<text x="1000" y="{y+64}" class="small muted">{e(", ".join(reviewer["anchors"]))}</text>')
    body.append('<text x="58" y="690" class="body muted">Reviewer IDs are anonymized; coverage means concerns have visible response anchors.</text>')
    return base("Dashboard Preview: Reviewer Map", "A compact matrix checks whether each reviewer has response anchors.", "\n  ".join(body))


def risk_gates(data: dict) -> str:
    rows = data["risk_history"]
    keys = [("P0", "#ef4444"), ("P1", "#f97316"), ("P2", "#f59e0b"), ("resolved", "#16a34a")]
    max_v = max(row[key] for row in rows for key, _ in keys)
    x0, y0, w, h = 64, 156, 620, 300
    def x(i: int) -> float: return x0 + i * w / (len(rows) - 1)
    def y(v: int) -> float: return y0 + h - v * h / max_v
    body = ['<rect x="36" y="112" width="708" height="430" rx="18" class="panel shadow"/>', '<text x="58" y="150" class="h ink">Risk Trend（近 7 天）</text>', f'<line x1="{x0}" y1="{y0+h}" x2="{x0+w}" y2="{y0+h}" class="line"/>', f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0+h}" class="line"/>']
    for key, color in keys:
        pts = " ".join(f'{x(i):.1f},{y(row[key]):.1f}' for i, row in enumerate(rows))
        body.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="4"/>')
        for i, row in enumerate(rows):
            body.append(f'<circle cx="{x(i):.1f}" cy="{y(row[key]):.1f}" r="4" fill="{color}"/>')
    for i, row in enumerate(rows):
        body.append(f'<text x="{x(i):.1f}" y="500" text-anchor="middle" class="tiny muted">{e(row["date"])}</text>')
    body.append('<text x="58" y="526" class="body muted">Anonymized demo trend; not live telemetry.</text>')
    body.append('<rect x="776" y="112" width="388" height="430" rx="18" class="panel shadow"/>')
    body.append('<text x="800" y="150" class="h ink">Gates 状态</text>')
    for i, gate in enumerate(data["gate_runs"][:8]):
        yrow = 184 + i * 42
        cls = "soft-green" if gate["result"] == "pass" else "soft-amber"
        fg = "green" if gate["result"] == "pass" else "amber"
        body.append(f'<text x="800" y="{yrow}" class="body ink">{e(gate["gate"])}</text>')
        body.append(pill(1060, yrow-18, 68, gate["result"].upper(), cls, fg))
    return base("Dashboard Preview: Risk & Gates", "Trend, gate status, and report previews are real modules in the static webview.", "\n  ".join(body))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    files = {
        "dashboard-overview.svg": overview(data),
        "dashboard-issue-board.svg": issue_board(data),
        "dashboard-reviewer-map.svg": reviewer_map(data),
        "dashboard-risk-gates.svg": risk_gates(data),
    }
    for name, svg in files.items():
        path = OUT / name
        path.write_text(svg, encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
