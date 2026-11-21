# 器官注册表 · conductor 的机体—器官—环境架构

> 定位：**conductor 是机体**（状态机、门禁、决策权），`skills/conductor-*`（与 conductor 同级） 是器官（单一能力、可独立加载），
> **14 场景是工作环境**（只声明本环境调用哪些器官）；方法文档与脚本已**从 conductor 拆到各器官目录**，conductor 的 `references/` 只留兼容指针。每个器官自带 `references/` 与需要的 `scripts/`，可独立工作。
> 本表是"器官总线"：conductor 只按表调用，不在入口重复器官内部步骤。

## 一、器官清单（13 个）

| 器官 skill | 职责 | 调用阶段 | 输入 → 输出 | 缺失降级 |
|---|---|---|---|---|
| `conductor-router` | 场景/路径/档位规划 | S1 | 用户原句 → 执行图 + 声明（含省掉步骤） | 降级只读 9/10，绝不猜改码 |
| `conductor-brainstorm` | 需求澄清、设计拷问 | S2（场景 1/2/3/11） | 模糊需求/样例 → 规格要点 + 未决 + 假设 | 内联五问；用自带 `grill-design-SKILL.md` 方法 |
| `conductor-spec` | 活规格、变更契约 | S2（standard/full；bug 轻量） | brainstorm 输出 → 六段 change-contract + Acceptance | 无基线建 baseline；脚本缺失登记未机器校验 |
| `conductor-tdd` | RED-GREEN-REFACTOR | S3（改码/13） | 一条行为 → 红/绿测试 + verify 证据 | 环境阻断登记，禁造假绿 |
| `conductor-review` | 独立换眼 + review 门禁 + 代码审查机器证据 | S4/S5 | diff + 档位 → 报告 + gate 退出码 0；自带 `scan_gaps/source_purity/intent_gaps` 扫描 | 内联清单但门禁不放宽 |
| `conductor-learn` | 学习回写、经验沉淀 | S5（standard/full） | overview → 触发→动作条目 + 回写目标 | 目标不可写登记阻塞；lite 跳过须声明 |
| `conductor-ledger` | 承诺外置、断点、零未勾销 | S0/S4/S5 | 多来源 → 紧凑台账 + check 结论；自带 `debt_ledger.py` 技术债扫描 | 重建台账，禁刷状态 |
| `conductor-overview` | 会话记录两-tier压缩 | S0/收尾 | 主题+状态 → L0 主文件 + `.details.md` | 主文件 create；详情可缺 |
| `conductor-impact` | 影响面草稿 | S1/S4（5/7） | 符号/文件/diff → 引用者 + 建议测试 | 人工列直接引用者并声明未全量 |
| `conductor-debug` | 根因与最小复现 | 场景 8 | 现象/报错 → 根因 + 复现 + 回归要求 | 复现不了停下问用户 |
| `conductor-git` | 任务内提交与发版 | 条件触发（每任务 GREEN 后；发版走 `release_notes.py` + release-checklist） | 任务文件清单 → commit hash + overview 变更行 | 沙箱拒绝登记 git 阻塞；非 git 目录交回重路由 |
| `conductor-subagent` | 子代理派发（全新上下文执行任务，省主上下文） | **任何适用多代理的场景**（改码 S3、批量调研、多文档产出、并行分析等）按判据条件触发 | 任务 brief → 子代理结果 + 评审/复核结论 | 无子代理能力则主上下文直做并声明；连续返修 ≥2 轮停下问用户 |
| `conductor-sync` | 统一安装/更新 conductor 家族到智能体全局目录 + 完整性三测试 | 用户说同步/安装/更新 skill 时；改完 skill 落全局时 | 项目 skills/ → 全局复制清单 + 三测试通过计数 | 列差异交用户手动复制；测试失败如实报告禁交付 |

## 二、阶段 → 器官调用（standard/full；lite 按 `../../../conductor-router/references/cost-tiers.md` 裁剪）

