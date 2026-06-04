# Extension Interface

`extensions/` is the lightweight contract for adding project-specific rebuttal experience without editing the core suite. An extension can contribute reviewer prompts, domain checkers, CSV/TSV schemas, regression fixtures, and validation commands.

The goal is intentionally small: extensions are discoverable, auditable, and copyable. They are not a separate runtime or plugin framework.

## Directory Shape

```text
extensions/
  my-skill-pack/
    manifest.yaml
    README.md
    prompts/
    checks/
    schemas/
    fixtures/
```

## Extension Types

`Prompt extension`: add reviewer, AC, layout, artifact, or domain-specific persona prompts.

`Checker extension`: add scripts that catch domain-specific failure modes such as protocol drift, cost-claim gaps, safety wording, or dataset-scope ambiguity.

`Schema extension`: add ledgers or maps that make claims, numbers, reviewer concerns, and promised revisions auditable.

## Manifest Contract

Each extension must include a `manifest.yaml` with these fields:

```yaml
name: my_lab_rebuttal_rules
version: 0.1.0
description: Project-specific rebuttal checks and reviewer prompts.
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
```

The `! ` prefix in `validation_commands` means the command is expected to fail. This is useful for bad regression fixtures.

## Create a New Extension

```bash
bash scripts/create_extension.sh my-lab-rebuttal-rules
```

Then edit the generated prompt, checker, schema, and fixtures.

## Validate Extensions

```bash
python3 scripts/validate_extensions.py
```

The suite-level validation wrapper also runs extension validation:

```bash
bash scripts/validate_suite.sh
```

## Design Rules

Keep extension data anonymized when it is meant for public demos.

Keep checks conservative: prefer catching P0/P1 trust risks over style preferences.

Keep claims auditable: every strong public-facing claim should map to evidence, a reviewer issue, or an explicit limitation.

Keep extension logic local: do not require network access, private credentials, or hidden project state.
