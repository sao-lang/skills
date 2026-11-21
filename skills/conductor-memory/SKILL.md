---
name: conductor-memory
description: conductor 的记忆器官（会话记录 + 学习沉淀）。S0 建/续 overview、收尾写结论、S5 门禁通过后抽经验回写时加载；L0 主文件控 token，回写默认 dry-run，不替 conductor 放行。
---

# conductor-memory · 记忆器官

> **器官类型**：记忆（短期 + 长期） —— 输入主题/状态 → 输出 overview（L0 两-tier）+ 经验沉淀条目
> conductor 机体的"短期记忆 + 长期记忆"：短期只让当前需要的一层进上下文（两-tier 压缩）；长期让第 10 次任务比第 1 次更聪明（经验回写）。只产出记录、草稿与证据，不放行。

## 输入
- 记录（overview）：主题、场景/路径/档位、当前闸门、产物路径、未完成项（≤3）、下一步
- 沉淀（learn）：overview 主文件与 `.details.md`（按需）、可选项目约定文件路径与器官 `lessons.md` 路径

## 输出
- 主文件 `overviews/YYYY-MM-DD/<sid>-<主题>.md`：**仅 L0 索引卡（≤8 行）+ 需要的 review 章节**
- 详情文件 `overviews/YYYY-MM-DD/<sid>-<主题>.details.md`：环境、L1 摘要、关键决策、验证细节、变更清单
- 最小会话指针 `.conductor-session.json`：`{"sid":"xxxxxxxx"}`（兼容旧 session_id 字段）
- learn 草稿：`触发条件 → 处理动作` 条目列表 + 回写目标（项目约定或 `<organ>/references/lessons.md`）；默认 dry-run 不落盘

## 执行
1. 跑 `scripts/overview_path.py` 定位；同会话 append，换任务 `--new-session`。
2. 续接**只读主文件 L0**；需要历史决策才打开 `.details.md`；禁止整份灌入。
3. 只记有后续影响的内容：诉求/决策/问题带状态/产物/证据/未完成项；闲聊与未采纳方案不写。
4. 改码交付时 review 报告内嵌主文件（门禁要求），其余大块详情一律进 `.details.md`。
5. 沉淀（S5、review 门禁退出 0 且台账零未勾销之后）：从 overview 抽有后续影响的条目；每条补成"触发条件 + 处理动作"；同义合并去重，与已有约定冲突标待裁决不静默覆盖。
6. 默认 `learn_capture.py --dry-run` 出草稿；人工确认后再 `--apply` 写入，禁止自动污染 skill；无可复用经验写"本次无新增经验"并留痕。

## 方法源
- `references/overview.md`（两-tier 模板、过滤规则、加载协议）
- `references/handoff-SKILL.md`（L1 交接纪律，原 handoff 已并入）
- `references/learning-method.md`（抽取、去重、回写与门禁边界）
- `references/lessons-template.md`（`lessons.md` 与项目约定的条目格式）

## 降级
- 主文件不存在 → `overview_path.py` create；详情缺失 → 跳过不影响续接；写 overview 前必须脱敏。
- 回写目标不可写 → 在 overview 登记「learn 阻塞 + 目标路径」，不影响本次收尾，下次 S0 必须提醒补写。
- overview 不存在而要做沉淀 → 停下报告，不猜内容。
- lite 档 → 记录只保 L0 主文件、跳过沉淀，但必须在路由声明的"省掉"里列出。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：记录/交接/沉淀方法与条目模板
- `scripts/overview_path.py`：会话指针定位（同会话归同一文件）
- `scripts/learn_capture.py`：从 overview 抽候选条目，默认 dry-run
