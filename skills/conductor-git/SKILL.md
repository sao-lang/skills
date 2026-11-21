---
name: conductor-git
description: conductor 的 git 操作器官。收到"提交代码"请求，或改码任务 RED→GREEN 完成走到提交时机时加载；只执行 git 操作并留证据，不决定是否推送——强推等危险操作必须用户明确要求。
---

# conductor-git · git 操作器官

> conductor 机体的"手脚（git）"：把每个任务的绿灯成果变成干净、原子、可回溯的提交。
> 执行者，不是决策者——推送与否、是否 force 是用户的决定。

## 输入

- 时机信号：每任务 RED→GREEN 完成（commit 时机）/ 用户直接说"提交代码"
- 本任务的精确文件清单（来自计划/任务 brief）与测试通过状态

## 输出

- commit hash + 符合规范的 message + hooks 通过
- overview 变更清单里追加一行（hash + 简述）

## 执行

1. **只暂存本任务精确文件**：`git add` 逐个加，禁 `git add -A`/`git add .`；提交前 `git status --short` + `git diff --cached --stat` 两步核对。
2. **message 规范**：`<type>(<scope>): 中文简述`（≤72 字符），body 说"为什么"；完整规则与示例见 `git-commit-rules.md`。
3. **hooks**：失败修根因，**禁止 `--no-verify`**；红灯不提交，GREEN 后才提交。
4. **留证据**：commit hash 记入 overview；提交后 `git log --oneline -1` 核对。
5. 时机触发：场景链里标了 `git(commit)` 才调；用户一句"提交代码"= 只做提交，不越权做其他 git 操作。

## 方法源

- `references/git-commit.md`（提交纪律摘要）
- `git-commit-rules.md`（完整提交规则：message 规范、暂存纪律、红线、检查清单）
- `references/release-checklist.md`（发版清单：版本、CHANGELOG、tag、回滚；配 `../scripts/release_notes.py` 出草稿）

## 降级

- 沙箱拒绝 git 权限 → 告知用户，登记「git 阻塞」，禁改断言或跳过验证硬提交。
- 非 git 目录 → 本器官不适用，交回 conductor 重路由。
- push 被拒 → 先调查远端变化并报告；**绝不擅自 force-push**，仅用户明确要求才强推。

## 本器官自带（可独立工作）

- `SKILL.md`：角色、I/O、执行与降级
- `references/git-commit.md`：提交纪律摘要
- `references/release-checklist.md`：发版清单
- `scripts/release_notes.py`：从 conventional commits 生成 CHANGELOG 草稿与版本建议
