---
name: conductor
description: 通用的 AI 开发工作流主控 skill。当收到开发、重构、修 bug、项目初始化、迭代、架构设计、或"拷问代码/设计"类需求时，本 skill 应被加载：它是唯一的流程主控，内置完整工程纪律（头脑风暴/写计划/worktree/子代理/TDD/系统化调试/代码评审/收尾），并负责场景路由、会话记录、缺口台账自省、影响面与技术债治理、门禁与交接。适用于 Claude Code、Codex、OpenCode、Droid 等支持 SKILL.md 的通用 agent。
---

# conductor · 开发工作流主控

> 指挥家：本 skill 亲自执棒整条开发流程（路由→工程纪律→门禁→交接）；需要专门工具时调用
> grill-design / code-quality-review / graphify / handoff 等，它们只按本 skill 指定的阶段被加载。

## 定位（必读）

- **唯一流程主控**：不再有"治理外壳 + 外部工程内核"两套工作流。
- **工程纪律已内化**：brainstorm → plan → worktree → 子代理 → TDD → 调试 → review → finish，
  固化在 `references/02-engineering/engineering-*.md`，由 conductor 自己执行。
- **外部 skill 只是工具**：不定义阶段，只在指定阶段被加载。

## 触发后必须先做的两件事

1. **定位 overview 文件**：S0 跑 `scripts/overview_path.py --project-root . --topic "<主题>"`，按返回的 `action`（append/create）与 `path` 建/续会话记录。脚本用会话指针 `.conductor-session.json` 锚定——同会话多轮自动归到同一文件，换任务时带 `--new-session`。详见 `references/01-routing/overview.md`。
2. **路由 = 规划执行图**（`references/01-routing/routing.md`）：把用户的话解析成执行图（节点=场景，边=链/分支，模式=路径）。
   - 五层：结构算子定拓扑 → 语义三问定场景+路径 → `scenarios.md` 的 I/O 契约校验衔接 → 置信度+**假设明示**+待澄清 → 高≥0.8 执行/中 0.5–0.8 确认/低<0.5 问用户。
   - 失败降级到只读场景 9/10，**绝不猜改码场景硬跑**；每节点完成后重规划；用户一句话纠正即重路由。**未声明不推进。**
   - 跨 agent 复用：`references/01-routing/router-prompt.md` 是上述规划器的自包含提示词，可单独注入任意 agent。

## 十四场景与流程裁剪

| 场景 | 走的工程阶段（本 skill 主控） | 额外加载 |
|---|---|---|
| 1 项目初始化 | brainstorming → writing-plans（止步） | overviews 建库、技术选型拷问 |
| 2 架构设计 | brainstorming + 设计树（止步于架构规格） | grill-design + architecture-contracts |
| 3 补充设计 | 局部 brainstorm（只补缺口） | 定位已有设计，禁重写既有结论 |
| 4 项目开发 | 全程 brainstorm→plan→TDD→review→finish | S0/S4 + ponytail/caveman/coding-rules |
| 5 项目迭代 | brainstorm（轻）→ plan → TDD → review | **impact_analysis** 影响面 + 回归检查 |
| 6 设计驱动重构 | 核设计差异 → TDD 锁行为 → review → finish | **contract-migration** 契约核对，禁夹带 |
| 7 项目重构 | TDD 锁行为 → review → finish | impact_analysis + ponytail，禁夹带新功能 |
| 8 解 bug | debugging → TDD 复现 → review | **最小复现构造**（engineering-debugging）+ 回归证据 |
| 9 拷问代码/设计 | 不跑工程阶段（纯只读） | grill-design / grill-me / code-quality-review，出清单不改码 |
| 10 代码库理解 | 不跑工程阶段（纯只读） | graphify + scan_gaps + architecture-contracts |
| 11 文档/注释同步 | 局部（只核差异，不跑代码 TDD） | grill-design + architecture-contracts，出差异清单；含注释/docstring 补全 |
| 12 门禁验收/发布 | 不跑工程阶段（只验证） | preflight+verify+scan_gaps+review 全套 + **release-checklist** |
| 13 测试补课 | TDD 变体（只补测试） | test-strategy.md，出测试 + 覆盖率证据 |
| 14 文档/资源清理 | 不跑工程阶段（S1→确认无依赖→执行→结束） | 删除/归档/移动文档、改无关文档内容；无代码改动不跑 TDD/verify；**在场景链中销毁必须排最后**（见 routing §3.5） |

详细步骤见 `references/01-routing/scenarios.md`（含场景 I/O 契约表，链式组合做类型校验）。

> **references 导航**（省 token 硬纪律）：30 份文档"何时读哪份"见 `references/05-meta/README.md`（五类）。**按阶段与粒度渐进加载，禁止一次性全读**：
> - `routing.md` / `scenarios.md`：S1 路由只需读 routing 全文 + scenarios 的**「I/O 契约表」**一节判衔接；**执行到某个具体场景时，才读 scenarios 对应那一节**，不整份加载。
> - `engineering-workflow.md`：S2 读 brainstorm+plan 两节、S3 读 worktree、S5 读 finish——**只读当前阶段那一节**，不整份加载。
> - 其余 reference 按 `README.md` 索引的触发条件加载。

