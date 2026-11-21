# Skill 矩阵 · 阶段加载表与仓库地址

> 本文件回答两个问题：**每阶段调哪个器官 / 工具**、**这些 skill 从哪来 / 怎么装**。
> 架构：conductor 是机体（状态机+门禁+决策），`skills/conductor-*`（与 conductor 同级） 是器官（单一能力），场景是环境；完整总线见 `organ-registry.md`。
> **成本档位裁剪**：下表是 standard/full；lite 按 `../../../conductor-router/references/cost-tiers.md` 跳过 overview L1 交接/env_probe/台账/影响面/活规格/学习回写/独立子代理（改 `review_gate.py --lite`）。省掉的步骤必须写进路由声明。

## 1. 完整阶段矩阵

| 阶段 | 主控 | 加载 / 调用 | 本步禁止 | 出口条件 |
|---|---|---|---|---|
| S0 会话开始 | conductor | `preflight.py` → 器官 `conductor-overview`（L0 主文件 + `.details.md`，内含改名并入的 overview L1 交接方法）→ `env_probe.py`（有环境信号时）→ 器官 `conductor-ledger` init（有隐含清单时） | 禁止直接写代码 | 预检 + overview L0 + 状态文件已忽略 + 承诺已采集 |
| S1 场景路由 | conductor | 器官 `conductor-router` 出执行图+声明；器官 `conductor-impact`（跨模块/full）；场景7 `migration_ledger.py init --merge` | 禁止跳过声明 | 路由声明含场景/路径/档位/省掉 |
| S2 设计计划 | conductor | 器官 `conductor-brainstorm`（自带 grill-design 方法与规格模板）→ 器官 `conductor-spec`（六段 change-contract，Acceptance 灌入台账）；架构类由 `conductor-impact` 核契约 | 规格未确认不动手；契约未确认不进 S3 | 规格要点 + 未决清单 + 契约 `contract_check.py` 退出 0 |
| S3 TDD 实现 | conductor | 器官 `conductor-subagent`（计划 ≥3 独立任务时派发，条件触发；判据见 cost-tiers 条件加载表）；器官 `conductor-tdd`（RED→GREEN，`verify.py` 证据，最小改动原则已内联）；写码后 `source_purity.py --strict` | 无失败测试不写实现；禁 fake/动态类型 | 红转绿、全量绿、无未豁免污染 |
| S4 自省补强 | conductor | `scan_gaps.py` → `verify.py` → `debt_ledger.py` → `source_purity.py check --strict`；器官 `conductor-ledger` check；需要时 `conductor-impact`；安全/测试/接口按 guard 核对 | 未达标不许进 review | 覆盖率/缺口/纯净/台账五项达标 |
| S5 review 收尾 | conductor | 器官 `conductor-review`（standard/full 子代理 + 自带七维契约；lite 走 `--lite`）→ `review_gate.py`；`conductor-ledger` 零未勾销；器官 `conductor-learn`（standard/full，默认 dry-run，确认后回写）；发版走 `release-checklist.md` + `release_notes.py`；`conductor-overview` 收尾 | Blocker 未清零 / 台账未收口不许收尾；learn 不自动污染 skill | gate 退出 0 + 台账零未勾销 + learn 留痕 + overview 已更新 |

### 确定性脚本（scripts/，非 skill，直接执行）

> **单一真相源**：`verify / review_gate / overview_path / commitment_ledger / migration_ledger / impact_analysis` 在 `conductor/scripts/` 是薄 shim，实现分别在 `conductor-tdd / conductor-review / conductor-overview / conductor-ledger / conductor-ledger / conductor-impact` 的 `scripts/`；调用路径不变。`script_parity_test.py` 检查 shim 不漂移。

