---
name: conductor-plan
description: 通用的路径规划器官（流程图引擎），已吸收原 conductor-router 的场景判定与头脑风暴的 plan 步骤展开能力。收到任务需要解析成清晰执行路径时加载——开发/生活/业务/决策/学习/排查等场景通用；分析意图与上下文，不清楚就澄清等待输入，输出带循环/分支/重试/空转防护的 JSON 执行图 + mermaid。被 conductor 调用时用其 01-routing/execution-graph-adapter.md 接入 14 场景，单独使用时按通用模板规划。只出图不执行。
---

# conductor-plan · 路径规划器官

> **器官类型**：规划（蓝图设计） —— 输入用户原句 + 上下文 → 输出完整执行图（JSON + mermaid）；只规划不执行
> 通用流程图引擎：把任意任务解析成“每步做什么、谁做、怎么算完成、出错怎么办”的图。
> 单独用 = 通用规划器；被 conductor 调用 = 接入 14 场景模板的开发规划器。

## 输入
- 用户原句（可能夹杂闲聊/杂务/回指）
- 上下文：对话历史、overview、指定文件、目录事实、历史执行图
- 模式：`standalone`（默认，通用）或 `conductor`（被 conductor 调用）

## 输出（严格结构）
- **execution-plan.json**：完整执行图（schema 见 `references/execution-graph-schema.md`）
- **mermaid 图**：给用户看的可视化（`plan_validate.py --mermaid`）
- **声明**：目标 / 模式 / 节点数 / 关键分支 / 置信度 / 假设 / 省掉 / “错了请说”

## 执行（六步管线）
1. **事务分类**：分清任务相关 / 环境杂务 / 闲聊 / 外部操作 / 历史回指，只把任务画进图。
2. **意图分析**：四问（产出物 / 对象 / 约束与习惯 / 信息够不够）→ 匹配模板。
2.5 **扫反例库**：规划前扫 `references/cases.md`（真实失败案例），避免重犯同类错误。
3. **澄清循环**：信息不足 → 一次问清 frontier（≤5 项，给候选）→ **等待用户输入**；<0.5 置信度禁止出图。
4. **拓扑推导**：按依赖排序（生产者先、销毁后、闸门内联、失败路径显式、改码必带验证）。
5. **步骤展开**：始终完整展开到动作级（kind: tool/skill/research/think/ask/gate/action + 控制节点），每步带 `action` + `exit_criteria` + 空转预算。
6. **出图固化**：生成 JSON → mermaid → 声明 → 跑 `plan_validate.py` 校验（不过则修图重出）。

详见 `references/planning-method.md`；模板见 `references/templates/`（generic / conductor）；习惯适配见 `references/habits.md`。

## 机器校验
```bash
python scripts/plan_validate.py --plan execution-plan.json --mermaid
```
校验结构合法（节点/边/控制流/退出判据/空转预算）+ 生成 mermaid；退出码 0 = 可交付。

## 降级
- 信息不足且用户未回应 → 停在 `ask`，**不出图**，禁止猜着画。
- 模板匹配不上 → generic 从零推导；图 >30 节点 → 拆 subplan 分层。
- 校验器不可用 → 人工按 schema 第七节核对，声明“未机器校验”。

## 与 conductor 的关系
- 被 conductor 调用时：加载 conductor 机体的 `references/01-routing/execution-graph-adapter.md`（场景适配层归 conductor 持有），ref 指向器官/脚本/门禁；图固化进 overview 执行图节，S1 声明引用。
- 单独使用时：加载 `templates/generic.md`，全动作类型可用，图存 overview 旁或用户指定。
- **只规划不执行**：循环/重试/空转字段写进图；执行与状态跟踪由调用方（conductor 状态机或用户/agent）负责。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、六步管线、降级
- `references/execution-graph-schema.md`：图 DSL 契约（节点/边/控制流/校验规则）
- `references/planning-method.md`：通用规划方法
- `references/cases.md`：规划反例库（规划前必扫）
- `references/test-plan.md`：端到端效果测试方案 + 测试结果（黑盒子代理验证规划质量；改规划方法后应重跑）
- `references/templates/generic.md`：通用模板库（conductor 场景适配层在 conductor 机体的 01-routing/execution-graph-adapter.md）
- `references/habits.md`：用户习惯适配
- `scripts/plan_validate.py`：结构校验 + mermaid 生成
