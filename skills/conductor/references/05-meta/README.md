# conductor references 索引

> 34 份知识文档（含本索引），按需加载（渐进式披露）。本索引回答"什么情况读哪份"。
> 加载纪律：只在本表指定的阶段/触发条件下读对应文件，不要一次性全读。

## 目录结构（物理归类）

```
references/
├── 01-routing/       A 类：流程与路由（6 份）
├── 02-engineering/   B 类：工程纪律（5 份）
├── 03-coding-rules/  C 类：编码规则（8 份：common + 7 语言）
├── 04-guards/        D 类：规则与门禁（13 份）
└── 05-meta/          E 类：本索引 + roadmap（2 份）
```

下文表格里的路径均从 skill 根（`conductor/`）出发，如 `references/01-routing/routing.md`。

## A. 流程与路由（S0/S1 必读）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `references/01-routing/routing.md` | S1（读全文） | 场景路由规划器——把用户的话解析成执行图（结构算子→语义三问→I/O 契约→置信度） |
| `references/01-routing/router-prompt.md` | 需跨 agent 复用路由时 | routing 的自包含提示词版，可注入 Codex/CC/OpenCode/Droid |
| `references/01-routing/scenarios.md` | S1 只读「I/O 契约表」节；执行到具体场景时读该场景节 | 14 场景详细流程 + 工程能力链 + 场景 I/O 契约表。**不要整份加载** |
| `references/01-routing/cost-tiers.md` | S1 判档时（与 routing 同时） | 成本档位 lite/standard/full：判定条件、裁剪表、lite 轻量复核证据；专治小改动跑全套空转 |
| `references/01-routing/overview.md` | S0 / 收尾 | 会话记录格式（overviews/日期/文件），写入前脱敏 |
| `references/01-routing/skill-matrix.md` | 需查阶段加载表/工具来源时 | 阶段→skill 加载矩阵 + 外部工具清单 + 跨 agent 安装 |

## B. 工程纪律（superpowers 内化，S2–S5 按需读）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `references/02-engineering/engineering-catalog.md` | 想知道某个 superpowers skill 去哪了 | 15 个 skill 逐个去向 + 10 个具名能力的输入输出契约 |
| `references/02-engineering/engineering-workflow.md` | 按节读：S2 读 brainstorm+plan、S3 读 worktree、S5 读 finish | brainstorm（先调查再开口+回述+红旗）、writing-plans（Interfaces+Self-Review 五问）、worktree、finish 详解。**不要整份加载** |
| `references/02-engineering/engineering-tdd.md` | S3 | RED-GREEN-REFACTOR + Verify RED/GREEN 强制细节 + 5 借口 + 红旗 |
| `references/02-engineering/engineering-debugging.md` | 场景 8 解 bug | 4 阶段根因法 + 完成前验证 |
| `references/02-engineering/engineering-code-review.md` | S5 / 派子代理时 | 评审严重度分级 + subagent 派单契约/两段式/fix-loop 护栏 |

## C. 编码规则（写码事件触发，非全程加载）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `references/03-coding-rules/coding-rules-common.md` | 任何写码动作前 | 通用铁律：类型、禁魔法字符串、注释模板、长度基线、三道锁 |
| `coding-rules-<lang>.md` | 写对应语言代码时 | 该语言注释方案/语法/禁魔法字符串载体/长度基线/验证命令清单 |
| | | `<lang>` ∈ python, typescript, react, vue, go, rust, dart |

> 7 个语言文件靠通配符引用（不逐个列名），这是刻意的渐进式披露——只读当前语言那份。

## D. 规则与门禁（特定场景触发）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `references/04-guards/independent-review.md` | S5 改码场景交付前 | 独立 review 门禁完整规则：触发范围/派单契约/通过标准/fix-loop/与S4分工（SKILL.md 锁5 指针） |
| `references/04-guards/tech-debt-ledger.md` | S4/S5 收尾、债治理 | 技术债登记与量化口径（债指数/台账字段/进 overview 未完成项） |
| `references/04-guards/contract-migration.md` | 接口变更/写 DB migration 时（S2/S4/场景6/12） | 接口契约漂移四同步 + DB 迁移可逆性/锁表/兼容检查清单 |
| `references/04-guards/release-checklist.md` | 场景12/S5 发版时 | 版本命名/CHANGELOG/tag/回滚预案清单（发布编排） |
| `references/04-guards/examples-to-spec.md` | 用户举例/参考 X 那样/改这里时 | 样例→完整规格：归纳意图→6 维外推→分类确认→落地核对 |
| `references/04-guards/design-spec-template.md` | S2 写设计规格时（场景 1/2/3/4） | 规格模板：设计意图+技术栈+架构五要素+Approaches+未决清单+定稿自检 |
| `references/04-guards/git-commit-rules.md` | S3 绿后 / S5 提交前 | commit 时机、message 格式、暂存纪律（禁 add -A）、红线、检查清单 |
| `references/04-guards/security-redlines.md` | S4 安全核对 / 涉及密钥注入时 | 密钥脱敏、不可信输入 fail-closed、危险路由、成本闸门 |
| `references/04-guards/test-strategy.md` | S4 / 测试相关场景 | 测试金字塔、Mock 边界、覆盖率达标口径、假绿识别 |
| `references/04-guards/architecture-contracts.md` | 设计/改码/接线核对时 | 接线四问 + 断点模式清单，专治"内部通外部断" |
| `references/04-guards/source-purity.md` | S3 写码时 + S4 自省（所有改码场景） | 源码纯净守卫：把"禁 fake 实现/禁动态类型"软约束变退出码——source_purity.py 扫内存/假实现+Any/object，带留痕豁免；专治"测试代码污染源码/类型不具体" |
| `references/04-guards/commitment-ledger.md` | S0/S4/S5 公共节点；凡有隐含待办清单的场景（4/5/6/7/8/9/11/12） | 全场景防漏框架：五类根因→三道横切防线（外置事实/证据判定/换眼验证）、承诺台账状态机、多来源采集、防流程膨胀三纪律。先读这份 |
| `references/04-guards/migration-integrity.md` | 场景7 重构全程（先读 commitment-ledger.md） | 场景7 特化：迁移五步法 + migration_ledger shim + 行为等价/差分证据；通用机制不在此重复 |

## E. 项目元信息（维护 skill 自身时读）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `references/05-meta/roadmap.md` | 想知道某能力为何这样设计 / 加新场景前 | 已激活能力、P2 候选、激活原则、各次改造记录 |

## 加载优先级与冲突

0. **大文件按节读（省 token）**：`routing.md` + `cost-tiers.md` 在 S1 读全文；`scenarios.md` 路由时只读 I/O 契约表、执行到具体场景才读该节；`engineering-workflow.md` 按 S2/S3/S5 只读对应节。三个大文件都不要整份灌进上下文。
1. **工程纪律 vs 编码规则正交**：前者管"先写测试再实现"，后者管"实现写成什么样"，同时遵守。
2. **流程主控唯一**：conductor 自己执行全部工程阶段，A/B 类文档是它的步骤说明，不是外部 skill。
3. **工具是配角**：grill-design/graphify/code-quality-review 等只在指定阶段被调用，不占能力链节点。
4. **拿不出证据不标完成**：D 类门禁的退出码/行号是硬证据，写在 overview。
