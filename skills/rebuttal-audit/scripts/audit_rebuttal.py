#!/usr/bin/env python3
"""Mechanical audit for one-page academic rebuttals."""

from __future__ import annotations

import argparse
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path


class BBoxParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.words: list[dict[str, float | str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "word":
            return
        d = dict(attrs)
        try:
            self.words.append(
                {
                    "xmin": float(d["xmin"]),
                    "xmax": float(d["xmax"]),
                    "ymin": float(d["ymin"]),
                    "ymax": float(d["ymax"]),
                }
            )
        except Exception:
            pass


class BBoxLayoutParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.current_line = None
        self.in_word = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "line":
            try:
                self.current_line = {
                    "xmin": float(d["xmin"]),
                    "xmax": float(d["xmax"]),
                    "ymin": float(d["ymin"]),
                    "ymax": float(d["ymax"]),
                    "words": [],
                }
            except Exception:
                self.current_line = None
        elif tag == "word" and self.current_line is not None:
            self.in_word = True

    def handle_data(self, data):
        if self.in_word and self.current_line is not None:
            s = data.strip()
            if s:
                self.current_line["words"].append(s)

    def handle_endtag(self, tag):
        if tag == "word":
            self.in_word = False
        elif tag == "line" and self.current_line is not None:
            self.current_line["text"] = " ".join(self.current_line["words"])
            self.lines.append(self.current_line)
            self.current_line = None


def run(cmd):
    try:
        return subprocess.run(cmd, text=True, capture_output=True, check=False)
    except FileNotFoundError:
        return None


WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'/][A-Za-z0-9]+)*|[A-Za-z]*\\?[θΘ][A-Za-z]*")


def visible_word_count(text):
    return len(WORD_RE.findall(text))


def normalize(text: str) -> str:
    text = text.replace("\\theta", "theta").replace("θ", "theta").replace("Θ", "theta")
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = re.sub(r"[{}$]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def split_layout_chunks(line):
    chunks = [c.strip() for c in re.split(r"\s{4,}", line.rstrip()) if c.strip()]
    return chunks or ([line.strip()] if line.strip() else [])


def is_ignored_tail_chunk(chunk):
    s = chunk.strip()
    if not s or len(s) <= 2 or s.endswith("-"):
        return True
    if re.match(r"^(C\d+:|Issue\b|Evidence\b|Where\b|OK:|ISSUES:|WARNINGS:)", s):
        return True
    if re.match(r"^(Table|Figure|Fig\.|Appx\.|Appendix|A\d+)\b", s):
        return True
    if re.match(r"^(Role|Row|Label use|Avg|Mechanism|Main claim|Diagnostic|Calibrated)\b", s):
        return True
    if re.fullmatch(r"[\d\s.,()+\-/%=×xX]+", s):
        return True
    if not re.search(r"[.!?]$", s):
        return True
    return False


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * pct)))
    return ordered[idx]


def layout_tail_issues(layout_text, min_words):
    if min_words <= 0:
        return []
    hits = []
    in_table = False
    for raw in layout_text.splitlines():
        if re.search(r"\b(Issue|Role)\b.*\b(Evidence|Row|Label use)\b", raw):
            in_table = True
        if re.match(r"\s*C\d+:", raw):
            in_table = False
        if in_table:
            continue
        for chunk in split_layout_chunks(raw):
            if is_ignored_tail_chunk(chunk):
                continue
            n = visible_word_count(chunk)
            if 0 < n < min_words:
                hits.append((chunk, n))
    seen = set()
    unique = []
    for chunk, n in hits:
        key = (chunk, n)
        if key not in seen:
            seen.add(key)
            unique.append((chunk, n))
    return unique


