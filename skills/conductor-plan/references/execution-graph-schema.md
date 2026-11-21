# 执行图 DSL · 节点 / 边 / 控制流 / 动作类型

> 执行图是 conductor-plan 的唯一输出契约：机器可校验（JSON）、人可读（mermaid）、可执行（节点带动作类型与退出判据）。
> 设计目标：把任意任务（开发/生活/业务/决策/排查）解析成一张**明确每一步做什么、什么时候停、出错怎么办**的图。

## 一、顶层结构（JSON）

```json
{
  "version": "1.0",
  "goal": "<一句话目标>",
  "source": "user_request | context | habit",
  "mode": "standalone | conductor",
  "template": "generic.<type> | conductor.<scenario>",
  "confidence": 0.0,
  "assumptions": ["..."],
  "clarifications": ["..."],
  "nodes": [ <Node> ],
  "edges": [ <Edge> ],
  "budget": { "max_steps": 30, "max_retries": 3, "noop_limit": 2 },
  "meta": { "created": "...", "context_refs": [...], "habit_refs": [...] }
}
```

## 二、节点（Node）

```json
{
  "id": "n1",
  "kind": "action | tool | skill | research | think | ask | gate | branch | loop | retry | parallel | subplan",
  "label": "<人可读的一句话>",
  "action": "<具体做什么：调哪个工具/读哪个文件/做哪个判断>",
  "inputs": ["<前置节点产出的契约>"],
  "outputs": ["<本节点产出的契约>"],
  "serves_task": "<仅 research/think 节点必填：本调研/分析服务于哪个原子任务；禁止跨任务借用>",
  "exit_criteria": "<怎么知道这步完成了——必须可判定>",
  "on_fail": "ask | retry | abort | skip",
  "budget": { "max_rounds": 3 },
  "ref": "<conductor 模式：场景号/器官名/脚本名>"
}
```

### 动作类型（kind）——固化的关键

| kind | 含义 | 谁执行 | 示例 |
|---|---|---|---|
| `tool` | 跑确定性工具/命令/script | 执行方（conductor 或 agent） | `python verify.py --lang python` |
| `skill` | 加载器官/专家能力 | 执行方 | `conductor-review` 独立评审 |
| `research` | AI 调研/读文件/查资料 | AI | 读 M6 文档、查 API 文档 |
| `think` | AI 分析/决策/权衡 | AI | 比对两个方案、判根因 |
| `ask` | 问用户，等待输入 | 用户 | “M5 是设计文档还是代码？” |
| `gate` | 门禁校验，不通过不能推进 | 执行方 | review_gate 退出码 0 |
| `action` | 通用动作（生活/业务等非开发） | 执行方/AI | 订机票、发邮件、采购 |
| `branch` | 条件分支（按判定表达式选路） | 执行方 | 测试通过? → 实现 : 修测试 |
| `loop` | 循环（带条件 + 最大轮次） | 执行方 | RED-GREEN 直到全绿 |
| `retry` | 重试（带触发条件 + 上限） | 执行方 | 失败重试 3 次再告警 |
| `parallel` | 并行（子节点无依赖） | 执行方 | 同时调研 A 和 B |
| `subplan` | 子图（嵌套执行图，复杂节点展开） | 执行方 | 子任务 = 另一张图 |

**纪律**：叶子节点（真正干活的）只能是 `tool / skill / research / think / ask / gate / action`；
`branch / loop / retry / parallel / subplan` 是控制节点，必须有子节点或指向边，不允许空转。

## 三、边（Edge）

```json
{ "from": "n1", "to": "n2", "type": "seq | cond | loop_back | retry | parallel", "label": "<条件/说明>", "guard": "<闸门：满足才走这条边>" }
```

- `seq`：顺序；`cond`：条件分支（label 写条件表达式，guard 写闸门）
- `loop_back`：循环回边（必须指向 loop 节点，且带 `budget.max_rounds`）
- `retry`：重试回边（指向 retry 节点，带上限，超限转 `on_fail`）
- `parallel`：并行分叉/汇合（配合 parallel 节点）

## 四、控制流的表达范式

**循环**（TDD 的 RED-GREEN）：
```
n_loop(loop, max_rounds=5) → n_red(tool: 跑测试) → n_green(tool: 实现)
    → n_gate(gate: 全绿?) --否--> n_loop (loop_back)
                            --是--> n_next
```

**分支**（需求澄清分流）：
```
n_check(think: 产出物是代码?) → branch
    --是--> n_code(skill: 改码链)
    --否--> n_read(skill: 只读分析链)
```

**重试**（运维告警）：
```
n_backup(tool: 备份) → n_gate(gate: 成功?)
    --否--> n_retry(retry, max=3) --loop_back--> n_backup
    超限 → n_alert(tool: 告警) → abort
```

**空转防护**：每个循环/重试节点必须有 `exit_criteria` 和 `budget.max_rounds`；
执行方检测“连续 N 步 outputs 无变化 / gate 连续失败 / 节点被反复进入超过上限”→ 停下报 `stalled`，转 `ask` 用户。
图里必须显式标 `budget.noop_limit`（默认 2），否则校验器 FAIL。

## 五、状态（执行中，由执行方维护）

节点状态：`pending | running | done | failed | skipped | blocked`。
执行图本身是静态蓝图；状态在 `execution-state.json`（由执行方写）里跟踪，不污染图结构。

## 六、conductor 模式 vs standalone 模式

| 维度 | standalone | conductor |
|---|---|---|
| 模板 | generic.*（生活/学习/业务/决策/排查…） | conductor.<场景号>（14 场景） |
| 动作类型 | 全类型（action 为主） | tool/skill/gate 为主，ref 指向器官/脚本 |
| 门禁 | 用户自定义 exit_criteria | 复用 conductor 硬门禁（规格确认/verify/review_gate） |
| 执行方 | agent 或用户自己 | conductor 状态机 |
| 输出去向 | overview 旁 / 用户指定 | overview 的执行图节，S1 声明引用 |

## 七、校验规则（plan_validate.py 实现）

1. 顶层必填：version/goal/mode/nodes/edges/budget
2. 每个节点必填：id/kind/label/action/exit_criteria；叶子节点 kind 合法
3. 边的 from/to 必须指向存在的节点；loop_back/retry 必须指向对应控制节点且有 budget
4. 每个 loop/retry 必须有 max_rounds 和 on_fail；branch 必须有 ≥2 条出边
5. 每个节点有 exit_criteria；budget.noop_limit 存在
6. 无孤儿节点（除入口外，每个节点有入边；除终点外，有出边）
7. mermaid 可生成（节点 label 转义、边 label 合法）
8. research/think 节点必须有 `serves_task`（调研归属，防跨任务借用）
9. 顶层含 `tasks[]` 时（多原子任务），每个 research/think 的 serves_task 必须指向存在的任务 id
