---
name: conductor-review
description: conductor 的独立 review 器官。改码交付前加载：standard/full 派全新上下文子代理跑七维审查，lite 做三问轻量复核；用 review_gate 出机器证据，不替代 conductor 的放行决策。
---

# conductor-review · 换眼器官

> conductor 机体的"免疫检查"：执行者自查不算，必须换眼并留证据。

## 输入
改动清单或 diff、意图源（规格/任务 brief）路径、档位、overview 路径。

## 执行
- **standard/full**：派**全新上下文子代理**按本器官 `references/code-quality-review-SKILL.md` 执行七维审查（+ 接线四问，重点查功能遗漏/断点），Blocker=0 才放行；有 Blocker → fix loop 后**再派新子代理**复审，禁止复用旧报告。
- **lite**：不派子代理；在主 overview 写「轻量复核（lite）」章节：意图一致 / 边界与错误 / 证据（verify + source_purity 退出码），跑 `review_gate.py --lite`。

## 输出
- overview 内 `## 独立 review 报告`（多轮用 `### Round N`，内嵌不拆文件）或 lite 的轻量复核章节
- `review_gate.py` 退出码 0 的机器证据

## 方法源
`references/independent-review.md`、`engineering-code-review.md`（派单契约/fix-loop）。

## 降级
`references/code-quality-review-SKILL.md` 不可读 → 显式写「缺失/影响/降级」，用 `references/engineering-code-review.md` 内联七维清单；**拿不到 review_gate 证据禁止 finish**。lite 复核发现 Blocker>0 → 立即升 standard 重审。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的方法文档 + 改名并入的协作 skill 原文
- `scripts/`：器官专属确定性脚本（如有）