## 阶段 → skill 加载矩阵

每步先声明主控，再声明加载项与禁止项。完整表（含 skill 仓库地址与跨 agent 安装）见 `references/01-routing/skill-matrix.md`。

| 阶段 | 主控 | 加载 / 调用 |
|---|---|---|
| S0 会话开始 | 本 skill | `preflight.py` 预检 → **实际调用 `handoff`** → 跑 `overview_path.py` 定位/建 overview（会话指针锚定，见 overview.md）→ 跑 `env_probe.py` 探测真实环境需求/可用性写入 overview 环境节；续接先读 L0（~10 行），按需读 L1/L2，禁止全量 |
| S1 场景路由 | 本 skill | `routing.md` 规划执行图 + 声明 skill 组/禁止项/下一站；命中样例信号（举例/参考X那样）启用 `examples-to-spec.md`；改码/迭代场景跑 `impact_analysis.py` 出影响面草稿 |
| S2 设计计划 | 本 skill | `engineering-workflow.md`（brainstorm+plan）；写规格用 `design-spec-template.md`；拷问加 `grill-design`；架构类加 `architecture-contracts`（含 §4.5：依赖真实环境的功能必须进计划，不许因无环境预先砍掉）；按 `examples-to-spec.md` 补全样例；涉接口/迁移加 `contract-migration.md` |
| S3 TDD 实现 | 本 skill | `engineering-tdd.md` + `engineering-workflow.md`（worktree/subagent）；挂 ponytail+caveman+coding-rules；按影响面清单核关联项；绿后按 `git-commit-rules.md` 提交 |
| S4 自省补强（改码） | 本 skill | `scan_gaps.py`→`verify.py`（覆盖率门禁，只认其输出为测试证据，见 `test-strategy.md` §5）→`debt_ledger.py`（技术债台账）；拷问加 grill-me；安全核对 `security-redlines.md`；接口/迁移核对 `contract-migration.md`；**按 `architecture-contracts.md` §4.5 核对依赖真实环境的功能是否仍在生产代码里（没环境≠砍功能）**；**执行者自查 L1/L2，不替代 S5** |
| S4 分析（只读） | 本 skill | graphify / scan_gaps / review；**不跑 verify、不触发独立 review 门禁** |
| S5 review 收尾 | 本 skill | `engineering-code-review.md`+`engineering-workflow.md`（finish）；解 bug 读 `engineering-debugging.md`；**改码场景交付前必经独立 review（见下）**；深度审查加 `metago-code-review-deep`；发布走 `release-checklist.md`+`release_notes.py`；按 `git-commit-rules.md` 提交；收尾 handoff + 写 overview |

**确定性脚本**（scripts/，非 skill，输出即证据写入 overview）：`preflight.py` 依赖预检 · `overview_path.py --topic <主题>` 会话指针定位 overview（换任务 `--new-session`）· `env_probe.py` 真实环境需求/可用性探测（S0 写 overview，用户要真实测试时给入口命令）· `verify.py --lang <lang>` 验证+覆盖率门禁 · `scan_gaps.py` 缺口草稿 · `review_gate.py --overview <path>` 独立review证据门禁（非改码加 `--waived`）· `impact_analysis.py --symbols/--files/--diff` 变更影响分析 · `debt_ledger.py` 技术债台账 · `release_notes.py --since <tag>` CHANGELOG草稿。

### 场景 × 阶段矩阵（S1 硬输出，决定跳过哪些阶段）

| 路径 | 场景 | S0 | S1 | S2 | S3 | S4 | S5 |
|---|---|---|---|---|---|---|---|
| 改码 | 1/4/5/6/7/8 | ✓ | ✓ | ✓ | ✓ | 改码变体 | ✓ |
| 只读 | 9/10 | ✓ | ✓ | — | — | 只读变体 | —（写 overview 后结束） |
| 文档 | 2/3/11 | ✓ | ✓ | 核差异 | S3' 只改文档 | 核签名 | ✓ |
| 文档·清理 | 14 | ✓ | ✓ | — | 确认无消费者依赖后执行清理 | — | —（写 overview 后结束） |
| 验证 | 12/13 | ✓ | ✓ | — | 13 补测试/12 跳过 | ✓ | ✓（含独立 review 门禁） |

**只读出口**：只读路径出口是"发现清单/代码地图/证据台账已交付且可追溯"，**不是"测试全绿"**——禁止对无代码改动的场景套用门禁，否则空转。

## 代码规则如何生效

