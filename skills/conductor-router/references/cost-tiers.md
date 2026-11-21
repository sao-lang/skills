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
| S5 独立 review 子代理 | ✗ → 轻量复核 | ✓ | ✓（高风险可再叠 metago） |
| S5 review_gate.py | `--lite`（见第五节） | 默认 | 默认 |
| S5 learn 回写 | ✗（须声明省掉） | ✓（dry-run → 人工确认后回写） | ✓（含被否决方案） |
| S5 overview L1 交接 | ✗（overview L1 一行即可） | ✓ | ✓ |

**不可裁剪的底线**（任何档位）：规格确认、失败测试先行、`verify.py` 证据、`source_purity --strict` 退出码 0、review 门禁（lite 也有自己的门禁）、overview L0。
**允许省掉的只是**：重复声明、全量工程文档、与本机风险无关的扫描、外部 skill 加载、独立子代理（仅 lite）。

## 三、判档声明（写进 S1 输出）

lite 一行式：
```
场景 N / 路径 X / 档位 lite；脚本：overview_path, verify, source_purity, review_gate --lite；
省掉：overview L1 交接, env_probe, 承诺台账, 影响面, 变更契约(spec), 学习回写(learn), 独立 review 子代理。如判断有误请直接纠正。
```
standard/full 用 routing.md §4.5 的完整模板，末尾追加 `成本档位：<standard|full>` 与 `省掉：<列表或无>`。

**升档触发**：执行中发现任一 high 条件命中（改动跨文件、出现契约变更、发现隐含清单、测试需要真实环境）→ 立即停下改声明升档，禁止沿用 lite 省略的步骤补跑就当没事。

## 四、lite 的轻量复核（替代独立子代理）

lite 不派子代理，但**必须换一种眼**做三项复核，写进 overview 的 `## 轻量复核（lite）` 章节：

1. **意图一致**：改动是否只实现承诺范围，有没有夹带重构/新功能 —— 附 `文件:行号`。
2. **边界与错误**：空值、异常分支、调用方是否受影响 —— 附 `文件:行号` 或写"无新增风险"并说明依据。
3. **证据**：`verify.py` 退出码 + `source_purity` 退出码，两个都要写。

小节必须含 `档位: lite` 与 `Blocker = 0`（无阻塞项也写 `Blocker = 0`）。`review_gate.py --lite` 机器校验：章节存在、档位标记、Blocker 清零、≥3 条复核项、≥2 条带行号或退出码证据；任一缺失退出码非 0，禁止 finish。
**若复核中发现 Blocker > 0**：立即升到 standard，派独立子代理，不能用 lite 蒙混过关。

## 五、与其他文档的关系

- 档位判定的语义部分归 `routing.md`（场景/路径/置信度），本文件只管"跑多深"。
- 独立 review 的完整规则归 `../../conductor-review/references/independent-review.md`：standard/full 仍强制子代理；本文件只定义 lite 的替代门禁。
- 承诺台账的防漏规则归 `../../conductor-ledger/references/commitment-ledger.md`：lite 因"无隐含清单"才跳过；一旦发现清单必须补建台账并升档。
- 变更契约的规则归 `conductor-spec`：standard/full 必出六段契约，Acceptance 注入台账；lite 跳过须声明。
- 学习回写的规则归 `conductor-learn`：standard/full 收尾留痕，默认 dry-run，禁止自动污染 skill；lite 跳过须声明。
- 证据口径不变：测试证据只认 `verify.py`，源码污染只认 `source_purity --strict`，拿不出退出码不得标完成。
