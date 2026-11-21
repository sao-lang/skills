---
name: conductor-impact
description: conductor 的影响面器官。改码/迭代/重构需要知道"改这里波及谁"时加载；输出调用方与建议测试草稿，明确标注草稿需核实。
---

# conductor-impact · 影响面器官

> conductor 机体的"外周神经"：给出可能受影响的边界，不充当权威结论。

## 输入
符号名 / 改动文件列表 / diff（stdin）；跨文件关系复杂时可用外部调用图工具（原 `graphify` 已筛选废弃，本器官不依赖）。

## 输出
- 直接引用者、间接调用链、建议跑的测试清单
- 每条附源码位置；明确标注「草稿，需打开源码核对」

## 执行
1. 单文件/单符号且无跨模块信号 → **跳过**（lite 与 standard 默认不跑）。
2. standard 有跨模块信号或 full 必跑：`impact_analysis.py --symbols/--files/--diff`。
3. 跨文件关系复杂时按 `references/architecture-contracts.md` 的接线四问逐条核对，关键边打开源码；不建外部图（冷启动成本高于收益）。
4. 输出按 conductor 编排灌入承诺台账：`... | commitment_ledger.py init --stdin`（台账脚本清单见 conductor 的 skill-matrix）。

## 方法源
`scripts/impact_analysis.py`、`references/architecture-contracts.md`（接线四问）。

## 降级
脚本缺失 → 人工列直接引用者并写"未做全量影响面"，禁止声称已核完。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的架构契约文档（architecture-contracts / contract-migration）
- `scripts/impact_analysis.py`：影响面草稿
