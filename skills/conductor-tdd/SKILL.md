---
name: conductor-tdd
description: conductor 的 TDD 器官。收到"实现某行为/修 bug 后补回归"时加载；只负责 RED-GREEN-REFACTOR 与测试证据，不决定要不要开工。
---

# conductor-tdd · 测试驱动器官

> **器官类型**：执行（肌肉） —— 输入一条已确认行为 → 输出红/绿测试 + verify 证据
> conductor 机体的"肌肉"：把一条已确认的行为变成可验证代码。

## 输入
一条已确认规格/一个已定位 bug + 当前语言规则文件。

## 输出
- 失败测试（文件:行号 + 运行命令 + 失败输出）
- 实现代码
- 绿证据（测试命令 + 退出码）
- 若绿后重构，附重构前后测试仍绿证据

## 执行
1. RED：先写最小失败测试，跑出红；Verify RED——确认失败原因就是缺该行为，不是环境/拼写。
2. GREEN：写最小实现让测试过；Verify GREEN——跑全量相关测试，不只单条。
3. REFACTOR：保持绿的前提下改善结构；不改行为。
4. 测试证据只认 `scripts/verify.py` 输出；裸跑 pytest/vitest 不算 S4 证据。
5. 五个"不写测试"借口逐条拒绝（见方法源）。

## 方法源
`references/engineering-tdd.md`（循环、Verify、5 借口、红旗）、`test-strategy.md`（测试策略）、`coding-rules-common.md` + `coding-rules-<lang>.md`（实现写成什么样，7 种语言）。

## 降级
环境缺失导致无法跑红/绿 → 登记「环境阻断」（报错 + 所需环境），禁止改断言、换 fake 或标完成；交回 conductor 决定是否升档/停下问用户。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的 TDD 方法、测试策略与通用 + 7 语言编码规则
- `scripts/verify.py`：验证命令聚合与退出码证据