def bbox_layout_tail_issues(html_text, min_words, min_fill):
    parser = BBoxLayoutParser()
    parser.feed(html_text)
    if not parser.lines:
        return []

    usable_widths = {"left": [], "right": []}
    for line in parser.lines:
        text = line.get("text", "").strip()
        if not text or (line["xmax"] > 300 and line["xmin"] < 300):
            continue
        col = "left" if line["xmin"] < 306 else "right"
        width = line["xmax"] - line["xmin"]
        if width >= 150:
            usable_widths[col].append(width)

    column_width = {col: (percentile(widths, 0.95) or 240.0) for col, widths in usable_widths.items()}

    hits = []
    in_table = False
    for line in parser.lines:
        text = line.get("text", "").strip()
        if re.match(r"^(Issue|Role)\b", text):
            in_table = True
        if re.match(r"^C\d+:", text):
            in_table = False
        if in_table or is_ignored_tail_chunk(text):
            continue
        if line["xmax"] > 300 and line["xmin"] < 300:
            continue
        col = "left" if line["xmin"] < 306 else "right"
        denom = column_width.get(col) or 240.0
        fill = (line["xmax"] - line["xmin"]) / denom if denom else 1.0
        words = visible_word_count(text)
        if fill < min_fill or (words < min_words and fill < 0.95):
            hits.append((text, words, fill))

    seen = set()
    unique = []
    for text, words, fill in hits:
        key = (text, words)
        if key not in seen:
            seen.add(key)
            unique.append((text, words, fill))
    return unique


def protocol_cost_checks(text: str):
    norm = normalize(text)
    issues = []
    warnings = []
    ok = []

    has_fixed_pair = re.search(r"fixed[- ]pair", norm) is not None
    fixed_windows = [
        norm[max(0, m.start() - 140) : min(len(norm), m.end() + 180)]
        for m in re.finditer(r"fixed[- ]pair", norm)
    ]
    has_small_near_fixed = any(
        re.search(r"small[- ]?(four|4)|small diagnostic", window) for window in fixed_windows
    )
    has_full_near_fixed = any(
        re.search(r"full[- ]?(eight|8)|8 datasets|eight datasets|full benchmark", window)
        for window in fixed_windows
    )
    has_conflicting_fixed_window = any(
        re.search(r"small[- ]?(four|4)|small diagnostic", window)
        and re.search(r"full[- ]?(eight|8)|8 datasets|eight datasets|full benchmark", window)
        for window in fixed_windows
    )

    if has_fixed_pair:
        if has_conflicting_fixed_window:
            issues.append("fixed-pair claim mentions both full and small diagnostic scope nearby; verify the scope wording")
        elif has_small_near_fixed and has_full_near_fixed:
            warnings.append("fixed-pair appears with different scopes in different places; verify this is intentional")
        if not re.search(r"shared pair|diagnostic|sensitivity|calibrated|no per[- ]dataset|label use", norm):
            warnings.append("fixed-pair claim lacks explicit diagnostic/shared-pair/label-use wording")
        else:
            ok.append("fixed-pair claim has scope or label-use qualifiers")

    if re.search(r"\b2\s*theta\b|2theta", norm):
        if re.search(r"calibrated|diagnostic|sensitivity|tuned|not.*main|outside strict", norm):
            ok.append("2theta/calibrated analysis appears bounded")
        else:
            warnings.append("2theta-like analysis appears without calibrated/diagnostic/tuned boundary language")

    if re.search(r"\b1\s*theta\b|1theta", norm):
        if re.search(r"strict|fixed|label[- ]free|no labels|zero[- ]shot|deployable", norm):
            ok.append("1theta/main analysis appears tied to strict/deployable wording")
        else:
            warnings.append("1theta-like main result lacks strict/fixed/label-free wording")

    if re.search(r"label use", norm):
        tex_rows = re.split(r"\\\\", text)
        fixed_pair_none_rows = [
            row for row in tex_rows
            if re.search(r"fixed[- ]pair", normalize(row))
            and re.search(r"\bnone\b", normalize(row))
            and not re.search(r"shared pair|diagnostic|calibrated", normalize(row))
        ]
        if fixed_pair_none_rows:
            warnings.append("label-use map may describe fixed-pair as none; consider shared pair or diagnostic wording")
        if re.search(r"shared pair|per[- ]dataset|validation|no labels|none", norm):
            ok.append("label-use vocabulary is visible")

    cost_signal = re.search(r"cost|runtime|latency|\blat\b|memory|\bmem\b|route", norm) is not None
    if cost_signal:
        missing = []
        if not re.search(r"memory|\bmem\b", norm):
            missing.append("memory")
        if not re.search(r"latency|\blat\b|runtime", norm):
            missing.append("latency/runtime")
        if not re.search(r"route", norm):
            missing.append("route ratio")
        if re.search(r"latency|\blat\b|runtime", norm) and not re.search(r"\bvs\b|relative to|baseline", norm):
            missing.append("latency baseline")
        if missing:
            warnings.append("cost evidence may be incomplete: missing " + ", ".join(missing))
        else:
            ok.append("cost evidence names memory, latency/runtime, route, and baseline signal")

    if re.search(r"negative|weak case|dtd|eurosat|failure", norm):
        if re.search(r"accuracy|cost|routing|prompt|prior|reliability|sensitivity", norm):
            ok.append("negative/weak-case language includes a diagnosis axis")
        else:
            warnings.append("negative/weak-case language lacks diagnosis axis")

    if re.search(r"broader use|generalize|extend", norm):
        if re.search(r"limitation|future work|validation|closed|open|shift", norm):
            ok.append("broader-use claim appears bounded")
        else:
            warnings.append("broader-use claim may be overbroad without limitation/future-work boundary")

    return ok, issues, warnings


