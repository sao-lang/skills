---
name: conductor-sync
description: conductor 的统一安装与完整性器官。用户说"同步/安装/更新 conductor skills""装到智能体里"或改完 skill 需要落全局时加载：把项目 skills/ 的 conductor 家族复制到智能体全局目录，并跑契约/效果/单一真相源三测试验证接线完好。
---

# conductor-sync · 统一安装与完整性器官

> **器官类型**：安装同步（装机与质检车间） —— 输入项目 skills/ → 输出同步清单 + 完整性三测试计数
> conductor 机体的"装机与质检车间"：项目 `skills/` 是唯一真相源，全局安装是复制副本；
> 本器官负责**统一安装/更新全家 skill** 并验证副本与接线没被改坏。

## 输入

- 项目 `skills/` 目录（唯一真相源，conductor + conductor-* 同级家族）
- 目标全局目录 `~/.workbuddy/skills/`

## 输出

- 同步清单：每个 skill 复制了哪些文件、全局有哪些"源已删"的多余文件（需人工确认后删除）
- 完整性证据：organ_contract / organ_effect / script_parity 三测试的通过计数（如 39/39、15/15、18/18）

## 执行

1. **同步**：`python ../scripts/sync-global.py`（默认同步 conductor 家族；`--all` 含非 conductor 家族 skill；`--dry-run` 只列差异）。
2. **验证**：依次跑三测试，全绿才算"已同步且健康"——
   - `python ../scripts/organ_contract_test.py`（接线/契约/自包含）
   - `python ../scripts/organ_effect_test.py`（真实输入→输出冒烟）
   - `python ../scripts/script_parity_test.py`（shim 不漂移）
3. **清理 stale**：同步输出里的"全局多余"文件，逐个确认后删除，禁止盲删。

## 方法源

- `references/install-verify.md`（复制原则、stale 处理、三测试说明）

## 降级

- 全局目录不可写 → 列出差异清单交用户手动复制，禁止声称"已同步"。
- 任一测试失败 → 如实报告失败项与原因，禁止只同步不验证、禁止带病声明"更新完成"。

## 本器官自带（可独立工作）

- `SKILL.md`：安装/验证流程与降级
- `references/install-verify.md`：安装与验证方法
- `scripts/`：`sync-global.py`（统一安装/更新）+ `organ_contract_test.py` / `organ_effect_test.py` / `script_parity_test.py`（完整性测试）+ `collaboration_skill_audit.py`（协作 skill 筛选审计）