规则不是第二个 skill，靠"会话级约束 + 写码事件触发"生效：S1 种下常驻一句话指针"写码前先读 `references/03-coding-rules/coding-rules-common.md` 与当前语言 `coding-rules-<lang>.md`"，规则正文直到写码那刻才读（渐进式披露）。工程纪律与规则正交：前者管"先测试再实现"，后者管"实现写成什么样"。规则文件：`coding-rules-common.md` + `coding-rules-{python,typescript,react,vue,go,rust,dart}.md`（<lang> 靠通配符引用，只读当前语言那份）。

## 强制机制（五道锁）

- **锁 1 · 写码前**：未读规则文件禁止产生代码；违反则该步无效、回退重做。
- **锁 2 · 写码中**：每写函数/类/循环边写边对照注释模板、类型原则、禁魔法字符串、长度基线。
- **锁 3 · 写码后**：跑 formatter/linter/type-checker/注释检查，退出码非 0 → 禁止进 review、禁止标完成。
- **锁 4 · 提交前**：按 `git-commit-rules.md` 核对——测试绿、暂存区只有本次文件、message 合规；**禁 `git add -A`/`.` 盲加混入他人改动**；提交后核对 HEAD。
- **锁 5 · 交付前独立 review**：改码场景 finish 前必须由独立子代理跑 `code-quality-review`，Blocker 清零才准交付；`review_gate.py` 机器校验 overview 证据，退出码非 0 禁止交付。**完整规则见 `references/04-guards/independent-review.md`（触发范围/派单契约/通过标准/fix-loop/与S4分工）。**

例外必须显式声明并记入 overview（如生成代码、第三方文件、vendor 边界），禁止以"技术债"名义静默放行——欠账一律登记（`debt_ledger.py` + `tech-debt-ledger.md`）。

## skill 加载纪律

声明"加载 X"时必须真的调用：① S0 跑 preflight 确认存在；② 加载失败必须显式降级并在 overview 写"缺失X/影响Y/降级Z"，禁止静默跳过或假装加载；③ 关键依赖 `handoff`（S0）缺失须告知用户并给安装命令；④ 只读路径 9/10 不强依赖 handoff，但需标注"无交接上下文"。工程纪律已内置，无外部主控依赖。

## 铁律（贯穿全程）

1. 规格未确认不动手。
2. 无失败测试不算实现。
3. 自省未过不进 review。
4. 拿不出证据（测试行号 / linter 退出码 / 覆盖率）不得标完成。
5. 工程纪律已内置：S2/S3/S5 读 `engineering-*.md` 执行，不加载外部流程 skill。
6. 测试证据只认 `verify.py`：裸跑 pytest/vitest 不算 S4 证据；覆盖率命令缺失或阈值无着落，退出码非 0，禁止进 review、禁止标完成。
7. 改码场景交付前必经独立 review：全新上下文子代理跑 `code-quality-review`，Blocker 清零才准 finish；`review_gate.py` 机器校验证据，退出码非 0 禁止交付（见 `independent-review.md`）。
8. **无真实环境 ≠ 砍功能**：依赖 Docker/DB/Redis 的功能照常写生产实现，只在真实环境能验证的部分登记"待验证"未完成项；禁止以"环境不支持"为由删功能或只写 fake 标完成（见 `architecture-contracts.md` §4.5）。用户要真实测试时跑真实入口（如 `tests/integration/`），不复用 mock 命令。

## 会话记录（overviews）

**一个会话一个 md**（不是一轮一个），由 `scripts/overview_path.py` 用会话指针 `.conductor-session.json` 定位：同会话多轮归同一文件，换任务带 `--new-session`。存项目根 `overviews/YYYY-MM-DD/`，格式见 `references/01-routing/overview.md`，写入前脱敏。**按 overview.md「记什么/不记什么」过滤**：与项目无关的对话、未采纳未落实的调研/方案、中间试错一律不写；每个问题带状态（已解决/待跟进/已否决）。
**分层读写**：每份 overview 顶部必有 ≤12 行 L0 索引卡（场景/闸门/产物/未完成项/下一步）；续接先只读 L0，按需读 L1/L2；>30 行详情独立成 `.xxx.md` 主文件只留路径——禁止把整份 overview 全量灌进上下文。

## 代码理解工具（graphify）

场景 9/10 跨文件问题（谁调用/改了波及什么）用 `graphify` 替代 grep/read 循环：`pip install graphifyy` → `graphify install` → `/graphify .` 建图，查询卡 2000 token。给的是**带源码位置的上下文**不是已验证答案，关键边须打开源码核对；不替代 `scan_gaps.py`。短会话/单文件问题不用（冷启动成本）。

## 跨 agent 与会话交接

本 skill 目录为通用结构：Claude Code 放 `.claude/skills/conductor/`、Codex 放 `.codex/skills/conductor/`、OpenCode 放 `.opencode/skill/conductor/`，或用 `npx skills add <repo> --skill conductor`。不依赖任何特定 agent 的内置工具名。会话交接用 `handoff`（S0/S5）。
