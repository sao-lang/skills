# 成本档位 · lite / standard / full

> 用途：在 S1 路由时决定**这一轮到底跑多少流程**，把"省积分"变成可判定的规则，而不是靠 AI 临场自觉。
> 核心认知：conductor 的成本大头不在脚本本身，而在**入口文档体积 + 每轮强制步骤 + 独立 review 子代理**。
> 低风险小改动走全套 = 空转；高风险大改动走 lite = 漏东西。判档必须写在路由声明里，可纠正。

## 一、三档判定（S1 必做）

按**从严**原则：任一 high 条件命中即升到对应档，不允许为了省积分降档。

| 条件 | lite | standard | full |
|---|---|---|---|
| 改动规模 | 单文件 ≤30 行（新增+删除） | 单模块多文件 / 单文件 >30 行 | 多模块 / 跨仓库 |
| 接口与依赖 | 无跨模块契约、签名、依赖变更 | 模块内接口调整 | 跨模块契约 / DB migration / 架构变更 |
| 隐含待办清单 | 无（规格里无多项承诺，无需台账） | 有清单，需承诺台账 | 有多来源清单 / 迁移台账 |
| 真实环境依赖 | 无，本地 `verify.py` 可验 | 有依赖信号但不新增生产路径 | 新增依赖真实环境的功能 / 迁移 |
| 设计决策 | 无，已有明确指令 | 局部设计，brainstorm+plan 精简 | 架构/设计规格需确认 |
| 用户要求 | "快一点 / 省积分 / 别跑全套" 时优先 | 默认 | "零遗漏 / 全量 / 深度审查 / 迁移别漏" |
| 置信度 | ≥0.8 且无假设 | ≥0.8 | 有假设或 <0.8（先问，不硬跑） |

**典型 lite**：单函数 bug 修复、单个 typo/注释修正、单文件小迭代、单文件测试补课、纯文档/注释同步（场景 11）。
**禁止 lite**：场景 1/2/6/7/12、任何迁移/架构/多模块改动、用户明确要求防漏或深度审查的任务。

## 二、各档裁剪表（"省掉"必须在路由声明里列出来）

| 节点 | lite | standard | full |
|---|---|---|---|
| S0 preflight | ✓ | ✓ | ✓ |
| S0 overview L0 | ✓（只建/续 + 一行 L1） | ✓ | ✓ |
| S0 overview L1 交接 | ✗（除非续接且 L0 信息不足） | ✓（有上次交接时） | ✓ |
| S0 env_probe | ✗ | 仅出现真实环境依赖信号时 | ✓ |
| S0 commitment_ledger init | ✗ | 有隐含清单时 | ✓ |
| S1 路由声明 | 一行式（场景+路径+档位+脚本） | 完整模板 | 完整模板 + 执行图细节 |
| S1 impact_analysis | ✗ | 无跨模块信号时 ✗ | ✓ |
| S2 brainstorm/plan | 一句话规格确认 | 精简（只写 Interfaces + 未决项） | 完整 + grill-design-SKILL.md / design-spec-template.md |
| S2 change-contract | ✗ | ✓ 六段契约 + `contract_check.py` | ✓ 六段契约 + Acceptance 入台账 |
| S3 TDD | ✓ RED→GREEN（小步） | ✓ | ✓ |
| S3 编码规则 | common + 当前语言 | 同 lite | 同 lite |
| S4 scan_gaps / debt_ledger | ✗ | ✓（debt 仅在新增 TODO 时） | ✓ |
| S4 verify.py | ✓（唯一测试证据） | ✓ | ✓ |
| S4 source_purity --strict | ✓（只扫改动文件） | ✓ | ✓（重构用 baseline + --scope） |
| S4 commitment_ledger check | ✗ | 有台账时 ✓ | ✓ |
| S5 独立 review 子代理 | ✗ → 轻量复核 | ✓ | ✓（高风险可加多轮复审） |
| S5 review_gate.py | `--lite`（见第五节） | 默认 | 默认 |
| S5 learn 回写 | ✗（须声明省掉） | ✓（dry-run → 人工确认后回写） | ✓（含被否决方案） |
| S5 overview L1 交接 | ✗（overview L1 一行即可） | ✓ | ✓ |

**不可裁剪的底线**（任何档位）：规格确认、失败测试先行、`verify.py` 证据、`source_purity --strict` 退出码 0、review 门禁（lite 也有自己的门禁）、overview L0。
**允许省掉的只是**：重复声明、全量工程文档、与本机风险无关的扫描、外部 skill 加载、独立子代理（仅 lite）。

## 三、器官级条件加载（同档位内的自适应跳过）

> 档位决定"跑多深"，本表决定"同档位内哪些器官这一轮真的要跑"。
> 执行中按**当前环境与用户输入**逐条判，命中跳过条件就跳过该器官；
> 每个跳过必须写进路由声明的"省掉"并带一句依据，禁止静默跳过；升档触发（第四节）优先于本表。

