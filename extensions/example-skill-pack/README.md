# Example Skill Pack

This example shows the smallest copyable extension shape for adding project-specific rebuttal rules.

It contributes:

`prompts/domain_reviewer.md`: a reviewer persona for domain-claim scope.

`checks/check_domain_claims.py`: a simple checker that flags broad claims without evidence hooks.

`schemas/domain_claims.example.csv`: an example ledger for mapping claims to scope and evidence.

`fixtures/good.md` and `fixtures/bad.md`: regression fixtures used by `validation_commands`.
