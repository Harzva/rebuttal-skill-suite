.PHONY: validate regression clean-check install check-install package-check table-check issue-map-check tone-check response-check promise-check archive

REBUTTAL_TEX ?=
REVIEWERS ?= FEoB,bCeM,y76H,MekP
CODEX_HOME ?= $(HOME)/.codex

validate:
	bash scripts/validate_suite.sh $(REBUTTAL_TEX) $(REVIEWERS)

regression:
	bash scripts/run_regression_fixtures.sh

clean-check:
	python3 scripts/validate_repo_clean.py .

package-check:
	python3 scripts/validate_release_package.py .

table-check:
	python3 scripts/check_result_table.py examples/result_summary.csv --expect schemas/result_table_expectations.example.csv

issue-map-check:
	python3 scripts/check_reviewer_issue_map.py examples/issue_map_response_good.md --map schemas/reviewer_issue_map.example.csv --reviewers $(REVIEWERS) --fail-on P1

tone-check:
	python3 scripts/check_rebuttal_tone.py examples/tone_good.md --fail-on P1

response-check:
	python3 scripts/check_response_text.py examples/platform_response_good.md --reviewers $(REVIEWERS) --require-reviewers --platform openreview --max-words 220 --max-chars 1500

promise-check:
	python3 scripts/check_revision_promises.py examples/revision_promises_good.md --fail-on P1

archive:
	bash scripts/build_release_archive.sh

install:
	bash scripts/install_skills.sh --codex-home $(CODEX_HOME)

check-install:
	bash scripts/install_skills.sh --codex-home $(CODEX_HOME) --check
