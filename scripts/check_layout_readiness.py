#!/usr/bin/env python3
"""Audit one-page rebuttal layout fullness and column balance."""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}


@dataclass
class Finding:
    severity: str
    code: str
    message: str


@dataclass
class LayoutMetrics:
    page_width: float
    page_height: float
    left_max_y: float
    right_max_y: float
    max_y: float
    word_count: int = 0


KEY_VALUE_RE = re.compile(r"([A-Za-z_]+)\s*=\s*([0-9.]+)")


def parse_metrics_text(path: Path) -> LayoutMetrics:
    values: dict[str, float] = {}
    for key, value in KEY_VALUE_RE.findall(path.read_text(encoding="utf-8", errors="replace")):
        values[key.lower()] = float(value)
    required = ["page_width", "page_height", "left_max_y", "right_max_y", "max_y"]
    missing = [key for key in required if key not in values]
    if missing:
        raise ValueError("metrics file missing keys: " + ", ".join(missing))
    return LayoutMetrics(
        page_width=values["page_width"],
        page_height=values["page_height"],
        left_max_y=values["left_max_y"],
        right_max_y=values["right_max_y"],
        max_y=values["max_y"],
        word_count=int(values.get("word_count", 0)),
    )


def pdf_page_count(path: Path) -> int | None:
    try:
        proc = subprocess.run(["pdfinfo", str(path)], check=False, text=True, capture_output=True)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    match = re.search(r"^Pages:\s+(\d+)", proc.stdout, re.M)
    return int(match.group(1)) if match else None


def parse_pdf_bbox(path: Path) -> LayoutMetrics:
    page_count = pdf_page_count(path)
    if page_count is not None and page_count != 1:
        raise ValueError(f"expected one-page PDF for layout readiness, got {page_count} pages")
    try:
        proc = subprocess.run(
            ["pdftotext", "-bbox-layout", "-f", "1", "-l", "1", str(path), "-"],
            check=True,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ValueError("pdftotext is required for PDF layout readiness checks") from exc
    root = ET.fromstring(proc.stdout)
    page = next((elem for elem in root.iter() if elem.tag.endswith("page")), None)
    if page is None:
        raise ValueError("pdftotext output did not contain a page element")
    page_width = float(page.attrib.get("width", "0"))
    page_height = float(page.attrib.get("height", "0"))
    midpoint = page_width / 2.0
    left_max = 0.0
    right_max = 0.0
    max_y = 0.0
    word_count = 0
    for word in root.iter():
        if not word.tag.endswith("word"):
            continue
        text = (word.text or "").strip()
        if not text:
            continue
        try:
            x_min = float(word.attrib["xMin"])
            x_max = float(word.attrib["xMax"])
            y_max = float(word.attrib["yMax"])
        except (KeyError, ValueError):
            continue
        x_center = (x_min + x_max) / 2.0
        if x_center < midpoint:
            left_max = max(left_max, y_max)
        else:
            right_max = max(right_max, y_max)
        max_y = max(max_y, y_max)
        word_count += 1
    return LayoutMetrics(page_width, page_height, left_max, right_max, max_y, word_count)


def load_metrics(path: Path) -> LayoutMetrics:
    if path.suffix.lower() == ".pdf":
        return parse_pdf_bbox(path)
    return parse_metrics_text(path)


def check_layout(metrics: LayoutMetrics, min_fill: float, column_delta_warn: float, column_delta_fail: float) -> list[Finding]:
    findings: list[Finding] = []
    fill_ratio = metrics.max_y / metrics.page_height if metrics.page_height else 0.0
    delta = abs(metrics.left_max_y - metrics.right_max_y)
    lower_side = "right" if metrics.right_max_y < metrics.left_max_y else "left"

    if fill_ratio < min_fill:
        findings.append(
            Finding(
                "P1",
                "large-lower-page-blank",
                f"page text reaches only {fill_ratio:.2f} of page height; inspect for unfinished-looking lower-page whitespace",
            )
        )

    if delta >= column_delta_fail:
        findings.append(
            Finding(
                "P1",
                "severe-column-imbalance",
                f"column bottoms differ by {delta:.1f}pt; the {lower_side} column may look accidentally empty",
            )
        )
    elif delta >= column_delta_warn:
        findings.append(
            Finding(
                "P2",
                "column-imbalance",
                f"column bottoms differ by {delta:.1f}pt; consider safe spacing/title/table-placement adjustments if the blank looks unintentional",
            )
        )

    if metrics.word_count and metrics.word_count < 120:
        findings.append(
            Finding(
                "P2",
                "very-low-word-density",
                f"only {metrics.word_count} extracted words on the page; confirm the response does not look underdeveloped",
            )
        )

    return findings


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    if fail_on == "none":
        return False
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="PDF or key=value metrics fixture")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    parser.add_argument("--min-fill", type=float, default=0.78)
    parser.add_argument("--column-delta-warn", type=float, default=120.0)
    parser.add_argument("--column-delta-fail", type=float, default=220.0)
    args = parser.parse_args()

    metrics = load_metrics(args.path)
    findings = check_layout(metrics, args.min_fill, args.column_delta_warn, args.column_delta_fail)
    summary = (
        f"fill={metrics.max_y / metrics.page_height if metrics.page_height else 0:.2f} "
        f"left_bottom={metrics.left_max_y:.1f} right_bottom={metrics.right_max_y:.1f} "
        f"delta={abs(metrics.left_max_y - metrics.right_max_y):.1f} words={metrics.word_count}"
    )
    if findings:
        print(f"LAYOUT_READINESS_FINDINGS {summary}")
        for finding in findings:
            print(f"{finding.severity}\t{finding.code}\t{finding.message}")
        print("SUGGESTION\tPrefer title/spacing/table-placement adjustments; do not add weak filler just to occupy blank space.")
    else:
        print(f"LAYOUT_READINESS_OK {summary}")
    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