| 脚本 | 用途 | 调用 |
|---|---|---|
| `preflight.py` | 预检外部 skill + 语言验证工具是否就位，缺失给安装命令 | `python scripts/preflight.py --project-root .` |
| `verify.py` | 执行 `coding-rules-<lang>.md` 的验证命令，汇总退出码为证据 | `python scripts/verify.py --lang <lang>` |
| `scan_gaps.py` | 扫 TODO/pass/fake/协议无实现/install 无调用，生成缺口台账草稿 | `python scripts/scan_gaps.py --path src` |
| `review_gate.py` | 校验 overview 的独立 review 证据（章节/Blocker 清零/内嵌报告章节或外部报告文件存在），防"声称审查但无证据" | `python scripts/review_gate.py --overview <path>`；非改码场景加 `--waived --waiver-reason "<理由>"`；lite 档加 `--lite`（与 `--waived` 互斥） |
| `impact_analysis.py` | 变更影响分析：从符号/改动文件/stdin diff 找引用者与建议跑的测试，辅助迭代/重构的影响面评估 | `python scripts/impact_analysis.py --symbols Foo,bar` / `--files src/a.py` / 管道 `--diff` |
| `debt_ledger.py` | 技术债台账：扫 TODO/FIXME/HACK 等标记，算债指数与热点文件，出草稿 | `python scripts/debt_ledger.py --path src`；`--format json`；`--fail-over <N>` 卡口 |
| `release_notes.py` | 发布说明草稿：从 conventional commits 生成 CHANGELOG 分组 + 语义化版本建议 | `python scripts/release_notes.py --since <tag> --repo <path>` |
| `overview_path.py` | overview 路径定位：用会话指针 `.conductor-session.json` 锚定，同会话多轮归同一文件（跨 agent 通用，零环境变量依赖） | `python scripts/overview_path.py --project-root . --topic "<主题>"`；换任务加 `--new-session`；结束加 `--end-session` |
| `env_probe.py` | 真实环境探测：docker 可用性、集成测试目录、DB/Redis 依赖信号，给真实测试入口命令（防"无环境砍功能"） | `python scripts/env_probe.py --project-root .` |
| `commitment_ledger.py` | 承诺台账（全场景防漏引擎）：init 多来源采集（--from-modules/--from-list/--stdin/--manual）、next 断点、check --strict 零未勾销门禁、show 概览 | `python scripts/commitment_ledger.py init --ledger .commitment-ledger.json --from-list docs/spec.md`；impact 输出管道 `--stdin`；收尾 `check --ledger ... --modules src --strict`（见 `../../../conductor-ledger/references/commitment-ledger.md`） |
| `migration_ledger.py` | 场景7 兼容 shim（底层委托 commitment_ledger，固定 source=module）：init 扫码建台账、next 断点、check --strict 收口门禁 | `python scripts/migration_ledger.py init --path src --project <名>`；新增模块 `--merge`；续接 `next`；收尾 `check --path src --strict`（见 `../../../conductor-ledger/references/migration-integrity.md`） |
| `source_purity.py` | 源码纯净门禁：数据驱动规则库（27条+自定义）扫 fake 实现与不具体类型各语言多形状；**存量基线只卡新增/改到的文件**（重构场景）；purity-exempt 留痕豁免；排除 tests/；默认合并 intent_gaps | `scan --path src --strict`；重构 `baseline --path src` 后 `check --path src --baseline .purity-baseline.json --scope changed.txt --strict`；`rules` 列规则（见 `source-purity.md`） |
| `intent_gaps.py` | 意图空白扫描（函数级 AST）：无注释跨模块占位（pass/NotImplementedError）、声明未用且无说明的参数；合法豁免=注释说明/abstract/_前缀/docstring | `python scripts/intent_gaps.py --path src --strict`；已默认并入 source_purity，`--no-intent` 可关（见 `source-purity.md` §二·补） |
| `contract_check.py` | 变更契约检查：六段齐全 + Acceptance 非空，可只输出 Acceptance 条目喂台账 | `python ../../conductor-spec/scripts/contract_check.py --contract change-contract.md`；`--acceptance-only` 管道到 `commitment_ledger.py init --stdin` |
| `learn_capture.py` | 从 overview 抽可回写经验草稿，默认 dry-run，需 `--apply --out` 才落盘 | `python ../../conductor-learn/scripts/learn_capture.py --overview <path>`；确认后 `python ../../conductor-learn/scripts/learn_capture.py --overview <path> --out docs/conventions.md --apply` |
| `script_parity_test.py` | 检查 6 个重复入口仍是薄 shim、目标存在且 `--help` 可转发，防实现漂移 | `python scripts/script_parity_test.py` |

## 2. Skill 清单与仓库地址

> **器官 skill**（`skills/conductor-*`，与 conductor 同级）由 conductor 按 `organ-registry.md` 调用；每个只声明 I/O、加载时机与降级，不重复 conductor 状态机。
> 外部 skill 是器官的执行器/工具，不定义阶段。目录随项目自包含，`preflight.py --verify-organs` 可复核。

