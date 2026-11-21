---
name: conductor
description: 通用的 AI 开发工作流主控 skill。收到开发/重构/迁移/修 bug/项目初始化/迭代/架构设计/拷问代码或设计/代码库理解/文档同步/门禁验收/测试补课/文档清理，或"别漏需求/模块""别写内存版假实现/别用 Any"类防漏与源码纯净需求时加载：作为机体只做状态机、路由、门禁与器官调度；工程能力由 11 个器官 skill 执行。适用于支持 SKILL.md 的 agent。
---

# conductor · 开发工作流机体

> **机体—器官—环境**：conductor 只持有状态机 S0–S5、决策权与硬门禁；`skills/conductor-*` 是器官（单一能力）；14 场景是工作环境（声明调哪些器官）；`references/` 是共享组织（方法论与证据口径）。
> 铁律：**器官给结论和证据，不放行；conductor 才放行**。入口不重复器官内部步骤。

## 触发后必须先做

1. **定位 overview**：跑 `scripts/overview_path.py --project-root . --topic "<主题>"`；同会话续写 L0 主文件（≤8 行），详情在 `.details.md`，默认不读详情。
2. **路由并声明**：调 `conductor-router`，声明「场景 / 路径 / 成本档位 / 省掉 / 下一站」。**未声明不推进**；低置信先问，降级只读，绝不猜改码硬跑。

## 器官总线

完整映射见 `references/01-routing/organ-registry.md`（调用阶段、I/O、缺失降级、废弃 skill 清单）。**按表调用，不临场发挥**：

| 阶段 | 必调器官 | 按触发 |
|---|---|---|
| S0 | `conductor-overview` | `conductor-ledger`（有隐含清单） |
| S1 | `conductor-router` | `conductor-impact`（跨模块/full） |
| S2 | `conductor-brainstorm` | `conductor-spec`（standard/full）、自带拷问与规格模板 |
| S3 | `conductor-tdd` | 自带编码规则 |
| S4 | `conductor-tdd`（证据） | `conductor-ledger`、`conductor-impact` |
| S5 | `conductor-review` | `conductor-ledger`、`conductor-learn`（standard/full）、`conductor-git`（finish） |

成本档位 lite/standard/full 由 `conductor-router` 判定；规则见器官自带 `../conductor-router/references/cost-tiers.md`。lite 省掉交接/环境探测/台账/影响面/活规格/学习回写/独立子代理，保留规格确认、TDD、`verify.py`、`source_purity`、review 门禁。

**条件加载**：同档位内器官是否真的跑，按 `../conductor-router/references/cost-tiers.md` 第三节的条件加载表判（如单文件小修跳 worktree、无清单跳台账）；每个跳过写进声明"省掉"并带依据，禁止静默跳过。

## 十四场景 = 工作环境（只声明器官，不重复步骤）

| 场景 | 路径 | 器官链 |
|---|---|---|
| 1 初始化 / 4 开发 | 改码 | router → brainstorm → spec → tdd → ledger → review → learn → git(worktree→commit→finish) |
| 2/3 设计 | 文档 | router → brainstorm（自带拷问方法；确认后可出 spec 草稿） |
| 5 迭代 / 6 设计驱动重构 | 改码 | router → spec → impact → tdd → ledger → review → learn → git(worktree→commit→finish) |
| 7 项目重构 | 改码 | router → ledger(migration shim) → spec → impact → tdd → review → learn → git(commit→finish) |
| 8 解 bug | 改码 | router → debug → spec(轻量) → tdd → review → learn → git(commit→finish) |
| 9 拷问 / 10 理解 | 只读 | router → brainstorm / impact → overview（结束） |
| 11 文档同步 | 文档 | router → brainstorm → overview |
| 12 门禁验收 | 验证 | router → review（+ledger） |
| 13 测试补课 | 验证 | router → tdd → review → learn → git(commit) |
| 14 文档清理 | 文档·清理 | router → overview（确认无依赖后执行，排链尾） |

场景细节与 I/O 契约见 `../conductor-router/references/scenarios.md`：**S1 只读 I/O 契约表，执行到某场景才读该节**。

## 硬门禁（不可下放给器官）

- **规格未确认不动手**；**无失败测试不算实现**；**拿不出证据（命令+退出码/行号）不标完成**。
- 测试证据只认 `scripts/verify.py`；写码后必跑 `scripts/source_purity.py check --strict`（fake 实现/动态类型/无注释占位，重构用 baseline + `--scope`）。
- 改码交付前必过 `scripts/review_gate.py`：standard/full 走独立子代理，lite 走 `--lite` 轻量复核；Blocker 未清零禁止 finish。
- 有隐含清单必建台账，`commitment_ledger.py check --strict` 退出 0 才准 finish；禁止刷状态、禁止静默跳过。
- 真实环境优先：无环境不砍功能、不写 fake 冒充 adapter、不留无注释跨模块占位；环境缺失登记「环境阻断」，禁改断言造假绿。

## 参考与脚本

- 参考文档按需加载，索引见 `references/05-meta/README.md`：`../conductor-router/references/routing.md`/`../conductor-router/references/cost-tiers.md`/`organ-registry.md` 在 S1 读，`../conductor-router/references/scenarios.md`、`../conductor-brainstorm/references/engineering-workflow.md`、`../conductor-spec/references/spec-method.md`、`../conductor-learn/references/learning-method.md` 按节，其余触发才读。
- 16 个工作流入口：`preflight / overview_path / env_probe / verify / scan_gaps / review_gate / impact_analysis / debt_ledger / release_notes / commitment_ledger / migration_ledger / source_purity / intent_gaps / sync-global / contract_check / learn_capture`；其中 6 个重复入口是薄 shim，实现只在器官目录；另有 4 个测试/审计脚本 `collaboration_skill_audit / organ_contract_test / organ_effect_test / script_parity_test`；参数见 `skill-matrix.md`。
- 外部 skill 缺失必须显式降级并在 overview 写「缺失 X / 影响 Y / 降级 Z」，禁止静默跳过。
