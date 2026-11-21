# conductor 适配模板（mode=conductor）

> 被 conductor 调用时加载：把 14 场景、S0–S5 阶段、器官/脚本/门禁映射为执行图节点。
> 核心引擎保持通用；本文件只是“场景适配层”——把 conductor 的规定流程翻译成图。

## 一、场景 → 节点骨架映射

| 场景 | 路径 | 节点骨架（kind:ref） |
|---|---|---|
| 1 初始化 | 改码 | research(查目录) → skill:brainstorm(规格) → tool:tdd.verify → skill:review → gate(收尾) |
| 2 架构设计 | 文档 | research(现状) → skill:brainstorm(拷问+规格) → ask(确认) → action(写设计文档) |
| 3 补充设计 | 文档 | research(读已有设计) → skill:brainstorm(补未决) → ask(确认) → action(文档增量) |
| 4 新功能 | 改码 | skill:brainstorm(规格) → [subagent 条件] → loop(tdd: RED→GREEN) → git(commit) → skill:review → gate |
| 5 迭代 | 改码 | 同 4，前置 research(现状) |
| 6 设计驱动重构 | 改码 | research(读设计) → skill:brainstorm(规格) → skill:impact → [subagent] → loop(tdd) → review → gate |
| 7 项目重构/迁移 | 改码 | tool:migration_ledger(建台账) → skill:impact → loop(tdd) → tool:commitment_ledger.check → review → gate |
| 8 解 bug | 改码 | skill:debug(根因) → skill:brainstorm(轻量契约) → research(最小复现) → loop(tdd) → review → gate |
| 9 拷问设计 | 只读 | research(读设计) → skill:brainstorm(拷问方法) → think(问题清单) → action(写 overview) → END |
| 10 理解代码 | 只读 | research(读代码) → skill:impact(调用关系) → think(代码地图) → action(写 overview) → END |
| 11 文档同步 | 文档 | research(扫签名) → action(改文档) → tool:verify(核签名) → gate |
| 12 门禁验收 | 验证 | tool:verify → tool:scan_gaps → tool:review_gate → gate(全绿?) |
| 13 测试补课 | 验证 | skill:tdd(补测试) → loop(RED→GREEN) → skill:review → gate |
| 14 文档清理 | 清理 | gate(确认无消费者) → action(删除/归档) → action(写 overview) → END |

## 二、conductor 模式的节点 ref 对照表

| kind | ref 取值 | 说明 |
|---|---|---|
| `tool` | `verify.py` / `preflight.py` / `scan_gaps.py` / `source_purity.py` / `review_gate.py` / `commitment_ledger.py` / `migration_ledger.py` / `impact_analysis.py` / `removal_check.py` / `sync-global.py` | 脚本名，参数写进 action |
| `skill` | `conductor-brainstorm` / `conductor-spec`(已并入 brainstorm)/ `conductor-tdd` / `conductor-review` / `conductor-memory` / `conductor-ledger` / `conductor-impact` / `conductor-debug` / `conductor-git` / `conductor-subagent` / `conductor-sync` / `conductor-plan` | 器官名（当前 11 器官，router 已并入 conductor-plan） |
| `gate` | `规格确认` / `失败测试先行` / `verify 退出 0` / `source_purity --strict` / `review_gate 退出 0` / `台账零未勾销` / `文档同步核对` / `removal_check 零残留` | conductor 硬门禁（不可裁剪，除条件加载表允许的跳过） |
| `ask` | `置信度<0.5` / `契约不符` / `设计问题未解决` / `低置信重路由` | 停下问用户的点 |

## 三、conductor 特有的控制流

**TDD 循环**（场景 4/5/6/7/8/13 通用）：
```
loop(max_rounds=8, on_fail=ask)
  n_red(tool: 写失败测试) → n_gate1(gate: 确认失败?)
  → n_green(tool: 实现到绿) → n_gate2(gate: verify 全绿?)
  → 未全绿 loop_back；全绿 → 下一节点
```

**review 返修循环**（所有改码场景 S5）：
```
skill:conductor-review → gate(独立 review 报告 + Blocker=0?)
  --Blocker>0--> think(转 finding 给执行者) → loop_back 到 tdd（最多 2 轮，连续 2 轮停下问用户）
  --Blocker=0--> skill:conductor-memory(沉淀) → END
```

**git 条件节点**：每任务 GREEN 后插 `skill:conductor-git(commit)`；用户说“先不提交”→ `skipped` 节点并写省掉声明。

**多场景链**（用户一句话多个动作）：按 planning-method 第 3 步依赖排序，每段展开为 subplan，用 gate 衔接；销毁动作（场景14）排最后。

## 四、conductor 模式的门禁继承

1. **硬门禁不可裁剪**：规格确认、失败测试先行、verify 证据、source_purity --strict、review 门禁、overview L0——必须出成 gate 节点。
2. **条件加载**：按 cost-tiers 第三节判——跳过项写成 `skipped` 节点 + 省掉声明，不删除节点（保留路线完整性，标注为何跳）。
3. **档位映射**：lite/standard/full 影响节点的 `budget` 与 gate 深度，写进图的 `meta`。
4. **ref 校验**：ref 必须是上表里存在的脚本/器官/门禁名，plan_validate 可配置校验。

## 五、执行图与 S1 声明的关系

conductor-plan 出的图是 S1 声明的**详细版**：
- S1 声明 = 图的摘要（场景/路径/档位/省掉）
- 执行图 = 每步动作的完整蓝图
- 图固化进 overview 的执行图节；执行中状态由 conductor 的 S0–S5 状态机维护，不写回图结构
