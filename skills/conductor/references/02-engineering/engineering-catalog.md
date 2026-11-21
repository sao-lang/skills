# 工程能力目录 · superpowers 全景整合表

> 本文件回答两个问题：**superpowers 的每个 skill 去哪了？**、**conductor 的流程靠哪些能力跑起来？**
> 来源：obra/superpowers（15 个 skill）+ 本地压缩重制版（5 份 reference）。
> 整合原则：不是把 skill 文件塞进项目，而是把每个 skill **内化为 conductor 的具名工程能力**，
> 挂进 14 场景的具体阶段。能力是 conductor 流程里的节点，有名字、有输入输出契约、有详情文件。

## 0. 核心理念（4 条，贯穿所有能力）

1. **测试驱动**——永远先写测试，没有失败测试不算实现。
2. **系统化优先于临场发挥**——用流程取代猜测。
3. **降低复杂度是首要目标**——简单优于聪明（配合最小改动原则）。
4. **证据优于声称**——宣布完成前先验证，拿不出证据不得标完成。

> 这 4 条是跨器官的全局纪律，由 conductor 持有；各器官文档不重复收录。

## 1. 全景盘点（15 个 skill 逐个交代去向）

| # | superpowers skill | 去向 | conductor 能力名 | 挂载场景 / 阶段 | 详情文件 |
|---|---|---|---|---|---|
| 1 | brainstorming | ✅ 整合 | `brainstorm` | 场景 1/2/3/4/5 的 S2 | ../../../conductor-brainstorm/references/brainstorm-plan.md |
| 2 | writing-plans | ✅ 整合 | `plan` | 场景 1/4/5/6 的 S2 | ../../../conductor-brainstorm/references/brainstorm-plan.md |
| 3 | （隔离工作区类上游 skill） | ❌ 不采用 | — | 直接在当前工作区小步提交；隔离带来的目录/环境成本高于收益（2026-11-21 决策） | — |
| 4 | subagent-driven-development | ✅ 独立成器官 | `conductor-subagent` | 计划就绪进入实现阶段，条件触发 | ../../../conductor-subagent/SKILL.md + ../../../conductor-subagent/references/dispatch.md |
| 5 | executing-plans | ✅ 整合 | `execute`（分批模式） | 场景 4/5 S3 备选（需人在场） | —（一句话方法：分批执行 + 人工检查点，每批结束停下向用户汇报再继续） |
| 6 | test-driven-development | ✅ 整合 | `tdd` | 场景 4/5/6/7/8/13 的 S3 | ../../../conductor-tdd/references/engineering-tdd.md |
| 7 | requesting-code-review | ✅ 整合 | `review` | 所有改码场景（每任务间 + S5） | ../../../conductor-review/references/engineering-code-review.md |
| 8 | receiving-code-review | ✅ 整合 | `receive-review` | 横切：收到反馈时 | ../../../conductor-review/references/engineering-code-review.md |
| 9 | （分支收尾类上游 skill） | ❌ 不采用 | — | 交付由 review 门禁 + 用户决策收口，不做分支菜单/清理流程（2026-11-21 决策） | — |
| 10 | systematic-debugging | ✅ 整合 | `debug` | 场景 8；场景 6 接线失败时 | ../../../conductor-debug/references/engineering-debugging.md |
| 11 | verification-before-completion | ✅ 整合 | `verify` | 场景 12 门禁 + 所有改码场景收尾 | ../../../conductor-tdd/scripts/verify.py（shim `scripts/verify.py`）+ 本表 verify 契约行 |
| 12 | using-superpowers | ❌ 舍弃 | — | 它是 superpowers 的入口/触发说明；conductor 自己就是入口，不需要 | — |
| 13 | diagnosing-superpowers | ❌ 舍弃 | — | superpowers 自检工具，诊断"superpowers 是否装好"；与 conductor 无关 | — |
| 14 | writing-skills | ❌ 舍弃 | — | "怎么写 skill"元能力，非开发流程；造 skill 用 skill-creator 即可 | — |
| 15 | dispatching-parallel-agents | ♻️ 并入 | `conductor-subagent` + 路由并行算子 | 独立任务派发归 conductor-subagent；场景链并行归 routing 并行算子 | ../../../conductor-subagent/references/dispatch.md |

**结论**：10 个整合为具名能力（其中 subagent-driven 独立成器官），1 个并入已有机制，4 个舍弃或不采用——没有遗漏，也没有无理由丢弃。

## 2. 具名工程能力契约（conductor 流程的节点）

这些能力是 conductor 场景链里真正被调用的节点。每个都有输入/输出契约——场景衔接时按契约传递，与 `../../../conductor-router/references/scenarios.md` 的场景 I/O 契约表同构。

| 能力名 | 一句话职责 | 输入契约 | 输出契约 | 入口阶段 |
|---|---|---|---|---|
| `brainstorm` | 苏格拉底式提问逼清需求，逐块确认设计 | 粗糙需求 | 用户签字的设计文档 | S2 |
| `plan` | 拆成 2-5 分钟、精确到文件与验证的任务 | 设计文档 | 可执行实施计划 | S2 |
| `subagent` | 按判据派全新上下文子代理执行任务，两段评审 | 自包含任务 brief | 任务结论（一行）+ 两段评审通过 | S3（条件触发） |
| `tdd` | RED→GREEN→REFACTOR，测试前代码一律删 | 期望行为描述 | 通过测试的实现 + 证据 | S3（每任务内） |
| `debug` | 4 阶段根因：复现→追踪→纵深防御→条件等待 | 故障现象 | 根因 + 修复 + 回归测试 | 场景 8 主体 |
| `review` | 对照计划逐条查，按严重度分级 | 任务产出 + 计划 | 分级评审结论（Critical 阻断） | 每任务间 + S5 |
| `receive-review` | 把反馈当事实，改完回到验证仍绿 | 评审反馈 | 修改后的产出（仍绿） | 横切 |
| `verify` | 完成前跑真实验证，拿退出码/测试证据。方法：宣布完成前先跑**能证明真的完成**的命令，证据是测试输出/linter 退出码/覆盖率数字，不是感觉；与 S4 门禁（scan_gaps+verify）叠加，不重复造流程 | 完成声明 | 验证证据（退出码/覆盖率） | S4 + S5 前 |

## 3. 能力编排规则

1. **场景即能力链**：每个场景在 `../../../conductor-router/references/scenarios.md` 里写成 `能力A → 能力B → ...`，能力名必须在本表可查。
2. **契约传递**：前一能力的输出契约必须满足后一能力的输入契约；不满足则停下问用户（与 routing 的 I/O 校验同构）。
3. **按需裁剪**：只读/文档/验证路径的场景只调用子集（如场景 9/10 不调用 `tdd`/`review` 的改码变体）。
4. **方法已内化**：grill-design / code-quality-review / handoff 等方法已并入器官，graphify / ponytail 等已废弃，
   它们不占据能力链节点；例如 `brainstorm` 使用 `grill-design-SKILL.md` 做设计拷问。
5. **缺失降级**：某能力的详情文件缺失 → 按该能力"一句话职责 + 契约"最小执行，并在 overview 标注，禁止静默跳过。
