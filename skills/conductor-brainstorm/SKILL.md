---
name: conductor-brainstorm
description: conductor 的头脑风暴/需求澄清器官。收到模糊需求、设计草案或"拷问一下"时加载；把未决项和假设问清楚，输出可确认的规格，不替 conductor 做推进决策。
---

# conductor-brainstorm · 澄清器官

> conductor 机体的"感官"：把模糊输入变清晰，但闸门仍由 conductor 把。

## 输入
用户需求原句 / 设计草案 / 样例（"参考 X 那样"）/ 已有问题清单。

## 输出
- 澄清后的规格要点（逐条，可勾销）
- 未决清单（每条带"需谁拍板"）
- 明示假设（请用户否决）
- 若只是评估：输出问题清单（严重度 + 行号/依据），不改码

## 执行
1. 先调查再开口：能 `ls`/读文档/看报错就先查，不拿问题当偷懒。
2. 一轮问完整个 frontier（设计树 + 前沿），别挤牙膏式追问。
3. 回述用户意图请确认；两个红旗：跳过调查、把假设藏起来。
4. 有样例信号时转 `references/examples-to-spec.md` 做 6 维外推。

## 方法源
- `references/engineering-workflow.md` 的 brainstorm 节
- 改名并入的本器官方法：`references/grill-design-SKILL.md`（平台原生拷问，优先使用）；`grill-me` 已废弃。

## 降级
`references/grill-design-SKILL.md` 不可读 → 用上面三步内联执行，并在 overview 写「缺拷问方法 / 影响=拷问深度下降 / 降级=内联五问」。**规格未确认前不推进**，这条归 conductor，不归本器官。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的方法文档 + 改名并入的协作 skill 原文
- `scripts/`：器官专属确定性脚本（如有）
