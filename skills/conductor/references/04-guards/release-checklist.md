# 发布编排 · 版本 / CHANGELOG / tag / 回滚

> 用途：把"合并之后到上线之间"的散落动作固化成清单——版本命名、变更日志、
> tag/发布、回滚预案。补上生命周期里此前空白的一段。
> 定位：按需加载——场景 12（门禁验收/发布）、S5 finish 涉及发布、用户说"发版/上线/release"时读。

## 核心认知

发布不是"合并即结束"。合并之后仍需：确定版本 → 生成变更日志 → 打 tag → 部署 → 验证 → 保留回滚路径。
全程以门禁全绿为前提（场景 12），发布编排不替代门禁，只编排门禁之后的动作。

## 前置（硬门槛）

- [ ] 独立 review 门禁通过：`review_gate.py --overview <path>` 退出码 0（改码场景）。
- [ ] 全套门禁绿：preflight / verify（含覆盖率）/ scan_gaps，证据在 overview。
- [ ] 未关闭的高优先级技术债已显式声明（见 tech-debt-ledger.md），无静默放行。

## 版本命名

- 遵循语义化版本 `MAJOR.MINOR.PATCH`：
  - breaking 变更 → MAJOR；向下兼容的新功能 → MINOR；仅修复 → PATCH。
  - 可用 `scripts/release_notes.py` 根据 conventional commits 给版本建议（feat→MINOR、fix→PATCH、BREAKING→MAJOR）。
- 预发布用 `-alpha.N` / `-rc.N`，正式版去掉后缀。

## CHANGELOG

- 用 `scripts/release_notes.py --since <上个tag>` 从 conventional commits 生成草稿（`feat/fix/refactor/docs/chore` 分组）。
- 人工润色为"用户可理解的变化"，删除内部术语；草稿不直接当最终版发布。
- 每个版本段落含：版本号 + 日期 + 变更分类 + 破坏性变更醒目提示。

## 发布步骤

1. 确认版本号与 CHANGELOG 定稿。
2. 打 tag：`git tag -a v<version> -m "release v<version>"`，push tag（遵守 git-commit-rules，不 force-push）。
3. 部署：按项目既定方式（CI/CD 或手工），记录部署版本号与环境。
4. 冒烟验证：生产环境跑关键路径冒烟测试，证据记入 overview。
5. 公告（如需）：通知相关方版本号与主要变化。

## 回滚预案（发布前必须写好）

- 明确回滚触发条件（错误率/关键功能失败/数据异常阈值）。
- 记录回滚命令或步骤（含DB迁移回滚，见 contract-migration.md 的可逆性检查）。
- 确认回滚已在暂存环境验证过；无回滚路径的发布禁止上线。

## 完成判定

- [ ] 版本/tag/CHANGELOG 就位，tag 已 push。
- [ ] 部署版本号与冒烟证据在 overview。
- [ ] 回滚预案已写且验证过。
- 缺任一项不得宣告发布完成。
