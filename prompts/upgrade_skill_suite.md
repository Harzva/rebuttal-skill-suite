# Prompt: Upgrade the Rebuttal Skill Suite

Use this prompt when a real rebuttal iteration produced new lessons that should be folded back into the reusable suite.

```text
目标：持续升级 <repo_path>/rebuttal-skill-suite，使它成为可发布、可复用、专业级的 academic rebuttal adversarial review skill suite。

请实际修改文件，不要只给建议。

检查：
1. 当前发布版 repo：<repo_path>/rebuttal-skill-suite
2. 当前安装版 skills：~/.codex/skills/rebuttal-audit 和 ~/.codex/skills/rebuttal-leak-audit
3. 核心文件：README、workflow、两个 SKILL.md、reviewer_roles、scripts、release checklist

基于最新 rebuttal 经验，判断是否需要升级：
- reviewer persona 是否缺了某种真实审稿人攻击角度？
- P0/P1/P2 分级是否足够锋利？
- 是否覆盖 fixed-vs-tuned、label-use、cost、negative-case、leakage、layout、stop rule？
- gate script 是否能自动发现高风险问题？
- 是否需要新增匿名 fixture、claim-ledger 行、persona-output 结构检查或 suite-level validation？
- 是否需要新增 reported-number ledger 或 expected-failure regression fixture，防止规则变松？
- 是否需要新增 result-table CSV/TSV consistency checker，防止 appendix/summary 表和正文数字漂移？
- 是否需要新增 reviewer-issue map checker，防止某个 reviewer 原始 issue 没有对应 response anchor？
- 是否需要新增 tone-risk checker，防止 defensive、overclaim、casual 或 submission-strategy 语气削弱可信度？
- 是否需要新增安装、发布包、引用完整性或 private-text package check？
- 是否需要新增 release archive / CI validation，证明打包后仍能安装和运行？
- 是否需要新增 pasted-response / platform text-box checker，防止最终粘贴版漏 reviewer、带 TODO、本地路径或 LaTeX-only 命令？
- 是否需要新增 revision-promise checker，防止 `we will add/clarify/report` 变成没有位置和证据锚点的空头承诺？
- README、发布说明、安装版和 repo 版是否同步？

修改原则：
- 泛化到任意 academic rebuttal，不硬编码某一篇论文。
- 不泄露私有路径、advisor/internal feedback、工具日志或策略话术。
- reviewer personas 要先列 P0/P1/P2 findings，再给 minimal patch。
- 优先把真实踩坑变成可验证规则、脚本检查或 persona checklist。
- 形成“生成-攻击-聚合-最小修复-验证-停止”的闭环。

验证：
- quick_validate.py 验证两个 skills。
- run_rebuttal_gates.sh 在一个真实 rebuttal.tex 上跑通。
- aggregate_reviewer_feedback.py 能正常运行。
- validate_repo_clean.py 确认没有 __pycache__、临时 PDF、log、aux 等发布垃圾文件。
- 如有新增 claim 风险，用 check_claim_ledger.py 在匿名 fixture 或本地 ledger 上验证。
- 如有新增数字风险，用 check_reported_numbers.py 对匿名 fixture 或本地 number ledger 验证。
- 如有新增结构化结果表风险，用 check_result_table.py 对匿名 result table 或本地 summary CSV/TSV 验证。
- 如有 reviewer issue 覆盖风险，用 check_reviewer_issue_map.py 对匿名 issue map 或本地 coverage matrix 验证。
- 如有 tone 风险，用 check_rebuttal_tone.py 对匿名 tone fixture 或真实 rebuttal 验证。
- 如有最终粘贴版风险，用 check_response_text.py 对匿名 pasted-response fixture 或真实最终回复验证。
- 如有 revision promise 风险，用 check_revision_promises.py 对匿名 promise fixture 或真实 rebuttal 验证。
- 跑 run_regression_fixtures.sh，确保已知坏例子确实失败。
- 跑 validate_release_package.py 和 install_skills.sh --check，确认发布包完整且安装版同步。
- 跑 build_release_archive.sh，确认 tarball 解压后仍能通过 package/suite/regression 验证。
- 如有新增 persona，跑 check_persona_outputs.py 确保 P0/P1/P2/minimal patch/recommendation 完整。

最后输出：
- 本轮升级了什么。
- 修改了哪些文件。
- 验证结果。
- 下一轮可升级点。
- 是否达到可发布版本标准。
```
