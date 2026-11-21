---
name: conductor-learn
description: conductor 的学习回写器官。S5 门禁通过后加载，从 overview 抽取可复用决策、纠正与踩坑，写入项目约定或器官经验文件；默认 dry-run，不替 conductor 放行。
---

# conductor-learn · 学习回写器官

> conductor 机体的"长期记忆"：让第 10 次任务比第 1 次更聪明。只产出回写草稿与证据，不放行。

## 输入

- overview 主文件与 `.details.md`（按需）：关键决策、用户纠正、review Blocker 根因、环境阻断、未完成项
- 可选：项目约定文件路径、器官 `lessons.md` 路径

## 输出

- learn 草稿：`触发条件 → 处理动作` 条目列表
- 回写目标：项目级 `docs/conventions.md` 或 `.workbuddy/memory/MEMORY.md`；技能级 `<organ>/references/lessons.md`
- `learn_capture.py --dry-run` 的候选条目输出（默认不落盘）

## 执行

1. 从 overview 抽取有后续影响的条目；流水账、未采纳方案、闲聊不写。
2. 每条必须补成"触发条件 + 处理动作"，不能只写"注意 X"。
3. 去重：同义条目合并，不增殖；与已有约定冲突时标为待裁决，不静默覆盖。
4. 默认 `learn_capture.py --dry-run` 出草稿；人工确认后再 `--apply` 写入，禁止自动污染 skill。
5. 无可复用经验 → 写"本次无新增经验"并留痕，禁止静默跳过。
6. 本器官在 `review_gate.py` 退出 0、台账零未勾销之后运行；不参与放行决策。

## 方法源

- `./references/learning-method.md`：抽取、去重、回写与门禁边界
- `./references/lessons-template.md`：`lessons.md` 与项目约定的条目格式

## 降级

- 回写目标不可写 → 在 overview 登记「learn 阻塞 + 目标路径」，不影响本次收尾，但下次 S0 必须提醒补写。
- overview 不存在 → 停下报告，不猜内容。
- lite 档 → 跳过 learn，但必须在路由声明的"省掉"里列出。

## 本器官自带（可独立工作）

- `SKILL.md`：角色、I/O、执行与降级
- `references/`：回写方法与条目模板
- `scripts/learn_capture.py`：从 overview 抽候选条目，默认 dry-run
