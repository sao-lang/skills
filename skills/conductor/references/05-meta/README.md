# conductor references 索引

> conductor 本体只保留 8 份机体级文档；方法文档已拆到同级 `conductor-*` 器官目录。
> 完整器官 I/O 与加载映射见 `../01-routing/organ-registry.md`（本机体唯一的器官总线）。

## 机体保留文档（按需读）

| 文件 | 何时读 | 职责 |
|---|---|---|
| `../01-routing/organ-registry.md` | S1（必读） | 11 器官清单、阶段调用、筛选结果、状态纪律、测试入口 |
| `../01-routing/skill-matrix.md` | 需查阶段加载/安装时 | 阶段→器官调用表；外部 skill 已全部处理 |
| `../02-engineering/engineering-catalog.md` | 想知道能力去向时 | 原 superpowers 能力现在归哪个器官 |
| `../04-guards/source-purity.md` | S3/S4（改码必触发） | fake 实现/动态类型/意图空白门禁；脚本在本体 `scripts/` |
| `../../conductor-git/references/git-commit-rules.md` | S3 绿后 / S5 提交前 | commit 时机、message、暂存纪律 |
| `../04-guards/release-checklist.md` | 场景 12 / 发版 | 版本、CHANGELOG、tag、回滚 |
| `README.md`（本文件） | 维护 skill 时 | 机体文档索引 |
| `roadmap.md` | 想知道某能力为何这样设计 | 激活记录与决策 |

## 器官自带文档（不在本体内）

| 器官 | 自带 references（举例） | 自带 scripts |
|---|---|---|
| `conductor-router` | routing / cost-tiers / router-prompt / scenarios | — |
| `conductor-brainstorm` | brainstorm-plan / grill-design-SKILL / examples-to-spec / design-spec-template | — |
| `conductor-tdd` | engineering-tdd / test-strategy / coding-rules-* | verify.py |
| `conductor-review` | independent-review / engineering-code-review / code-quality-review-SKILL / code-quality-review-output-contract / security-redlines | review_gate.py |
| `conductor-ledger` | commitment-ledger / migration-integrity / tech-debt-ledger | commitment_ledger.py / migration_ledger.py / overview_path.py |
| `conductor-overview` | overview / handoff-SKILL | overview_path.py |
| `conductor-impact` | architecture-contracts / contract-migration | impact_analysis.py |
| `conductor-debug` | engineering-debugging | — |
| `conductor-git` | git-commit | — |
| `conductor-subagent` | dispatch | — |
| `conductor-spec` | change-contract-template / spec-method | contract_check.py |
| `conductor-learn` | learning-method / lessons-template | learn_capture.py |

> 加载纪律：S1 只读 organ-registry + routing + cost-tiers；scenarios 按节；其余触发才读。
> 废弃的外部 skill 已物理删除，不再留桩；如需追溯历史，看 `roadmap.md`。
> `roadmap.md` 是历史决策记录；当前状态以 `../01-routing/organ-registry.md` 与 `skill-matrix.md` 为准。
> 文档中 `scripts/xxx.py` 默认以 conductor 目录为 cwd；跨器官调用写相对路径。
> `verify / review_gate / overview_path / commitment_ledger / migration_ledger / impact_analysis` 是薄 shim，实现唯一真相源在器官目录；漂移由 `script_parity_test.py` 检查。
