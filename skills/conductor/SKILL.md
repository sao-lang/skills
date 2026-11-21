---
name: conductor
description: 通用的 AI 开发工作流主控 skill。收到开发/重构/迁移/修 bug/项目初始化/迭代/架构设计/拷问代码或设计/代码库理解/文档同步/门禁验收/测试补课/文档清理，或"别漏需求/模块""别写内存版假实现/别用 Any"类防漏与源码纯净需求时加载：作为机体只做状态机、路由、门禁与器官调度；工程能力由 11 个器官 skill 执行。适用于支持 SKILL.md 的 agent。
---

# conductor · 开发工作流机体

> **机体—器官—环境**：conductor 只持有状态机 S0–S5、决策权与硬门禁；`skills/conductor-*` 是器官（单一能力）；14 场景是工作环境（声明调哪些器官）；`references/` 是共享组织（方法论与证据口径）。
> 铁律：**器官给结论和证据，不放行；conductor 才放行**。入口不重复器官内部步骤。

## 触发后必须先做

1. **定位 overview**：跑 `scripts/overview_path.py --project-root . --topic "<主题>"`；同会话续写 L0 主文件（≤8 行），详情在 `.details.md`，默认不读详情。
2. **路由并声明**：调 `conductor-plan`（场景判定方法见其 `router/planning-core.md`），声明「场景 / 路径 / 成本档位 / 省掉 / 下一站」。**未声明不推进**；低置信先问，降级只读，绝不猜改码硬跑。

## 器官总线

完整映射见 `references/01-routing/organ-registry.md`（调用阶段、I/O、缺失降级、废弃 skill 清单）。**按表调用，不临场发挥**：

| 阶段 | 必调器官 | 按触发 |
|---|---|---|
| S0 | `conductor-memory` | `conductor-ledger`（有隐含清单） |
| S1 | `conductor-plan` | `conductor-impact`（跨模块/full） |
| S2 | `conductor-brainstorm`（澄清 + 规格固化一体） | standard/full 出 change-contract；lite 只澄清不固化 |
| S3 | `conductor-tdd` | `conductor-subagent`（任务集可并行时派发，条件触发，不限于改码）、自带编码规则 |
| S4 | `conductor-tdd`（证据） | `conductor-ledger`、`conductor-impact` |
| S5 | `conductor-review` | `conductor-ledger`、`conductor-memory`（沉淀，standard/full） |

成本档位 lite/standard/full 由 `conductor-plan` 判定；规则见 `references/01-routing/cost-tiers.md`。lite 省掉交接/环境探测/台账/影响面/契约固化/沉淀回写/独立子代理，保留规格澄清、TDD、`verify.py`、`source_purity`、review 门禁。

**条件加载**：同档位内器官是否真的跑，按 `../conductor/references/01-routing/cost-tiers.md` 第三节的条件加载表判（如单任务不派子代理、无清单跳台账、用户"先不提交"跳提交）；每个跳过写进声明"省掉"并带依据，禁止静默跳过。

## 十四场景 = 工作环境（只声明器官，不重复步骤）

| 场景 | 路径 | 器官链 |
|---|---|---|
| 1 初始化 / 4 开发 | 改码 | router → brainstorm(澄清→规格) → subagent(条件) → tdd → git(commit，条件) → ledger → review → memory(沉淀) |
| 2/3 设计 | 文档 | router → brainstorm（自带拷问与规格方法；确认后可固化 change-contract） |
| 5 迭代 / 6 设计驱动重构 | 改码 | router → brainstorm(规格) → impact → subagent(条件) → tdd → git(commit，条件) → ledger → review → memory(沉淀) |
| 7 项目重构 | 改码 | router → ledger(migration shim) → brainstorm(规格) → impact → tdd → git(commit，条件) → review → memory(沉淀) |
| 8 解 bug | 改码 | router → debug → brainstorm(轻量) → tdd → git(commit，条件) → review → memory(沉淀) |
| 9 拷问 / 10 理解 | 只读 | router → brainstorm / impact → memory（结束） |
| 11 文档同步 | 文档 | router → brainstorm → memory |
| 12 门禁验收 | 验证 | router → review（+ledger） |
| 13 测试补课 | 验证 | router → tdd → review → memory(沉淀) |
| 14 文档清理 | 文档·清理 | router → memory（确认无依赖后执行，排链尾） |

