---
name: conductor-git
description: conductor 的 git 操作器官。收到提交代码/建隔离工作区/合并收尾请求，或改码场景走到提交、worktree、finish 时机时加载；只执行 git 操作并留证据，不决定是否合并/推送——那是用户的决策。
---

# conductor-git · git 操作器官

> conductor 机体的"手脚（git）"：worktree 隔离、任务内提交、S5 收尾交付。执行者，不是决策者——
> 合并/推送/丢弃是用户的选择，本器官只给菜单和后果。

## 输入

- 时机信号：设计确认后（worktree）/ 每任务 RED→GREEN 完成后（commit）/ S5 全绿后（finish）/ 用户直接说"提交代码"
- 当前仓库状态：`git status` / `git rev-parse` 探测结果 / 测试基线状态

## 输出

- 隔离区：干净的 worktree + 绿色或全空测试基线
- 提交：精确暂存文件 + 规范 message + hooks 通过的 commit hash
- 收尾：全绿证据 + 3/2 选项菜单 + 用户选择执行结果 + worktree 清理证据

## 执行

1. **worktree**：按 `references/worktree.md`——先检测已有隔离（`GIT_DIR != GIT_COMMON` 即已在 worktree，跳过创建）→ 优先宿主原生工具 → 无原生才 `git worktree add` 回退；建区前必验 `.gitignore`。
2. **commit**：按 `references/git-commit.md`——只暂存本任务精确文件；message 说清"为什么"；hooks 失败修根因，**禁止 `--no-verify`**；RED 阶段不提交，GREEN 后才提交。
3. **finish**：按 `references/finish.md`——先在**即将集成的那棵树**重跑完整测试（"早些时候绿过"不算）→ 确认 base branch → 给菜单（普通仓库与命名分支 3 选、detached HEAD 2 选）→ 执行 → 清理。丢弃只在用户明确要求时提供。
4. 三步都是时机触发：场景链里标了 `git` 才调；用户一句"提交代码"= 只做 commit 步，不越权做 finish。

## 方法源

- `references/worktree.md`（隔离与基线）
- `references/git-commit.md`（提交纪律与红线）
- `references/finish.md`（收尾菜单、执行与清理）

## 降级

- 沙箱拒绝 git 权限 → 告知用户，改当前目录工作并跑基线测试，登记「git 阻断」。
- 非 git 目录 → 本器官不适用，交回 conductor 重路由。
- push 被拒 → 先调查远端变化并报告；**绝不擅自 force-push**，仅用户明确要求才强推。
- 清理被拒（含未提交文件）→ 展示 `git status` 让用户选，禁 `--force`。

## 本器官自带（可独立工作）

- `SKILL.md`：角色、I/O、执行与降级
- `references/`：worktree / git-commit / finish 三份方法文档
- `scripts/`：无（git 操作由宿主执行，本器官只定纪律与红线）