| 器官 skill | 状态 | 执行器 / 工具 |
|---|---|---|
| `conductor-router` | 主流程 S1 | 自包含（routing + cost-tiers + I/O 契约） |
| `conductor-brainstorm` | 主流程 S2 | 自带 `../../../conductor-brainstorm/references/grill-design-SKILL.md`、`../../../conductor-brainstorm/references/examples-to-spec.md` |
| `conductor-spec` | 主流程 S2（standard/full） | 自带 `../../../conductor-spec/references/change-contract-template.md`、`../../../conductor-spec/references/spec-method.md`、`../../../conductor-spec/scripts/contract_check.py` |
| `conductor-tdd` | 主流程 S3/S4 | 自带 `../../conductor-tdd/scripts/verify.py`、编码规则 |
| `conductor-review` | 主流程 S5 | 自带 `../../../conductor-review/references/code-quality-review-SKILL.md`、`scripts/review_gate.py` |
| `conductor-learn` | 主流程 S5（standard/full） | 自带 `../../../conductor-learn/references/learning-method.md`、`../../../conductor-learn/references/lessons-template.md`、`../../../conductor-learn/scripts/learn_capture.py` |
| `conductor-ledger` | 主流程 S0/S4/S5 | 自带 `../../conductor-ledger/scripts/commitment_ledger.py`、`migration_ledger.py` |
| `conductor-overview` | 主流程 S0/收尾 | 自带 `../../conductor-overview/scripts/overview_path.py`、overview L1 交接与两-tier 模板 |
| `conductor-impact` | 条件 S1/S4 | 自带 `../../conductor-impact/scripts/impact_analysis.py`、架构契约 |
| `conductor-git` | 条件：每任务 GREEN 后 / 用户说提交 | 自带 `../../../conductor-git/references/git-commit.md`、`../../../conductor-git/references/git-commit-rules.md` |
| `conductor-subagent` | 条件：S3 派发判据命中 | 自带 `../../../conductor-subagent/references/dispatch.md`；评审规则用 conductor-review |
| `conductor-debug` | 场景 8 | 自带 `../../../conductor-debug/references/engineering-debugging.md` |

**外部 skill 已全部处理**：grill-design / code-quality-review / handoff 改名并入器官；graphify / ponytail / caveman / grill-me / ponytail-review / caveman-compress / metago-code-review-deep 经筛选测试判定废弃并**物理删除**，主链零外部依赖。

## 3. 跨 agent 安装方式

通用 skills CLI（支持 Claude Code / Codex / Cursor / OpenCode 等）：

```bash
# 通用安装（把仓库 skill 装到当前项目的 .agents/skills/ 或用户级）
npx skills add <repo> --skill <skill-name>

# 示例（仓库内器官随 conductor 一起安装，无需单独装外部 skill）
```

按 agent 的目录约定（手动放置时）：

| Agent | Skill 目录 |
|---|---|
| Claude Code | `.claude/skills/<name>/SKILL.md` |
| Codex | `.codex/skills/<name>/SKILL.md` |
| OpenCode | `.opencode/skill/<name>/SKILL.md` 或 `.config/opencode/skill/` |
| 通用 CLI | `.agents/skills/<name>/SKILL.md` |

本 skill（`conductor`）位于项目根 `.agents/skills/conductor/`，为通用结构，可被上述任一 agent 加载。

## 4. 加载原则（单一主控）

1. **唯一主控**：conductor 自己执行全部工程阶段（brainstorm/spec/TDD/review/learn/debugging/收尾），
   步骤细节在 `engineering-*.md`，不再加载任何其他流程 skill。**没有第二套工作流**。
2. **工程纪律内化**：原 superpowers 方法论已提取为内部 reference（含来源致谢），
   不依赖外部 skill 是否存在；外部工具 skill 缺失只影响该工具，不影响流程本身。
3. **工具是配角**：已并入或废弃的外部 skill 不再加载；器官自带方法按阶段调用。
   它们不定义阶段、不争夺主控；conductor 决定何时加载哪个器官。
4. **事件触发规则加载**：coding-rules 靠 S1 种下的会话级约束 + 写码事件触发读取，不在 S3 动态注入。
