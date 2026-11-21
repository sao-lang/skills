# 活规格方法

## 1. 抽取（不重拷问）

从 brainstorm 输出映射：

| brainstorm 输出 | 契约段落 |
|---|---|
| 规格要点（已确认） | Delta + Acceptance |
| **规格要点替代/废弃的旧东西** | **Delta（删除/替换条目）+ Acceptance（残留为 0）** |
| 明示假设 | Open（带 owner） |
| 未决清单 | Open |
| 用户否决的方案 | Open（标注 rejected） |
| 既有接口/数据格式约束 | Invariants |

映射不到的内容留在 Open，禁止脑补进 Acceptance。

## 1·补、删除推导（每个 Delta 必做，防"该删没删"）

AI 天然擅长加东西，不擅长从需求变化推导出"什么该消失"。**每个 Delta 条目都必须过一遍删除推导**，不许只写新增：

1. **逐条问四问**：这个变化**替代**了什么？**废弃**了什么？让哪些字段/参数/分支/函数/模块/功能/文档**不再成立**？有没有旧调用方/旧配置/旧测试随之失效？
2. **写入 Delta**：用动词 `删除` / `替换` / `移除` / `下线` 开头，**必须带可核对的符号名**（反引号包裹的函数/类/字段/文件路径），如"删除 `legacy_mode` 参数与 `if legacy_mode` 分支"。纯中文描述无符号名的条目机器无法核对，视为未登记。
3. **写入 Acceptance**：每条待删项跟一条验收——"`X` 定义与引用均为 0（`removal_check.py --contract <path>` 退出码 0）"。
4. **核不出也要留痕**：确认"无旧物可删"的条目写"无遗留（核对依据：xxx）"，不许空白跳过。
5. 删除推导的结果就是 S5 的机器核对清单——`conductor-review` 的 `removal_check.py` 从 Delta 自动提取待删符号，残留即 FAIL。**这一步漏登记，后面就没人拦。**

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