场景细节与 I/O 契约见 `../conductor/references/01-routing/scenarios.md`：**S1 只读 I/O 契约表，执行到某场景才读该节**。

## 硬门禁（不可下放给器官）

- **规格未确认不动手**；**无失败测试不算实现**；**拿不出证据（命令+退出码/行号）不标完成**。
- 测试证据只认 `scripts/verify.py`；写码后必跑 `../conductor-review/scripts/source_purity.py check --strict`（fake 实现/动态类型/无注释占位，重构用 baseline + `--scope`）。
- 改码交付前必过 `scripts/review_gate.py`：standard/full 走独立子代理，lite 走 `--lite` 轻量复核；Blocker 未清零禁止收尾。
- 有隐含清单必建台账，`commitment_ledger.py check --strict` 退出 0 才准收尾；禁止刷状态、禁止静默跳过。
- 真实环境优先：无环境不砍功能、不写 fake 冒充 adapter、不留无注释跨模块占位；环境缺失登记「环境阻断」，禁改断言造假绿。
- **最小完整变更**：最小的是变更面不是 diff 行数；改契约同次删旧路径，禁新旧双轨；兼容层仅用户显式要求才建且必须带退出条件（登记进 change-contract Open 段，`source_purity.py` 双轨规则命中即卡）。
- **该删没删 = 改动未完成**：有废弃语义（契约 Delta 含删除/替换动词）时 S2 过删除推导、待删项带符号名登记，S5 用 `removal_check.py` 核对残留；纯新增无废弃项只写一行"无遗留"留痕。触发判据见 `../conductor/references/01-routing/cost-tiers.md` 第三节——机器可判优先，跳过必须声明。
- **文档与代码同等交付**：改公共契约/接口/架构决策 → 设计文档按 change-contract Affected 清单同步（或显式声明无影响）；未同步未声明 = Blocker，阻断收尾。

## 参考与脚本

- 参考文档按需加载，索引见 `references/05-meta/README.md`：`../conductor-plan/references/router/planning-core.md`/`../conductor/references/01-routing/cost-tiers.md`/`organ-registry.md` 在 S1 读，`../conductor/references/01-routing/scenarios.md`、`../conductor-brainstorm/references/brainstorm-method.md`、`../conductor-plan/SKILL.md`、`../conductor-brainstorm/references/spec-method.md`、`../conductor-memory/references/learning-method.md` 按节，其余触发才读。
- **8 个本体入口**：`preflight / env_probe`（S0 预检与环境探测，本体实现）+ `overview_path / verify / review_gate / impact_analysis / commitment_ledger / migration_ledger`（6 个薄 shim，实现唯一真相源在器官目录，`script_parity_test.py` 防漂移）。
- **已分流到器官的脚本**：缺口/纯净/意图扫描归 `../conductor-review/scripts/`（`scan_gaps.py` / `source_purity.py` / `intent_gaps.py`），技术债台账归 `../conductor-ledger/scripts/debt_ledger.py`，发版说明归 `../conductor-git/scripts/release_notes.py`；契约脚本在 `conductor-brainstorm/scripts/`，沉淀脚本在 `conductor-memory/scripts/`。
- **统一安装/更新与完整性测试**归 `conductor-sync`：`sync-global.py` + 三测试 + 协作审计，见其 SKILL.md；参数总表见 `skill-matrix.md`。
- 外部 skill 缺失必须显式降级并在 overview 写「缺失 X / 影响 Y / 降级 Z」，禁止静默跳过。
