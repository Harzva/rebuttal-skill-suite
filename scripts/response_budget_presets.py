#!/usr/bin/env python3
"""Print conference/platform response-box budget presets.

Presets are intentionally conservative defaults. Always check the current call
for papers or submission site before treating a preset as binding.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass(frozen=True)
class Preset:
    platform: str
    format: str
    max_words: Optional[int]
    max_chars: Optional[int]
    require_reviewers: bool
    note: str


PRESETS: dict[str, Preset] = {
    "openreview-750w": Preset("openreview", "text-box", 750, None, True, "Common word-budget style for author responses."),
    "openreview-4000c": Preset("openreview", "text-box", None, 4000, True, "Character-budget style for compact responses."),
    "cmt-750w": Preset("cmt", "text-box", 750, None, True, "CMT-style response with reviewer-ID coverage."),
    "cmt-4000c": Preset("cmt", "text-box", None, 4000, True, "CMT-style character-limited response."),
    "softconf-500w": Preset("softconf", "text-box", 500, None, True, "Tighter response box for short rebuttal rounds."),
    "plain-tight": Preset("plain", "text-box", 600, 3500, False, "Generic tight text-box check without required reviewer IDs."),
    "pdf-one-page": Preset("pdf", "pdf", None, None, False, "Use PDF page/layout gates rather than text-box limits."),
}


def env_lines(name: str, preset: Preset) -> list[str]:
    lines = [
        f"REBUTTAL_RESPONSE_PRESET={name}",
        f"REBUTTAL_RESPONSE_PLATFORM={preset.platform}",
        f"REBUTTAL_RESPONSE_FORMAT={preset.format}",
        f"REBUTTAL_RESPONSE_REQUIRE_REVIEWERS={int(preset.require_reviewers)}",
    ]
    if preset.max_words is not None:
        lines.append(f"REBUTTAL_RESPONSE_MAX_WORDS={preset.max_words}")
    if preset.max_chars is not None:
        lines.append(f"REBUTTAL_RESPONSE_MAX_CHARS={preset.max_chars}")
    return lines


def checker_args(preset: Preset) -> list[str]:
    args = ["--platform", preset.platform]
    if preset.require_reviewers:
        args.append("--require-reviewers")
    if preset.max_words is not None:
        args.extend(["--max-words", str(preset.max_words)])
    if preset.max_chars is not None:
        args.extend(["--max-chars", str(preset.max_chars)])
    return args


def list_presets() -> None:
    for name, preset in PRESETS.items():
        budget = []
        if preset.max_words is not None:
            budget.append(f"{preset.max_words} words")
        if preset.max_chars is not None:
            budget.append(f"{preset.max_chars} chars")
        if not budget:
            budget.append("no text-box budget")
        print(f"{name}\t{preset.platform}\t{', '.join(budget)}\t{preset.note}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preset", nargs="?", choices=sorted(PRESETS))
    parser.add_argument("--list", action="store_true", help="List available presets.")
    parser.add_argument("--json", action="store_true", help="Print the selected preset as JSON.")
    parser.add_argument("--shell", action="store_true", help="Print shell environment assignments.")
    parser.add_argument("--args", action="store_true", help="Print check_response_text.py arguments.")
    args = parser.parse_args()

    if args.list or not args.preset:
        list_presets()
        return 0

    preset = PRESETS[args.preset]
    if args.json:
        data: dict[str, Any] = {"name": args.preset, **asdict(preset)}
        print(json.dumps(data, indent=2, sort_keys=True))
    elif args.shell:
        print("\n".join(env_lines(args.preset, preset)))
    elif args.args:
        print(" ".join(checker_args(preset)))
    else:
        budget = []
        if preset.max_words is not None:
            budget.append(f"max_words={preset.max_words}")
        if preset.max_chars is not None:
            budget.append(f"max_chars={preset.max_chars}")
        print(f"{args.preset}: platform={preset.platform}, format={preset.format}, {', '.join(budget) or 'no text-box budget'}")
        print(f"note: {preset.note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
