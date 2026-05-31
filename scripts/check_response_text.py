#!/usr/bin/env python3
"""Check a final pasted rebuttal/author-response text for platform safety."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}

LATEX_ONLY_PATTERNS = [
    ("latex-vspace", re.compile(r"\\vspace\b")),
    ("latex-hspace", re.compile(r"\\hspace\b")),
    ("latex-includegraphics", re.compile(r"\\includegraphics\b")),
    ("latex-input", re.compile(r"\\input\b")),
    ("latex-bibliography", re.compile(r"\\bibliography\b")),
    ("latex-maketitle", re.compile(r"\\maketitle\b")),
    ("latex-table-env", re.compile(r"\\begin\s*\{\s*table\s*\}")),
    ("latex-figure-env", re.compile(r"\\begin\s*\{\s*figure\s*\}")),
]
PLACEHOLDER_PATTERNS = [
    ("todo", re.compile(r"\bTODO\b", re.I)),
    ("tbd", re.compile(r"\bTBD\b", re.I)),
    ("fill-placeholder", re.compile(r"\[\s*fill\s*\]", re.I)),
    ("double-question", re.compile(r"\?\?")),
]
LOCAL_PATH_RE = re.compile(
    r"(?:(?:/home|/Users|/tmp|/var/tmp)/[^\s),;]+|(?:[A-Za-z]:\\[^\s),;]+)|(?:file://[^\s),;]+))"
)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?")


@dataclass
class Finding:
    severity: str
    code: str
    line: int
    message: str


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def parse_reviewers(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def reviewer_present(text: str, reviewer: str) -> bool:
    pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(reviewer)}(?![A-Za-z0-9_-])", re.I)
    return bool(pattern.search(text))


def is_local_markdown_target(target: str) -> bool:
    cleaned = target.strip().strip("<>").split()[0]
    if cleaned.startswith(("http://", "https://", "mailto:")):
        return False
    if cleaned.startswith(("/", "./", "../", "file://")):
        return True
    if re.match(r"^[A-Za-z]:\\", cleaned):
        return True
    if re.search(r"\.(pdf|png|jpg|jpeg|gif|tex|csv|tsv|log|aux)(?:#.*)?$", cleaned, re.I):
        return True
    return False


def check_response_text(
    path: Path,
    reviewers: list[str],
    require_reviewers: bool,
    max_words: int | None,
    max_chars: int | None,
    platform: str,
) -> tuple[list[Finding], int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    findings: list[Finding] = []
    word_count = len(WORD_RE.findall(text))
    char_count = len(text)

    if max_words is not None and word_count > max_words:
        findings.append(
            Finding("P0", "word-limit", 1, f"word count {word_count} exceeds max {max_words}")
        )
    if max_chars is not None and char_count > max_chars:
        findings.append(
            Finding("P0", "char-limit", 1, f"character count {char_count} exceeds max {max_chars}")
        )

    missing = [reviewer for reviewer in reviewers if not reviewer_present(text, reviewer)]
    if missing:
        severity = "P0" if require_reviewers else "P1"
        findings.append(
            Finding(
                severity,
                "missing-reviewers",
                1,
                "missing reviewer IDs: " + ",".join(missing),
            )
        )

    for code, pattern in LATEX_ONLY_PATTERNS:
        for match in pattern.finditer(text):
            severity = "P0" if platform in {"openreview", "cmt"} else "P1"
            findings.append(
                Finding(
                    severity,
                    code,
                    line_for_offset(text, match.start()),
                    "LaTeX-only formatting command is risky in pasted response text",
                )
            )

    for code, pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(
                Finding(
                    "P0",
                    code,
                    line_for_offset(text, match.start()),
                    "unresolved placeholder or unknown reference marker",
                )
            )

    for match in LOCAL_PATH_RE.finditer(text):
        findings.append(
            Finding(
                "P0",
                "local-path",
                line_for_offset(text, match.start()),
                "local filesystem path or file URL should not appear in reviewer-facing text",
            )
        )

    for match in MARKDOWN_LINK_RE.finditer(text):
        target = match.group(1)
        if is_local_markdown_target(target):
            findings.append(
                Finding(
                    "P0",
                    "markdown-local-ref",
                    line_for_offset(text, match.start()),
                    f"Markdown link/image points to a local or attachment-like target: {target}",
                )
            )

    return findings, word_count, char_count


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path)
    parser.add_argument("--reviewers", default="", help="Comma-separated reviewer IDs expected in text.")
    parser.add_argument("--require-reviewers", action="store_true", help="Treat missing reviewer IDs as P0.")
    parser.add_argument("--max-words", type=int)
    parser.add_argument("--max-chars", type=int)
    parser.add_argument("--platform", choices=["openreview", "cmt", "plain"], default="plain")
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P0")
    args = parser.parse_args()

    findings, word_count, char_count = check_response_text(
        args.response,
        parse_reviewers(args.reviewers),
        args.require_reviewers,
        args.max_words,
        args.max_chars,
        args.platform,
    )

    if findings:
        print("RESPONSE_TEXT_FINDINGS")
        for finding in findings:
            print(
                f"{finding.severity}\t{finding.code}\tline {finding.line}\t{finding.message}"
            )
    else:
        print(
            f"RESPONSE_TEXT_OK words={word_count} chars={char_count} platform={args.platform}"
        )

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
