#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_NAME="${1:-}"

if [[ -z "$RAW_NAME" ]]; then
  echo "usage: bash scripts/create_extension.sh <extension-name>" >&2
  exit 2
fi

SLUG="$(printf '%s' "$RAW_NAME" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
if [[ -z "$SLUG" ]]; then
  echo "extension name must contain at least one letter or number" >&2
  exit 2
fi

EXT_DIR="$ROOT_DIR/extensions/$SLUG"
if [[ -e "$EXT_DIR" ]]; then
  echo "extension already exists: $EXT_DIR" >&2
  exit 1
fi

mkdir -p "$EXT_DIR/prompts" "$EXT_DIR/checks" "$EXT_DIR/schemas" "$EXT_DIR/fixtures"

cat > "$EXT_DIR/manifest.yaml" <<EOF_MANIFEST
name: ${SLUG//-/_}
version: 0.1.0
description: Project-specific rebuttal extension for prompts, checks, schemas, and fixtures.
extension_types:
  - prompt
  - checker
  - schema
prompts:
  - prompts/domain_reviewer.md
checks:
  - checks/check_domain_claims.py
schemas:
  - schemas/domain_claims.example.csv
fixtures:
  - fixtures/good.md
  - fixtures/bad.md
validation_commands:
  - python3 checks/check_domain_claims.py fixtures/good.md --fail-on P1
  - '! python3 checks/check_domain_claims.py fixtures/bad.md --fail-on P1'
severity_default_fail_on: P1
EOF_MANIFEST

cat > "$EXT_DIR/README.md" <<'EOF_README'
# Extension Pack

Describe the rebuttal failure modes this extension catches, when to run it, and which evidence ledgers or reviewer concerns it expects.
EOF_README

cat > "$EXT_DIR/prompts/domain_reviewer.md" <<'EOF_PROMPT'
# Domain Reviewer

Find P0/P1/P2 issues where domain claims exceed the available evidence.

For each issue, report concern, evidence needed, and minimal fix.
EOF_PROMPT

cat > "$EXT_DIR/checks/check_domain_claims.py" <<'EOF_CHECK'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

PATTERNS = [re.compile(r"\b(universally|always|production-ready|free speedup)\b", re.I)]
HINTS = ["evidence:", "table", "appendix", "ledger", "baseline", "limitation"]

parser = argparse.ArgumentParser()
parser.add_argument("path")
parser.add_argument("--fail-on", default="P1")
args = parser.parse_args()

text = Path(args.path).read_text(encoding="utf-8")
findings = []
for line_no, line in enumerate(text.splitlines(), start=1):
    if any(p.search(line) for p in PATTERNS) and not any(h in line.lower() for h in HINTS):
        findings.append((line_no, line.strip()))

for line_no, line in findings:
    print(f"P1: broad claim lacks evidence hook at line {line_no}: {line}")

if findings and args.fail_on in {"P0", "P1"}:
    sys.exit(1)
print("DOMAIN_CLAIMS_OK")
EOF_CHECK

cat > "$EXT_DIR/schemas/domain_claims.example.csv" <<'EOF_SCHEMA'
claim_id,claim_text,scope,evidence_anchor,reviewer_anchor,severity_if_missing
C1,"Scoped domain claim.","explicit scope","Table or appendix anchor","R1",P1
EOF_SCHEMA

cat > "$EXT_DIR/fixtures/good.md" <<'EOF_GOOD'
We scope this claim to the reported setting; evidence: Table 1 and the limitation paragraph.
EOF_GOOD

cat > "$EXT_DIR/fixtures/bad.md" <<'EOF_BAD'
The method universally works and gives a free speedup.
EOF_BAD

chmod +x "$EXT_DIR/checks/check_domain_claims.py"
echo "Created extension: $EXT_DIR"
