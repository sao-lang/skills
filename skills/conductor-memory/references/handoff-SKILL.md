# Overview L1 交接（原 handoff，已并入 conductor-memory）

> 本文件原名 `handoff`（来自 mattpocock/skills，MIT），现为 `conductor-memory` 的方法文档，
> **不再是独立 skill**：没有触发词、没有独立 frontmatter、不写独立 handoff 文件。
> 由 conductor 在 S0（续接定位）与 S5（收尾交接）时加载，配合 `overview.md` 的两-tier 模型使用。

## 旧的"handoff 文档"对应关系（读到旧资料时按此换算）

| 原 handoff 概念 | 现在落在哪 |
|---|---|
| `docs/handoff-<timestamp>.md` 整份交接文档 | **不再存在**。主文件 `overviews/YYYY-MM-DD/<sid>-<主题>.md` 只放 L0 索引卡 |
| Current state（本次完成了什么） | 详情文件 `.details.md` 的「L1 摘要」+「验证证据」 |
| Next steps（下一步优先级） | 主文件 L0 的「未完成 / 下一步」+ 详情「未完成项与下一步（完整）」 |
| Relevant artifacts（相关产物） | 主文件 L0 的「产物」；详情只存路径，不内联内容 |
| Suggested skills（下个会话加载什么） | 主文件 L0 的「下一步」写动作；器官由 conductor 按场景路由决定，不再手写 skill 清单 |

## 保留的有效经验（写作纪律）

1. **写前先扫已有产物**：PRD / ADR / 开放 issue / 近期 diff，能引用路径就不要复制内容。
   原 handoff 的这条纪律现在作用于 overview：详情里引用 `docs/...` 路径，不内联正文。
2. **不重复已捕获的内容**：已写进 change-contract、commitment-ledger、review 报告的内容只写路径。
3. **用户给了关注点参数时**，用它加权「下一步」小节：用户点名的排前面。
4. **具体优于概括**：L1 摘要写"改了哪些文件、做了什么决策"，不写"进展顺利"。

## 已废弃的部分（原文件含、现已删除）

- 独立 handoff 文件路径与 timestamp 命名 → 由 `overview_path.py` 管理 `overviews/` 结构
- `Suggested skills` 推荐清单（`diagnose / to-issues / grill-me / grill-with-docs / zoom-out / handoff`）
  → 这些 skill 已删除或并入器官；下一步动作写进 L0，器官选择归 conductor 路由
- Tools（Read/Write/Bash）说明 → 器官宿主自带，不再声明

## 来源致谢

原作品来自 <https://github.com/mattpocock/skills>（MIT License）。按许可要求保留声明：
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction.
本文件是对其核心思想（跨会话交接、引用而非复制、按优先级排下一步）的本地化重述与重构。
