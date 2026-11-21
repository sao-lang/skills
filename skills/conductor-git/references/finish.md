# finish：收尾交付（原 conductor 7 步工作流第 7 步）

> 由 conductor-git 在 S5 全绿（review gate 退出 0、台账零未勾销）后调用。
> 方法提取自 obra/superpowers，本地化重述。

**核心原则**：验测试 → 探环境 → 给选项 → 执行 → 清理。

1. **验测试**：跑**即将集成的那棵树**的完整测试套件（"早些时候绿过"不算）。失败则停下报告，菜单在绿灯之后。
2. **探环境**（切目录前先抓 `GIT_DIR`/`GIT_COMMON`/`WORKTREE_PATH`，清理要用）：
   普通仓库（相等）→ 3 选项、无清理；worktree+命名分支 → 3 选项、按来源判断清理；
   worktree+detached HEAD → 2 选项（无合并）、宿主管理原地保留。
3. **确认 base branch**：从计划/对话/upstream 推断后**向用户确认**——合并错分支代价极高。
4. **给菜单**（普通仓库与命名分支给 exactly 这 3 个，detached HEAD 给 2 个）：
   ```
   1. 本地合并回 <base>   2. 推送并创建 PR   3. 保留分支（我之后自己处理）
   ```
   丢弃**只在用户明确要求时**提供，且要求输入 `discard` 精确确认。
5. **执行选择**：本地合并先合并→验合并结果绿→再清理 worktree 和删分支；push 用 `git push -u`；
   **push 被拒先调查远端变化，绝不擅自 force-push**（仅用户明确要求才强推）。
6. **清理**（仅合并与确认丢弃时）：`GIT_DIR==GIT_COMMON`→无需清理；worktree 在 `.worktrees/`/`worktrees/` 下→
   `git worktree remove`+`prune`；其他位置→宿主拥有，**原地保留**（有 workspace-exit 工具就用）；
   **移除被拒**（含未提交文件）→绝不擅自 `--force`，展示 `git status` 让用户选。

## git 操作红线

| 借口 | 真相 |
|---|---|
| "测试刚才绿过" | 绿只证明那棵树；集成前必须在当前树重跑 |
| "显然想合并" | 集成是用户的决定，给菜单并等待 |
| "PR 提了，worktree 是垃圾" | PR feedback 在那个 worktree 里改，保留到落地 |
| "清理被拒，--force 就行" | 拒绝意味着文件只在该 worktree，force 会永久销毁 |
| "base 显然是 main" | 确认分叉点，"显然"合并错代价极高 |
| "push 被拒，强推修复" | 被拒说明远端变了，先调查，强推需用户明确要求 |

> **条件跳过**：用户明确说"不用合并/我自己处理"、项目无 git 仓库、或本次任务未建 worktree 且改动已在主分支提交完，
> finish 可简化为"报告全绿证据 + 提交状态"，跳过菜单；跳过须写进路由声明的"省掉"。
