---
name: conductor-overview
description: conductor 的会话记录器官。S0 建/续 overview、收尾写结论时加载；默认只有 L0 主文件进上下文，详情走 .details.md，控制 token 占用。
---

# conductor-overview · 记忆压缩器官

> conductor 机体的"短期记忆"：只让当前需要的一层进上下文。

## 输入
主题、场景/路径/档位、当前闸门、产物路径、未完成项（≤3）、下一步。

## 输出
- 主文件 `overviews/YYYY-MM-DD/<sid>-<主题>.md`：**仅 L0 索引卡（≤8 行）+ 需要的 review 章节**
- 详情文件 `overviews/YYYY-MM-DD/<sid>-<主题>.details.md`：环境、L1 摘要、关键决策、验证细节、变更清单
- 最小会话指针 `.conductor-session.json`：`{"sid":"xxxxxxxx"}`（兼容旧 session_id 字段）

## 执行
1. 跑 `scripts/overview_path.py` 定位；同会话 append，换任务 `--new-session`。
2. 续接**只读主文件 L0**；需要历史决策才打开 `.details.md`；禁止整份灌入。
3. 只记有后续影响的内容：诉求/决策/问题带状态/产物/证据/未完成项；闲聊与未采纳方案不写。
4. 改码交付时 review 报告内嵌主文件（门禁要求），其余大块详情一律进 `.details.md`。

## 方法源
`references/overview.md`（两-tier 模板、过滤规则、加载协议）、`handoff-SKILL.md`（L1 交接纪律，原 handoff 已并入）。

## 降级
主文件不存在 → `overview_path.py` create；详情缺失 → 跳过不影响续接；写 overview 前必须脱敏。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的方法文档 + 改名并入的协作 skill 原文
- `scripts/`：器官专属确定性脚本（如有）
