---
name: conductor-review
description: conductor 的独立 review 器官。改码交付前加载：standard/full 派全新上下文子代理跑七维审查，lite 做三问轻量复核；用 review_gate 出机器证据，并自带缺口/纯净/意图三扫描（S4 门禁证据），不替代 conductor 的放行决策。
---

# conductor-review · 换眼器官

> **器官类型**：审查（免疫系统） —— 输入 diff + 档位 → 输出报告 + review_gate 退出码；自查不算，必须换眼
> conductor 机体的"免疫检查"：执行者自查不算，必须换眼并留证据。
> 代码审查的机器证据也归本器官：`scan_gaps.py`（缺口）、`source_purity.py`（假实现/动态类型）、`intent_gaps.py`（意图空白）。

## 输入
改动清单或 diff、意图源（规格/任务 brief）路径、档位、overview 路径。

## 执行
- **standard/full**：派**全新上下文子代理**按本器官 `references/code-quality-review-SKILL.md` 执行七维审查（+ 接线四问，重点查功能遗漏/断点），Blocker=0 才放行；有 Blocker → fix loop 后**再派新子代理**复审，禁止复用旧报告。
- **lite**：不派子代理；在主 overview 写「轻量复核（lite）」章节：意图一致 / 边界与错误 / 证据（verify + source_purity 退出码），跑 `review_gate.py --lite`。

## 输出
- overview 内 `## 独立 review 报告`（多轮用 `### Round N`，内嵌不拆文件）或 lite 的轻量复核章节
- `review_gate.py` 退出码 0 的机器证据

## 方法源
`references/independent-review.md`（派单契约/fix-loop）、`engineering-code-review.md`（review 规矩）、`code-quality-review-SKILL.md`（七维方法）、`code-quality-review-output-contract.md`（输出契约）、`security-redlines.md`（安全红线）、`source-purity.md`（源码纯净门禁规则与豁免）。

## 机器扫描（S4 门禁证据，本器官提供）

| 脚本 | 扫什么 |
|---|---|
| `../scripts/scan_gaps.py` | TODO/pass/fake/协议无实现/install 无调用 → 缺口台账草稿 |
| `../scripts/source_purity.py` | fake 实现/不具体类型（数据驱动规则库+存量基线），默认合并 intent_gaps |
| `../scripts/intent_gaps.py` | 无注释跨模块占位、声明未用且无说明的参数（函数级 AST） |

## 降级
`references/code-quality-review-SKILL.md` 不可读 → 显式写「缺失/影响/降级」，用 `references/engineering-code-review.md` 内联七维清单；**拿不到 review_gate 证据禁止收尾**。lite 复核发现 Blocker>0 → 立即升 standard 重审。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的方法文档 + 改名并入的协作 skill 原文 + source-purity 门禁规则
- `scripts/`：review_gate.py / scan_gaps.py / source_purity.py / intent_gaps.py
