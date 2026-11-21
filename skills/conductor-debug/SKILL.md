---
name: conductor-debug
description: conductor 的调试器官。收到报错栈、行为不符、故障现象时加载；定位根因、构造最小复现、区分代码 bug 与环境阻断。
---

# conductor-debug · 根因器官

> conductor 机体的"诊断系统"：先找原因，再谈修复；不许拿环境缺失掩盖代码 bug。

## 输入
报错栈 / 行为不符描述 / 复现步骤 / 环境信息。

## 输出
- 根因结论（含证据位置）
- 最小复现（命令或测试）
- 修复范围建议 + 回归测试要求
- 若为环境问题：`环境阻断` 登记（报错 + 所需环境），交 conductor 决策

## 执行
1. 四阶段：定位现象 → 收集证据 → 形成假设 → 验证/推翻假设。
2. 先构造最小复现；没有复现不宣称根因。
3. 测试报错先分根因：代码 bug 自己修；连不上/容器起不来/缺驱动属环境依赖，明确告知用户 AI 解决不了。
4. 禁止改断言、换 fake、mock 掉失败来造假绿；生产实现照真实基础设施写。

## 方法源
`./references/engineering-debugging.md`、`../conductor-tdd/references/test-strategy.md` §5.5、`../conductor-impact/references/architecture-contracts.md` §4.5。

## 降级
复现不了 → 停下问用户要步骤/日志，交回 conductor 重路由（可能不是场景8）；环境阻断登记后可暂忽略该项，但禁止标完成。

## 本器官自带（可独立工作）
- `SKILL.md`：角色、I/O、执行与降级
- `references/`：从 conductor 拆分的方法文档 + 改名并入的协作 skill 原文
- `scripts/`：器官专属确定性脚本（如有）
