# 活规格方法

## 1. 抽取（不重拷问）

从 brainstorm 输出映射：

| brainstorm 输出 | 契约段落 |
|---|---|
| 规格要点（已确认） | Delta + Acceptance |
| 明示假设 | Open（带 owner） |
| 未决清单 | Open |
| 用户否决的方案 | Open（标注 rejected） |
| 既有接口/数据格式约束 | Invariants |

映射不到的内容留在 Open，禁止脑补进 Acceptance。

## 2. merge（跨会话）

- 已 verified 的 Acceptance 保留原文与证据引用，不改。
- 新 delta 追加，不覆盖历史。
- 若新改动推翻旧 Invariant，必须在 Delta 明写"解除约束 X"，并在 Open 记录谁拍板。
- 每次 merge 更新头部状态：draft → confirmed → verified。

## 3. 验收注入

```bash
python ../scripts/contract_check.py --contract change-contract.md
# --acceptance-only 输出的验收条目，按 conductor 编排交给承诺台账脚本 init --stdin 注入
# （台账脚本清单见 conductor 的 skill-matrix）
python ../scripts/contract_check.py --contract change-contract.md --acceptance-only
```

Acceptance 为空 → 契约无效，退回 S2。

## 4. 门禁边界

- 本器官只输出契约与脚本证据。
- 是否进 S3、是否放行，由 conductor 决定。
- 契约存在不等于完成；Acceptance 全部 verified 且 ledger 零未勾销才算收口。