| 器官 | 默认 | 跳过条件（任一命中即跳） | 必跑条件（任一命中即跑） |
|---|---|---|---|
| conductor-memory | ✓ | 续接且 L0 索引卡已含全部所需上下文 → 只 append 不重写 | 新会话 / 新任务 |
| conductor-ledger | 视清单 | 规格里无多项承诺、无 finding、无模块清单 | 有隐含清单 / 多来源差异 / 迁移 |
| conductor-impact | 视信号 | 单文件单符号、无跨模块引用信号 | 跨模块契约 / 公共接口变更 / full 档 |
| conductor-brainstorm 规格固化 | standard/full | bug 修复（降为轻量：根因+回归要求一行）；纯文档场景 | 改码且规格有多条验收 |
| conductor-tdd | 改码必跑 | —（失败测试先行不可裁） | 一切改码 |
| conductor-debug | — | 非报错/非行为不符场景不加载 | 出现报错栈、复现需求 |
| conductor-review | 改码必跑 | —（门禁不可裁，lite 也有轻量复核） | 一切改码交付前 |
| conductor-memory 沉淀 | standard/full | 无可复用经验 → 写"本次无新增"留痕（不算跳过）；用户要求赶时间且改动琐碎 | 有用户纠正 / 新约定 / 踩坑 |
| conductor-subagent | 条件触发 | 任务 ≤2 / 紧耦合 / 强依赖跨任务联想（根因探索类）/ 用户要求省 token 或直接写 | 任务集 ≥3 个独立单元 / 多文件显式契约衔接 / 会话已长（不限改码，调研/分析/文档/审查同样适用） |
| conductor-git(commit) | 改码任务 GREEN 后 | 用户明确"先不提交" | 每任务 RED→GREEN 完成后 |

**判法**：三列冲突时从严（必跑条件 > 跳过条件 > 默认）；拿不准就跑，跳过漏事的代价远大于多跑一步。

## 四、判档声明（写进 S1 输出）

lite 一行式：
```
场景 N / 路径 X / 档位 lite；脚本：overview_path, verify, source_purity, review_gate --lite；
省掉：overview L1 交接, env_probe, 承诺台账, 影响面, 变更契约(spec), 学习回写(learn), 独立 review 子代理；
条件跳过：子代理（单任务直做）、git(commit)（用户先不提交）。如判断有误请直接纠正。
```
standard/full 用 routing.md §4.5 的完整模板，末尾追加 `成本档位：<standard|full>` 与 `省掉：<列表或无>`。

**升档触发**：执行中发现任一 high 条件命中（改动跨文件、出现契约变更、发现隐含清单、测试需要真实环境）→ 立即停下改声明升档，禁止沿用 lite 省略的步骤补跑就当没事。

## 五、lite 的轻量复核（替代独立子代理）

lite 不派子代理，但**必须换一种眼**做三项复核，写进 overview 的 `## 轻量复核（lite）` 章节：

1. **意图一致**：改动是否只实现承诺范围，有没有夹带重构/新功能 —— 附 `文件:行号`。
2. **边界与错误**：空值、异常分支、调用方是否受影响 —— 附 `文件:行号` 或写"无新增风险"并说明依据。
3. **证据**：`verify.py` 退出码 + `source_purity` 退出码，两个都要写。

小节必须含 `档位: lite` 与 `Blocker = 0`（无阻塞项也写 `Blocker = 0`）。`review_gate.py --lite` 机器校验：章节存在、档位标记、Blocker 清零、≥3 条复核项、≥2 条带行号或退出码证据；任一缺失退出码非 0，禁止收尾。
**若复核中发现 Blocker > 0**：立即升到 standard，派独立子代理，不能用 lite 蒙混过关。

## 六、与其他文档的关系

- 档位判定的语义部分归 `routing.md`（场景/路径/置信度），本文件只管"跑多深"。
- 独立 review 的完整规则归 `../../conductor-review/references/independent-review.md`：standard/full 仍强制子代理；本文件只定义 lite 的替代门禁。
- 承诺台账的防漏规则归 `../../conductor-ledger/references/commitment-ledger.md`：lite 因"无隐含清单"才跳过；一旦发现清单必须补建台账并升档。
- 变更契约的规则归 `conductor-brainstorm`（spec 已并入）：standard/full 必出六段契约，Acceptance 注入台账；lite 跳过须声明。
- 沉淀回写的规则归 `conductor-memory`（learn 已并入）：standard/full 收尾留痕，默认 dry-run，禁止自动污染 skill；lite 跳过须声明。
- 证据口径不变：测试证据只认 `verify.py`，源码污染只认 `source_purity --strict`，拿不出退出码不得标完成。