def bbox_fullness_warnings(pdf: Path, min_bottom: float, max_column_gap: float):
    warnings = []
    ok = []
    bbox_out = Path("/tmp/rebuttal_audit_bbox.html")
    bbox = run(["pdftotext", "-bbox", str(pdf), str(bbox_out)])
    if not (bbox and bbox.returncode == 0 and bbox_out.exists()):
        warnings.append("pdftotext -bbox failed or unavailable; cannot estimate page fullness")
        return ok, warnings

    parser = BBoxParser()
    parser.feed(bbox_out.read_text(encoding="utf-8", errors="replace"))
    if not parser.words:
        warnings.append("no PDF bbox words found; cannot estimate page fullness")
        return ok, warnings

    ymax_all = max(float(w["ymax"]) for w in parser.words)
    if ymax_all >= min_bottom:
        ok.append(f"PDF text extends low on page (max y={ymax_all:.1f})")
    else:
        warnings.append(f"PDF may not be visually full (max y={ymax_all:.1f}, target {min_bottom:.0f})")

    left = [float(w["ymax"]) for w in parser.words if float(w["xmin"]) < 306]
    right = [float(w["ymax"]) for w in parser.words if float(w["xmin"]) >= 306]
    if left and right:
        gap = abs(max(left) - max(right))
        if gap > max_column_gap:
            warnings.append(f"column bottoms differ by {gap:.1f}pt; inspect for a large lower-column blank")
        else:
            ok.append(f"column bottom balance looks acceptable (gap={gap:.1f}pt)")
    return ok, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tex", required=True)
    ap.add_argument("--pdf")
    ap.add_argument("--log")
    ap.add_argument("--reviewers", default="")
    ap.add_argument("--min-tail-words", type=int, default=7)
    ap.add_argument("--min-tail-fill", type=float, default=0.80)
    ap.add_argument("--tail-issue-limit", type=int, default=12)
    ap.add_argument("--min-bottom-y", type=float, default=620.0)
    ap.add_argument("--max-column-bottom-gap", type=float, default=135.0)
    args = ap.parse_args()

    tex = Path(args.tex)
    text = tex.read_text(encoding="utf-8", errors="replace")
    issues = []
    warnings = []
    ok = []

    reviewers = [r.strip() for r in args.reviewers.split(",") if r.strip()]
    for r in reviewers:
        if r in text:
            ok.append(f"reviewer covered: {r}")
        else:
            issues.append(f"missing reviewer id in TeX: {r}")

    p_ok, p_issues, p_warnings = protocol_cost_checks(text)
    ok.extend(p_ok)
    issues.extend(p_issues)
    warnings.extend(p_warnings)

    if args.pdf:
        pdf = Path(args.pdf)
        info = run(["pdfinfo", str(pdf)])
        if info and info.returncode == 0:
            m = re.search(r"Pages:\s+(\d+)", info.stdout)
            pages = int(m.group(1)) if m else None
            if pages == 1:
                ok.append("PDF page count is 1")
            else:
                issues.append(f"PDF page count is {pages}, expected 1")
        else:
            issues.append("pdfinfo failed or unavailable")

        txt = run(["pdftotext", str(pdf), "-"])
        if txt and txt.returncode == 0:
            short = [ln for ln in txt.stdout.splitlines() if 0 < len(ln.strip()) <= 8]
            if len(short) <= 8:
                ok.append("few very short text lines in pdftotext output")
            else:
                warnings.append(f"many very short extracted lines; inspect for orphans: {short[:8]}")
        else:
            issues.append("pdftotext failed or unavailable")

        bbox_layout = run(["pdftotext", "-bbox-layout", str(pdf), "-"])
        if bbox_layout and bbox_layout.returncode == 0:
            tail_hits = bbox_layout_tail_issues(bbox_layout.stdout, args.min_tail_words, args.min_tail_fill)
            if tail_hits:
                shown = tail_hits[: args.tail_issue_limit]
                formatted = [f'"{chunk}" ({n} words, {fill:.0%} fill)' for chunk, n, fill in shown]
                extra = "" if len(tail_hits) <= len(shown) else f"; +{len(tail_hits) - len(shown)} more"
                issues.append(
                    f"short PDF layout tail-like lines below {args.min_tail_fill:.0%} fill or {args.min_tail_words} words: "
                    + "; ".join(formatted)
                    + extra
                )
            elif args.min_tail_words > 0:
                ok.append(f"no PDF layout tail-like lines below {args.min_tail_fill:.0%} fill / {args.min_tail_words} words")
        else:
            layout = run(["pdftotext", "-layout", str(pdf), "-"])
            if layout and layout.returncode == 0:
                tail_hits = layout_tail_issues(layout.stdout, args.min_tail_words)
                if tail_hits:
                    shown = tail_hits[: args.tail_issue_limit]
                    formatted = [f'"{chunk}" ({n} words)' for chunk, n in shown]
                    extra = "" if len(tail_hits) <= len(shown) else f"; +{len(tail_hits) - len(shown)} more"
                    issues.append(
                        f"short PDF layout tail-like lines below {args.min_tail_words} words: "
                        + "; ".join(formatted)
                        + extra
                    )
                else:
                    ok.append(f"no PDF layout tail-like lines below {args.min_tail_words} words")
            else:
                issues.append("pdftotext -bbox-layout/-layout failed or unavailable")

        f_ok, f_warnings = bbox_fullness_warnings(pdf, args.min_bottom_y, args.max_column_bottom_gap)
        ok.extend(f_ok)
        warnings.extend(f_warnings)

    if args.log and Path(args.log).exists():
        log = Path(args.log).read_text(encoding="utf-8", errors="replace")
        if "Overfull" in log:
            issues.append("LaTeX log contains Overfull")
        if re.search(r"(^|[\n!])\s*(LaTeX|Package).*Error", log):
            issues.append("LaTeX log contains an error")
        under = len(re.findall(r"Underfull", log))
        if under:
            warnings.append(f"LaTeX log contains {under} Underfull warnings; visually inspect")
        else:
            ok.append("no Underfull warnings")

    print("OK:")
    for item in ok:
        print(f"  - {item}")
    print("ISSUES:")
    for item in issues:
        print(f"  - {item}")
    print("WARNINGS:")
    for item in warnings:
        print(f"  - {item}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
