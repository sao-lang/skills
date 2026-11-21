---
name: conductor-ledger
description: conductor 的防漏台账器官。收到规格/差异/finding/模块清单需要逐条勾销时加载；外置承诺、定位断点、卡零未勾销，靠台账不靠记忆。
---

# conductor-ledger · 记忆外置器官

> conductor 机体的"长期记忆"：把隐含承诺变成机器可校验事实。

## 输入
来源任选可叠加：`--from-modules` 源码扫描 / `--from-list` 文档列表 / `--from-json` / `--stdin`（接 impact 与 review 输出）/ `--manual`。

## 输出
- 最小状态文件 `.commitment-ledger.json`（紧凑 JSON，空字段不写；场景7 shim 用 `.migration-ledger.json`）
- `next` 断点、`check --strict` 门禁结论、`show` 人工全览

## 执行
1. S0 采集：机器能扫的自动扫，人只补语义；增量合并保留已填状态。
2. S4 核证据：verified 必挂有效 evidence（路径真实存在或命令+退出码）；skipped 必填 reason。
3. S5 放行：`check --strict` 退出 0 才准 finish。
4. 状态机 `pending → in_progress → verified / skipped(reason)`；drift（新模块未登记）一律 FAIL。
5. 无隐含清单的场景不建台账；lite 档默认跳过。

## 方法源
`references/commitment-ledger.md`（通用框架）、`migration-integrity.md`（场景7 特化）、`tech-debt-ledger.md`（技术债台账；`debt_ledger.py` 是机体级脚本，调用方式见 skill-matrix）；本器官脚本 `../scripts/commitment_ledger.py` / `../scripts/migration_ledger.py`。

## 降级
台账文件损坏 → `init` 重建并保留能解析的项；drift → 重跑 `init --merge`；绝不允许刷状态过闸门。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的台账方法文档（commitment-ledger / migration-integrity / tech-debt-ledger）
- `scripts/`：commitment_ledger.py / migration_ledger.py
