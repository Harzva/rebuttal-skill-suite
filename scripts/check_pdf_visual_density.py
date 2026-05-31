#!/usr/bin/env python3
"""Estimate whether a rendered PDF page looks visually crowded.

This is a screenshot-style heuristic. It rasterizes the first PDF page when
pdftoppm is available, or reads a small metrics fixture with key=value lines.
It should support visual inspection, not replace it.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


SEVERITY_ORDER = {"P0": 3, "P1": 2, "P2": 1, "OK": 0}


@dataclass
class Metrics:
    source: str
    width: int = 0
    height: int = 0
    mean_density: float = 0.0
    max_band_density: float = 0.0
    dense_band_count: int = 0
    band_count: int = 0


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def parse_metrics_fixture(path: Path) -> Metrics:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return Metrics(
        source="fixture",
        width=int(float(values.get("width", 0))),
        height=int(float(values.get("height", 0))),
        mean_density=float(values.get("mean_density", 0.0)),
        max_band_density=float(values.get("max_band_density", 0.0)),
        dense_band_count=int(float(values.get("dense_band_count", 0))),
        band_count=int(float(values.get("band_count", 0))),
    )


def read_pnm_tokens(data: bytes):
    index = 0
    length = len(data)

    def next_token() -> bytes:
        nonlocal index
        while index < length and data[index] in b" \t\r\n":
            index += 1
        if index < length and data[index:index + 1] == b"#":
            while index < length and data[index:index + 1] not in b"\r\n":
                index += 1
            return next_token()
        start = index
        while index < length and data[index] not in b" \t\r\n":
            index += 1
        return data[start:index]

    magic = next_token()
    width = int(next_token())
    height = int(next_token())
    maxval = int(next_token())
    while index < length and data[index] in b" \t\r\n":
        index += 1
    return magic, width, height, maxval, data[index:]


def parse_pgm(path: Path, dark_threshold: int, band_height: int) -> Metrics:
    data = path.read_bytes()
    magic, width, height, maxval, pixels = read_pnm_tokens(data)
    if magic not in {b"P5", b"P2"}:
        raise ValueError(f"unsupported image format {magic!r}; expected PGM P5/P2")
    if magic == b"P2":
        raw_values = [int(x) for x in re.findall(rb"\d+", pixels)]
    elif maxval > 255:
        raw_values = [int.from_bytes(pixels[i:i + 2], "big") for i in range(0, len(pixels), 2)]
    else:
        raw_values = list(pixels[: width * height])
    expected = width * height
    values = raw_values[:expected]
    if len(values) < expected:
        values.extend([maxval] * (expected - len(values)))
    scaled_threshold = dark_threshold / 255.0 * maxval
    dark = [1 if value <= scaled_threshold else 0 for value in values]
    mean_density = sum(dark) / max(1, len(dark))
    band_densities: list[float] = []
    for top in range(0, height, band_height):
        bottom = min(height, top + band_height)
        segment = dark[top * width: bottom * width]
        if segment:
            band_densities.append(sum(segment) / len(segment))
    dense_band_count = sum(1 for value in band_densities if value >= 0.18)
    return Metrics(
        source="raster",
        width=width,
        height=height,
        mean_density=mean_density,
        max_band_density=max(band_densities or [0.0]),
        dense_band_count=dense_band_count,
        band_count=len(band_densities),
    )


def rasterize_pdf(path: Path, dpi: int, dark_threshold: int, band_height: int) -> Metrics:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("pdftoppm is not available; pass a metrics fixture instead")
    with tempfile.TemporaryDirectory(prefix="visual_density_") as tmp:
        prefix = Path(tmp) / "page"
        subprocess.run(
            ["pdftoppm", "-f", "1", "-singlefile", "-r", str(dpi), "-gray", str(path), str(prefix)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return parse_pgm(prefix.with_suffix(".pgm"), dark_threshold=dark_threshold, band_height=band_height)


def evaluate(metrics: Metrics, warn_band: float, severe_band: float, mean_warn: float, dense_bands_warn: int) -> list[Finding]:
    findings: list[Finding] = []
    if metrics.max_band_density >= severe_band:
        findings.append(
            Finding(
                "P1",
                "severe-visual-crowding",
                f"max dark-pixel band density {metrics.max_band_density:.3f} suggests a table or paragraph block may be visually collapsed",
            )
        )
    elif metrics.max_band_density >= warn_band:
        findings.append(
            Finding(
                "P2",
                "dense-visual-band",
                f"max dark-pixel band density {metrics.max_band_density:.3f} merits visual inspection of compact tables",
            )
        )
    if metrics.mean_density >= mean_warn:
        findings.append(
            Finding("P2", "high-page-ink", f"mean page density {metrics.mean_density:.3f} is high for a one-page response")
        )
    if metrics.dense_band_count >= dense_bands_warn:
        findings.append(
            Finding("P2", "many-dense-bands", f"{metrics.dense_band_count} bands exceed the dense-band heuristic")
        )
    return findings


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_ORDER[fail_on]
    return any(SEVERITY_ORDER[f.severity] >= threshold for f in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="PDF file or key=value metrics fixture.")
    parser.add_argument("--dpi", type=int, default=120)
    parser.add_argument("--band-height", type=int, default=24)
    parser.add_argument("--dark-threshold", type=int, default=220)
    parser.add_argument("--warn-band-density", type=float, default=0.22)
    parser.add_argument("--severe-band-density", type=float, default=0.32)
    parser.add_argument("--mean-density-warn", type=float, default=0.09)
    parser.add_argument("--dense-bands-warn", type=int, default=8)
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2"], default="P1")
    args = parser.parse_args()

    try:
        if args.input.suffix.lower() == ".pdf":
            metrics = rasterize_pdf(args.input, args.dpi, args.dark_threshold, args.band_height)
        else:
            metrics = parse_metrics_fixture(args.input)
    except Exception as exc:  # pragma: no cover - intentionally surfaced in CLI output
        print(f"P1\tvisual-density-unavailable\t{exc}")
        return 1 if SEVERITY_ORDER[args.fail_on] <= SEVERITY_ORDER["P1"] else 0

    findings = evaluate(
        metrics,
        warn_band=args.warn_band_density,
        severe_band=args.severe_band_density,
        mean_warn=args.mean_density_warn,
        dense_bands_warn=args.dense_bands_warn,
    )
    print(
        "METRICS\t"
        f"source={metrics.source}\twidth={metrics.width}\theight={metrics.height}\t"
        f"mean_density={metrics.mean_density:.3f}\tmax_band_density={metrics.max_band_density:.3f}\t"
        f"dense_band_count={metrics.dense_band_count}\tband_count={metrics.band_count}"
    )
    if findings:
        for finding in findings:
            print(f"{finding.severity}\t{finding.code}\t{finding.message}")
    else:
        print("OK\tvisual-density\tno dense screenshot bands exceeded configured thresholds")
    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
