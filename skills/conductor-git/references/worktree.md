# worktree：隔离工作区（原 conductor 7 步工作流第 2 步）

> 由 conductor-git 在改码场景、设计确认后调用。方法提取自 obra/superpowers，本地化重述。

**核心原则**：先检测已有隔离 → 用原生工具 → 无原生工具才回退 git → 不与宿主对抗。

1. **先检测是否已隔离**（不凭肉眼）：`GIT_DIR=$(cd "$(git rev-parse --git-dir)" && pwd -P)`、
   `GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)`。
   `GIT_DIR != GIT_COMMON` → 已在 linked worktree，跳过创建。
   **submodule 陷阱**：submodule 里也成立，先用 `git rev-parse --show-superproject-working-tree` 有输出则是 submodule，按普通仓库处理。
2. **优先原生 worktree 工具**（`EnterWorktree`/`/worktree`/`--worktree` flag）——原生工具自动管目录/分支/清理；
   绕过它用 `git worktree add` 会产生宿主看不见的 phantom state（头号错误）。无原生才用 `git worktree add "$path" -b "$BRANCH"` 回退。
3. **目录优先级**：用户显式声明 > 项目内 `.worktrees/`/`worktrees/`（前者优先）> 默认 `.worktrees/`。
4. **必须先验 gitignore**：`git check-ignore -q .worktrees`——未忽略则先加 `.gitignore` **并提交**再建 worktree，否则会把整个工作树误提交。
5. **初始化 + 干净基线**：按语言装依赖（package.json→npm / Cargo.toml→cargo / requirements.txt 或 pyproject.toml→pip/poetry / go.mod→go mod），跑测试确认基线（全绿或全空）。
6. **权限被沙箱拒绝**：告知用户，改为当前目录工作，跑 setup 和基线测试。

> 创建前若用户未表态是否隔离，先征求同意："要建隔离 worktree 吗？它保护当前分支不受改动影响。"
>
> **条件跳过**：改一个文件的小修、用户明确说"直接改"、或当前目录本身没有 git 仓库时，不建 worktree；
> 跳过须写进路由声明的"省掉"。多任务大改动、用户要求可回退时必须建。
