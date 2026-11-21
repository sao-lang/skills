---
name: conductor-brainstorm
description: conductor 的澄清与规格器官。收到模糊需求、设计草案或"拷问一下"时加载；把未决项和假设问清楚，并可将澄清结果固化为六段式 change-contract（可机器校验），不替 conductor 做推进决策与放行。
---

# conductor-brainstorm · 澄清与规格器官

> **器官类型**：澄清与规格（感官 + 契约） —— 输入模糊需求/样例 → 输出规格要点 + 六段 change-contract
> conductor 机体的"感官 + 契约层"：把模糊输入变清晰，再把一次性澄清固化成可跨会话维护、可机器校验的变更契约。只给结论和证据，闸门仍由 conductor 把。

## 输入
- 用户需求原句 / 设计草案 / 样例（"参考 X 那样"）/ 已有问题清单
- 规格（spec）阶段追加：可选旧 `change-contract.md`、当前 diff、相关模块清单

## 输出
- 澄清后的规格要点（逐条，可勾销）、未决清单（每条带"需谁拍板"）、明示假设（请用户否决）
- 若只是评估：输出问题清单（严重度 + 行号/依据），不改码
- 规格（spec）阶段追加：持久化 `change-contract.md`（六段固定：Why / Delta / Invariants / Affected / Acceptance / Open）+ `contract_check.py` 退出码 0 的机器证据 + Acceptance 清单（可灌入台账）

## 执行
1. 先调查再开口：能 `ls`/读文档/看报错就先查，不拿问题当偷懒。
2. 一轮问完整个 frontier（设计树 + 前沿），别挤牙膏式追问。
3. 回述用户意图请确认；两个红旗：跳过调查、把假设藏起来。
4. 有样例信号时转 `references/examples-to-spec.md` 做 6 维外推。
5. 规格固化（standard/full 档，S2 后段）：从本器官澄清输出抽取，**不重新拷问用户**；规格未确认的条目只能进 Open，不能偷偷写进 Acceptance。
6. 已有旧契约 → `merge`：保留已验证条目，只改 Delta / Affected / Acceptance，并在 Open 记录被否决的方案。
7. 契约未生成、`contract_check.py` 非 0 → **不进 S3**。这是 conductor 的硬门禁，本器官只提供证据。

## 方法源
- `references/brainstorm-plan.md`（brainstorm 与 plan 两能力的方法全文）
- `references/design-spec-template.md`（规格输出模板）
- `references/grill-design-SKILL.md`（平台原生拷问，优先使用）；`grill-me` 已废弃
- `references/change-contract-template.md`（六段契约模板与填写口径）
- `references/spec-method.md`（抽取、merge、验收注入与门禁方法）

## 降级
- 拷问方法不可读 → 用执行 1–3 内联，并在 overview 写「缺拷问方法 / 影响=拷问深度下降 / 降级=内联五问」。
- `contract_check.py` 不可用 → 手写契约，但 overview 必须写「缺失契约检查脚本 / 影响=Acceptance 未机器校验 / 降级=人工核对」。
- 首次项目无基线 → 生成 baseline 契约，Why 段写明"首个基线，待后续 delta 累积"。
- 规格未确认 → 不生成正式契约，只写草稿并退回 conductor 等待确认。**规格未确认前不推进**，这条归 conductor，不归本器官。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：澄清/拷问/规格方法 + 六段契约模板
- `scripts/contract_check.py`：六段齐全 + Acceptance 非空检查，可 `--acceptance-only` 输出
