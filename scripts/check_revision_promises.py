#!/usr/bin/env python3
"""Check whether rebuttal revision promises are concrete and auditable."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


SEVERITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "none": 99}
PROMISE_RE = re.compile(
    r"\b(?:"
    r"we\s+(?:will|would|plan\s+to|commit\s+to|add|clarify|include|report|state|update|revise)|"
    r"(?:the\s+)?(?:revision|revised\s+paper|camera-ready|final\s+version)\s+(?:will|would)|"
    r"(?:will|would)\s+be\s+(?:added|clarified|included|reported|stated|updated|revised)"
    r")\b",
    re.I,
)
WHERE_RE = re.compile(
    r"\b(?:"
    r"table|tab\.|figure|fig\.|appendix|supplement|section|caption|main\s+text|"
    r"main[-\s]+text|(?:limitation|discussion)\s+(?:paragraph|section)|"
    r"revised\s+(?:paper|tables?|captions?|appendix|supplement)|paper\s+tables?|"
    r"protocol\s+summary|revision\s+map|artifact|repository|code|checklist"
    r")\b",
    re.I,
)
EVIDENCE_RE = re.compile(
    r"\b(?:"
    r"result|accuracy|latency|runtime|memory|ratio|number|metric|ablation|diagnostic|"
    r"comparison|calculation|artifact|table|figure|appendix|supplement"
    r")\b",
    re.I,
)
EXPERIMENT_RE = re.compile(
    r"\b(?:run|evaluate|measure|benchmark|collect|train|sweep|experiment|experiments)\b",
    re.I,
)
VAGUE_RE = re.compile(
    r"\b(?:improve|fix|address|handle|discuss|expand|strengthen|better|more\s+details?)\b",
    re.I,
)
SPECIFIC_OBJECT_RE = re.compile(
    r"\b(?:protocol|threshold|label\s+use|cost|latency|memory|route|negative|limitation|"
    r"caption|table|figure|appendix|comparison|baseline|artifact|code|setting|scope)\b",
    re.I,
)
LIMITATION_RE = re.compile(
    r"\b(?:"
    r"limitation|limitations|limit|bounded|scope|out[-\s]?of[-\s]?scope|future\s+work|"
    r"fail|fails|failure|negative|weak|weakness|caveat|risk|prior|shift|open[-\s]?label|"
    r"reliability|misleading|misses?|degradation"
    r")\b",
    re.I,
)
LATEX_COMMAND_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?")
TABULAR_ENV_RE = re.compile(
    r"\\begin\{tabular\}(?:\[[^\]]*\])?\{[^{}]*\}(.*?)\\end\{tabular\}",
    re.S,
)
TABLE_RULE_RE = re.compile(
    r"\\(?:toprule|midrule|bottomrule|hline|cline|cmidrule)(?:\{[^{}]*\})?",
    re.I,
)


@dataclass
class Finding:
    severity: str
    code: str
    line: int
    message: str


def is_escaped_percent(line: str, idx: int) -> bool:
    """Return whether a percent sign is escaped as LaTeX text, not a comment."""
    slash_count = 0
    cursor = idx - 1
    while cursor >= 0 and line[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def strip_latex_comments(text: str) -> str:
    """Remove LaTeX comments while preserving escaped percent signs and line count."""
    cleaned_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        comment_at = None
        for idx, char in enumerate(body):
            if char == "%" and not is_escaped_percent(body, idx):
                comment_at = idx
                break
        if comment_at is not None:
            body = body[:comment_at]
        cleaned_lines.append(body + newline)
    return "".join(cleaned_lines)


def flatten_tabular_environments(text: str) -> str:
    """Convert tabular rows into paragraph-like row contexts for promise checks."""

    def repl(match: re.Match[str]) -> str:
        body = match.group(1)
        row_contexts: list[str] = []
        for raw_row in re.split(r"\\\\(?:\s*\[[^\]]*\])?", body):
            row = TABLE_RULE_RE.sub(" ", raw_row)
            row = row.replace("&", ". ")
            row = re.sub(r"\s+", " ", row).strip()
            if row:
                row_contexts.append(row)
        if not row_contexts:
            return "\n"
        return "\n\n".join(row_contexts) + "\n"

    return TABULAR_ENV_RE.sub(repl, text)


def strip_latex_noise(text: str) -> str:
    text = strip_latex_comments(text)
    text = flatten_tabular_environments(text)
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


def split_paragraphs(text: str) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    start = 0
    for match in re.finditer(r"\n\s*\n", text):
        paragraph = text[start : match.start()].strip()
        if paragraph:
            paragraphs.append((text.count("\n", 0, start) + 1, paragraph))
        start = match.end()
    tail = text[start:].strip()
    if tail:
        paragraphs.append((text.count("\n", 0, start) + 1, tail))
    return paragraphs


def compact(sentence: str, limit: int = 130) -> str:
    cleaned = re.sub(r"\s+", " ", sentence).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def check_promises(path: Path) -> tuple[list[Finding], int]:
    text = strip_latex_noise(path.read_text(encoding="utf-8", errors="replace"))
    findings: list[Finding] = []
    promise_count = 0

    for paragraph_line, paragraph in split_paragraphs(text):
        paragraph_context = re.sub(r"\s+", " ", paragraph)
        sentences = split_sentences(paragraph)
        for _, sentence in sentences:
            if not PROMISE_RE.search(sentence):
                continue
            promise_count += 1
            offset = paragraph.find(sentence)
            line = paragraph_line + (paragraph[:offset].count("\n") if offset >= 0 else 0)
            has_where = bool(WHERE_RE.search(paragraph_context))
            has_evidence = bool(EVIDENCE_RE.search(paragraph_context))
            snippet = compact(sentence)

            if not has_where and LIMITATION_RE.search(paragraph_context):
                findings.append(
                    Finding(
                        "P1",
                        "limitation-promise-without-location",
                        line,
                        "limitation, failure, or weak-case revision promise needs a concrete revised-paper location "
                        "(for example, limitation paragraph, discussion section, table caption, appendix, or artifact) in the same paragraph: "
                        + snippet,
                    )
                )
            elif not has_where:
                findings.append(
                    Finding(
                        "P1",
                        "promise-without-location",
                        line,
                        "revision promise lacks a concrete table/figure/appendix/caption/artifact location in the same paragraph: "
                        + snippet,
                    )
                )

            if EXPERIMENT_RE.search(sentence) and not has_evidence:
                findings.append(
                    Finding(
                        "P1",
                        "experiment-promise-without-evidence-hook",
                        line,
                        "new experiment or measurement promise lacks an evidence/result hook in the same paragraph: "
                        + snippet,
                    )
                )

            if VAGUE_RE.search(sentence) and not SPECIFIC_OBJECT_RE.search(paragraph_context):
                findings.append(
                    Finding(
                        "P2",
                        "vague-promise",
                        line,
                        "revision promise uses vague change language without a concrete object in the same paragraph: "
                        + snippet,
                    )
                )

    return findings, promise_count


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[finding.severity] <= threshold for finding in findings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--fail-on", choices=["P0", "P1", "P2", "none"], default="P1")
    args = parser.parse_args()

    findings, promise_count = check_promises(args.path)
    if findings:
        print(f"REVISION_PROMISE_FINDINGS promises={promise_count}")
        for finding in findings:
            print(
                f"{finding.severity}\t{finding.code}\tline {finding.line}\t{finding.message}"
            )
    else:
        print(f"REVISION_PROMISES_OK promises={promise_count}")

    return 1 if should_fail(findings, args.fail_on) else 0


if __name__ == "__main__":
    raise SystemExit(main())
