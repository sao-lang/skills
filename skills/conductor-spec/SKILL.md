---
name: conductor-spec
description: conductor 的活规格/变更契约器官。收到 brainstorm 输出的规格要点、未决与假设，或需要把一次改动固化成可持续维护的契约时加载；输出六段式 change-contract， Acceptance 进入承诺台账，不替 conductor 放行。
---

# conductor-spec · 活规格器官

> conductor 机体的"契约层"：把 brainstorm 的一次性澄清，固化成可跨会话维护、可机器校验的变更契约。只给结论和证据，不放行。

## 输入

- `conductor-brainstorm` 的输出：规格要点、未决清单、明示假设
- 可选：旧 `change-contract.md`、当前 diff、相关模块清单

## 输出

- 持久化 `change-contract.md`，六段固定：Why / Delta / Invariants / Affected / Acceptance / Open
- `contract_check.py` 退出码 0 的机器证据（六段齐全、Acceptance 非空）
- Acceptance 清单（可由脚本输出后灌入 `conductor-ledger`）

## 执行

1. 从 brainstorm 输出抽取，**不重新拷问用户**；规格未确认的条目只能进 Open，不能偷偷写进 Acceptance。
2. 已有旧契约 → `merge`：保留已验证条目，只改 Delta / Affected / Acceptance，并在 Open 记录被否决的方案。
3. `Affected` 段作为 `conductor-impact` 的输入，避免影响面分析凭空猜符号。
4. `Acceptance` 逐条进入台账：`contract_check.py --acceptance-only --contract <path> | commitment_ledger.py init --stdin`。
5. 契约未生成、`contract_check.py` 非 0 → **不进 S3**。这是 conductor 的硬门禁，本器官只提供证据。

## 方法源

- `./references/change-contract-template.md`：六段模板与填写口径
- `./references/spec-method.md`：抽取、merge、验收注入与门禁方法

## 降级

- 首次项目无基线 → 生成 baseline 契约，Why 段写明"首个基线，待后续 delta 累积"。
- `contract_check.py` 不可用 → 手写契约，但 overview 必须写「缺失契约检查脚本 / 影响=Acceptance 未机器校验 / 降级=人工核对」。
- brainstorm 输出未确认 → 不生成正式契约，只写草稿并退回 conductor 等待确认。

## 本器官自带（可独立工作）

- `SKILL.md`：角色、I/O、执行与降级
- `references/`：六段模板与方法原文
- `scripts/contract_check.py`：六段齐全 + Acceptance 非空检查，可输出 acceptance-only
