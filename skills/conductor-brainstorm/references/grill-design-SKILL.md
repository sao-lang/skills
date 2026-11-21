# 需求拷问（把方案打穿）

> 本文件原名 `grill-design`（独立 skill），现为 `conductor-brainstorm` 的方法文档，
> **不再是独立 skill**：没有触发词、没有独立 frontmatter，不自行决定何时使用——
> 何时加载、何时收口，由 conductor-brainstorm 与 conductor 决定。加载时机见 `../SKILL.md`。

把用户的一个方案 / 设计 / 想法，当成一棵「设计树」来拷问，直到达成共识。

## 核心机制

- **设计树**：每个决策会分叉出挂在它下面的决策。
- **前沿（frontier）**：所有「前提已经定了、现在就能问」的问题集合。
- **一轮问完整个前沿**：每个问题编号 + 给出推荐答案，等用户回答后再算下一轮。
- **事实归 agent，决策归用户**：能自己查的事实（跑脚本 / 读文档 / 查配置），绝不去问用户；
  派子代理去查，**不阻塞** —— 查的过程中先问前沿里其余的问题。
- **收尾**：前沿清空 = 达成一致；在用户确认前**不要行动**。

## 一轮的格式

```
❓ **Q1** - **<问题标题>**：<问题正文，可含多个选项>
➡️ <推荐答案>

---

❓ **Q2** - **<问题标题>**：<问题正文，可含多个选项>
➡️ <推荐答案>
```

## 怎么问（本平台惯用）

一次抛 2~4 个前沿问题，用 `AskUserQuestion`（每个问题给 2~4 个选项，推荐项放第一个并标「（推荐）」）。
本轮回答会重塑树：已定的决策把前沿往外推、解锁原本卡住的问题 —— 重新算前沿，问下一轮。

## 两个校准

1. **「先实测再讨论」优先**：碰到「事实型」问题（这个脚本到底行不行 / 这个值是不是这样），
   先跑一下 / 读一下再问，别把能查的推给用户。
2. **收尾给结构化结论**：达成一致后，用「分节 + 表格」把定下来的决策列一遍，标出**仍未决的**，
   别只甩一句「好的」。

---

## 移植说明

**来源**：灵感取自 <https://github.com/mattpocock/skills> → `skills/productivity/grilling`（MIT License, © Matt Pocock）。
**并非照搬** —— 这是**蒸馏**后的平台原生技能：只继承了「设计树 + 前沿」这一核心机制，
其余（触发词、提问方式、收尾习惯）按本平台习惯重写。

> **License（MIT）**：原作品以 **MIT License** 发布，© Matt Pocock。按其要求保留版权与许可声明：
> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
> associated documentation files (the "Software"), to deal in the Software without restriction,
> including without limitation the rights to use, copy, modify, merge, publish, distribute,
> sublicense, and/or sell copies of the Software, subject to the inclusion of the above copyright
> notice and this permission notice in all copies or substantial portions of the Software.
原版 `grill-me` 是个空壳指针（只调 `grilling`），本文件是单体完整版，已并入 conductor-brainstorm。