| 阶段 | 必调器官 | 按触发调 | 门禁 |
|---|---|---|---|
| S0 | `conductor-overview` | `conductor-ledger`（有隐含清单） | overview L0 存在、状态文件已忽略 |
| S1 | `conductor-router` | `conductor-impact`（跨模块/full） | 路由声明含场景/路径/档位/省掉 |
| S2 | `conductor-brainstorm` | `conductor-spec`（standard/full）、自带 `design-spec-template` | 规格未确认不动手；契约未确认不进 S3 |
| S3 | `conductor-tdd` | 自带编码规则（最小完整改动内联） | 先红后绿、编码规则已读 |
| S4 | `conductor-tdd`（证据） | `conductor-impact`、`conductor-ledger` | `verify.py` + `source_purity --strict` |
| S5 | `conductor-review` | `conductor-ledger`、`conductor-learn`（standard/full） | `review_gate.py` 退出 0、台账零未勾销；learn 留痕 |

**路由纪律**：同一阶段可由多个器官协作，但**决策权只在 conductor**——器官给结论/证据，不自行推进阶段、不自行放行。

**条件加载**：档位决定"跑多深"，器官是否真的加载由 `../../../conductor-router/references/cost-tiers.md` 第三节（器官级条件加载表）按当前环境与用户输入判——命中跳过条件就跳，但每个跳过必须写进路由声明"省掉"并带依据。

## 三、协作 skill 筛选结果（审计脚本 `collaboration_skill_audit.py`，现归 conductor-sync）

| skill | 得分 | 结论 |
|---|---|---|
| `grill-design` | 6 | **改名并入** `conductor-brainstorm/references/grill-design-SKILL.md` |
| `code-quality-review` | 6 | **改名并入** `conductor-review/references/code-quality-review-SKILL.md`（+ output-contract） |
| `handoff` | 6 | **改名并入** `conductor-overview/references/handoff-SKILL.md` |
| `graphify` | 3 | DEPRECATE（冷启动成本高，与 impact 脚本重复） |
| `ponytail` | 3 | DEPRECATE（最小改动原则已内联进 `conductor-tdd`） |
| `caveman` / `grill-me` / `ponytail-review` / `caveman-compress` / `metago-code-review-deep` | ≤1 | DEPRECATE（重复或未被主链调用） |

> 废弃 skill 已**物理删除**（项目与全局均删），conductor 零外部依赖；改造后的器官自带方法原文，不依赖任何 stub。

## 四、状态文件纪律（器官产生的运行痕迹）

| 文件 | 最小内容 | 规则 |
|---|---|---|
| `.conductor-session.json` | `{"sid":"8位短hash"}` | 不写 topic/created/status；兼容旧 `session_id` |
| `.commitment-ledger.json` | 紧凑 JSON，空字段不写，id 不重复存 | 详情用 `commitment_ledger.py show` 看，不整份读进上下文 |
| `.migration-ledger.json` / `.purity-baseline.json` | 同类最小状态 | 首次生成时自动追加进目标项目 `.gitignore` |
| `change-contract.md` | 六段变更契约，非运行痕迹 | 项目内持久化；Acceptance 进入 `.commitment-ledger.json` |
| `<organ>/references/lessons.md` | 触发→动作条目 | 技能级回写，默认 dry-run 后人工确认 |

## 五、测试入口（测试套件归 conductor-sync）

```bash
python skills/conductor-sync/scripts/organ_contract_test.py
python skills/conductor-sync/scripts/organ_effect_test.py
python skills/conductor-sync/scripts/script_parity_test.py
python skills/conductor/scripts/preflight.py --project-root . --verify-organs
# 改完 skill 统一安装/更新到全局：
python skills/conductor-sync/scripts/sync-global.py
```

测试只验证**接线、契约、降级路径与状态文件压缩**，不声称替代真实 LLM 会话效果评估；真实调用效果由 scenario 冒烟清单人工复核（见 `../05-meta/roadmap.md`）。
