#!/usr/bin/env python3
"""Check rebuttal text for defensive, overclaiming, casual, or strategy-like tone."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}
LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?")
ABSOLUTE_NEGATION_RE = re.compile(
    r"\b(?:not|no|without|cannot|can't|does\s+not|do\s+not|did\s+not|"
    r"doesn't|don't|didn't|nor|neither|rather\s+than|instead\s+of)\b",
    re.I,
)

TONE_PATTERNS = [
    (
        "P0",
        "submission-strategy-language",
        re.compile(r"\b(?:convince\s+the\s+AC|appease\s+the\s+reviewer|raise\s+the\s+rating|optimi[sz]e\s+for\s+reviewer)\b", re.I),
        "remove strategy-language and state the scientific clarification directly",
    ),
    (
        "P1",
        "direct-reviewer-blame",
        re.compile(r"\b(?:the\s+)?reviewers?\s+(?:is|are)\s+(?:wrong|incorrect|mistaken)\b", re.I),
        "avoid saying the reviewer is wrong; say what the paper did not make clear",
    ),
    (
        "P1",
        "misunderstanding-framing",
        re.compile(r"\bmisunderstands?|misread(?:s|ing)?\b", re.I),
        "avoid attributing misunderstanding; reframe as clarification or missing emphasis",
    ),
    (
        "P1",
        "unfair-framing",
        re.compile(r"\b(?:unfair|not\s+fair|not\s+true|false\s+claim)\b", re.I),
        "avoid adversarial framing; answer with evidence and bounded correction",
    ),
    (
        "P1",
        "absolute-overclaim",
        re.compile(r"\b(?:prove[sd]?|guarantee[sd]?|always|never|perfect(?:ly)?|universal(?:ly)?|fully\s+solves?|eliminates?|all\s+cases)\b", re.I),
        "avoid absolute claims unless explicitly bounded by evidence, negation, and scope",
    ),
    (
        "P1",
        "novelty-overclaim",
        re.compile(r"\b(?:first\s+ever|entirely\s+new|completely\s+new|state[- ]of[- ]the[- ]art)\b", re.I),
        "avoid novelty or superiority claims that are not tied to a cited comparison",
    ),
    (
        "P2",
        "bare-disagreement",
        re.compile(r"\bwe\s+disagree\b", re.I),
        "prefer a neutral correction such as 'we clarify' or 'we will revise'",
    ),
    (
        "P2",
        "casual-language",
        re.compile(r"\b(?:basically|pretty|kind\s+of|sort\s+of|a\s+lot|huge|super|obviously)\b", re.I),
        "replace casual or loaded intensifiers with precise technical wording",
    ),
]


@dataclass
class Finding:
    severity: str
    code: str
    line: int
    message: str


def strip_latex_noise(text: str) -> str:
    stripped_lines = []
    for line in text.splitlines():
        out = []
        for idx, char in enumerate(line):
            if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
                break
            out.append(char)
        stripped_lines.append("".join(out))
    text = "\n".join(stripped_lines).replace("\\%", " percent ")
    return LATEX_COMMAND_RE.sub(lambda m: m.group(1) or " ", text)


def split_sentences(text: str) -> list[tuple[int, str]]:
    sentences: list[tuple[int, str]] = []
    start = 0
    for match in re.finditer(r"(?<=[.!?])\s+|\n\s*\n", text):
        sentence = text[start : match.start()].strip()
        if sentence:
            sentences.append((text.count("\n", 0, start) + 1, sentence))
        start = match.end()
    tail = text[start:].strip()
    if tail:
        sentences.append((text.count("\n", 0, start) + 1, tail))
    return sentences


def compact(sentence: str, limit: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", sentence).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def should_suppress_match(code: str, sentence: str, match: re.Match[str]) -> bool:
    if code != "absolute-overclaim":
        return False
    prefix = sentence[max(0, match.start() - 80) : match.start()]
    suffix = sentence[match.start() : match.end() + 120]
    if ABSOLUTE_NEGATION_RE.search(prefix):
        return True
    if re.search(r"\bnever\s+cited\s+as\s+no-label\s+evidence\b", suffix, flags=re.I):
        return True
    return False


def check_tone(path: Path) -> list[Finding]:
    text = strip_latex_noise(path.read_text(encoding="utf-8", errors="replace"))
    findings: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()

    for line, sentence in split_sentences(text):
        for severity, code, pattern, guidance in TONE_PATTERNS:
            for match in pattern.finditer(sentence):
                if should_suppress_match(code, sentence, match):
                    continue
                key = (code, line, compact(sentence, 80))
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    Finding(
                        severity,
                        code,
                        line,
                        f"{guidance}: {compact(sentence)}",
                    )
                )
    return findings


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    args = parser.parse_args()

    findings = check_tone(args.path)
    if findings:
        print(f"TONE_FINDINGS count={len(findings)}")
        for finding in findings:
            print(
                f"{finding.severity}\t{finding.code}\tline {finding.line}\t{finding.message}"
            )
    else:
        print("TONE_OK")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
