---
name: conductor
description: 通用的 AI 开发工作流主控 skill。收到开发/重构/迁移/修 bug/项目初始化/迭代/架构设计/拷问代码或设计/代码库理解/文档同步/门禁验收/测试补课/文档清理，或"别漏需求/模块/调用方""别写内存版假实现/别用 Any"类防漏与源码纯净需求时加载：内化工程纪律（brainstorm→plan→TDD→review→finish），负责场景路由与成本分档、承诺台账、证据门禁、独立 review、会话记录。适用于支持 SKILL.md 的 agent。
---

# conductor · 开发工作流主控

> 唯一流程主控：工程纪律已内化在 `references/02-engineering/`，外部 skill 只在指定阶段按档位作工具。
> **省成本第一原则：先判档，再执行**——能 lite 不 standard，能 standard 不 full；省掉的步骤必须在路由声明里写明。

## 触发后必须先做

1. **定位 overview**：`python scripts/overview_path.py --project-root . --topic "<主题>"` → 按返回 `action` 建/续；会话指针 `.conductor-session.json` 锚定，同会话多轮归同一文件。续接**只读 L0（≤12 行）**，必要时再看 L1/L2。格式见 `references/01-routing/overview.md`。
2. **路由并声明**：按 `references/01-routing/routing.md` 把用户的话解析成执行图，声明「场景 / 路径 / 成本档位 / 脚本 / 禁止项 / 下一站」。**未声明不推进**；置信度低先问用户，失败降级只读，绝不猜改码场景硬跑。

## 成本档位（S1 先判，写进声明）

| 档位 | 适用 | 保留 | 省掉 |
|---|---|---|---|
| **lite** | 单文件 ≤30 行改动 / 单函数 bug / 小注释或文档同步；无跨模块契约、无隐含清单、本地可验证 | preflight、overview L0、规格确认、TDD、`verify.py`、`source_purity`、轻量复核（`review_gate.py --lite`） | handoff、env_probe、承诺台账、影响面、独立 review 子代理、外部 grill/handoff skill、完整工程文档 |
| **standard**（默认） | 单模块功能改动 / 普通迭代 / 多函数 bug | lite 全部 + 独立 review 子代理 + 承诺台账（有清单时）+ 环境探测（有真实环境依赖时） | 架构拷问、影响面（无跨模块时）、full 全套 |
| **full** | 多模块 / 架构 / 迁移重构 / 高风险 / 用户要求零遗漏或深度审查 | 完整 S0–S5 + 独立 review + 承诺台账 + 影响面 + 相关 guard 文档 | 无 |

任一 lite 条件被打破立即升档；用户说"省积分 / 快一点 / 别跑全套"时取最低可用档，并在声明中列出省掉的步骤。完整判定、裁剪表与 lite 复核证据见 `references/01-routing/cost-tiers.md`。

## 十四场景（细节按节读 scenarios.md）

| 场景 | 路径 | 场景 | 路径 |
|---|---|---|---|
| 1 初始化 | 改码 | 8 解 bug | 改码 |
| 2 架构设计 | 文档 | 9 拷问代码/设计 | 只读 |
| 3 补充设计 | 文档 | 10 代码库理解 | 只读 |
| 4 项目开发 | 改码 | 11 文档/注释同步 | 文档 |
| 5 项目迭代 | 改码 | 12 门禁验收/发布 | 验证 |
| 6 设计驱动重构 | 改码 | 13 测试补课 | 验证 |
| 7 项目重构 | 改码 | 14 文档/资源清理 | 文档·清理 |

> 工程能力链与 I/O 契约表见 `references/01-routing/scenarios.md`：**S1 只读「I/O 契约表」，执行到某场景才读该节，不整份加载**。

## S0–S5 必做（按档位裁剪）

- **S0**：preflight → overview 定位/建 → handoff / env_probe / 承诺台账按档位触发 → 写 L0。
- **S1**：执行图 + 场景/路径/档位声明；改码/迭代在 standard/full 跑 `impact_analysis.py`；场景 7 跑 `migration_ledger.py init`（新增模块必 `--merge`）。
- **S2**：brainstorm + plan（lite 只做一句话规格确认）；**规格未确认不动手**。写规格用 `design-spec-template.md`，拷问/架构按触发加挂。
- **S3**：TDD RED→GREEN；写码前读 `coding-rules-common.md` + 当前语言那份；绿后按 `git-commit-rules.md` 提交。
- **S4**：`scan_gaps.py` → `verify.py`（测试证据只认它）→ `debt_ledger.py`；`source_purity.py check --strict`（fake 实现 / 动态类型 / 无注释占位；重构先 baseline + `--scope`）；有台账则 `commitment_ledger.py check --strict`。lite 只跑 verify + source_purity。
- **S5**：改码交付按档位过 review 门禁——standard/full 用全新上下文子代理 + `review_gate.py`，lite 用 `review_gate.py --lite` 轻量复核；有台账则零未勾销才 finish；收尾写 overview + handoff（lite 只写 L1 一行）。

## 五道锁与铁律

- **锁1 写码前**：未读编码规则禁止产出代码；**锁2 写码中**：边写边对照注释模板 / 类型 / 禁魔法串 / 长度基线；**锁3 写码后**：formatter/linter + `source_purity --strict` 退出码 0；**锁4 提交前**：测试绿、暂存区只含本次文件、禁 `git add -A`；**锁5 交付前**：按档位过 review 门禁。
- **铁律**：①规格未确认不动手 ②无失败测试不算实现 ③自省未过不进 review ④拿不出证据（命令+退出码/行号）不得标完成 ⑤测试证据只认 `verify.py` ⑥改码交付必过对应档 review 门禁 ⑦真实环境优先：无环境不砍功能、不写 fake 冒充 adapter、不散落 Any/object、不留无注释跨模块占位（见 `source-purity.md`）⑧防漏靠台账：有隐含清单必建，S5 零未勾销才 finish（见 `commitment-ledger.md`）。

## 参考文档与脚本（按需，不整份读）

- 34 份 reference 的「何时读哪份」见 `references/05-meta/README.md`：`routing.md` 读全文，`scenarios.md` 与 `engineering-workflow.md` 按节，其余触发才读；编码规则写码时才读当前语言那份。
- 14 个确定性脚本（输出即证据）：`preflight / overview_path / env_probe / verify / scan_gaps / review_gate / impact_analysis / debt_ledger / release_notes / commitment_ledger / migration_ledger / source_purity / intent_gaps / sync-global`；参数与证据口径见 `references/01-routing/skill-matrix.md`。
- graphify（跨文件问题）与 handoff（交接）按档位调用，规则见 `skill-matrix.md`；外部 skill 缺失必须显式降级并在 overview 写「缺失 X / 影响 Y / 降级 Z」，禁止静默跳过。
