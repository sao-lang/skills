# 十四场景详细流程

> 每场景 = 一段"主控归属 + 加载项 + 禁止项 + 下一步"的明确指令。S0 建/续 overview（同会话追加、新会话才建，见 overview.md）、S5 收尾对所有场景通用。
> **主控统一为 conductor**：每场景写成一条**器官链**（如 `conductor-brainstorm`→`conductor-tdd`→`conductor-review`）；旧称 `brainstorm/tdd/review` 是器官的简写，映射见 `organ-registry.md`。
> 能力是 conductor 内化的工程节点（来源/契约见 `engineering-catalog.md`，方法见 `engineering-*.md`），不是外部 skill。
> **加载纪律**：S1 路由时只需读下方「I/O 契约表」判定衔接；执行到某个具体场景时，再读该场景那一节。不要整份通读。
> **成本档位**：执行前先按 `cost-tiers.md` 判 lite/standard/full——lite 跳过下方通用前置 2b/3/5b、活规格(spec)与学习回写(learn)、S5 不派独立子代理（改用 `review_gate.py --lite`）；standard/full 在 S2 后跑 `conductor-spec`、S5 gate 通过后跑 `conductor-learn`。档位与"省掉"必须写进 S1 声明。
> **条件加载**：同档位内器官是否真的跑，按 `cost-tiers.md` 第三节条件加载表按实况判（如单任务不派子代理、无清单跳台账、用户"先不提交"跳提交）；跳过必须写进声明并带依据。subagent 与 git(commit) 是条件触发，不写进链就默认不跑。

## 交付前独立 review 门禁（standard/full 改码场景必做；lite 走轻量复核）

凡有代码改动的场景（1/4/5/6/7/8/13），standard/full 档由 **器官 `conductor-review` 派全新上下文子代理**跑 `code-quality-review`；lite 档走轻量复核（见 `cost-tiers.md`）
（七维+接线四问，重点查功能遗漏/断点），Blocker 清零才准交付；执行者 S4 自查不可替代。
只读(9/10)、纯文档(2/3/11)不触发；**lite 档例外**：不派子代理，写 overview 的「轻量复核（lite）」章节（三问+证据）并跑 `review_gate.py --overview <path> --lite`。**规则全文**见 `../../conductor-review/references/independent-review.md`。
**机器校验**：`review_gate.py --overview <path>` 核对 overview 的「独立 review 结果」章节+Blocker 清零+review 证据（内嵌报告章节有分级/证据，或外部报告文件存在）；
退出码非 0 禁止收尾；非触发场景用 `--waived` 显式豁免；lite 用 `--lite`（与 `--waived` 互斥）。

## 通用前置（所有场景必做）

1. 依赖预检：`python ../../conductor/scripts/preflight.py --project-root .`，缺失项先解决或登记例外。
2. 定位 overview：跑 `../../conductor-overview/scripts/overview_path.py --project-root . --topic "<主题>"`，按返回 path/action 建或续（会话指针 `.conductor-session.json` 锚定，同会话归同一文件；换任务加 `--new-session`）。详见 `../../conductor-overview/references/overview.md`。
2b. 环境探测（lite 跳过；standard 只在有真实环境依赖信号时跑；full 必跑）：跑 `../../conductor/scripts/env_probe.py --project-root .`，把真实环境需求/可用性（docker、集成测试目录、依赖信号）写入 overview 环境节。**依赖真实环境的功能必须留在计划内**（见 `architecture-contracts.md` §4.5），不许因当前无环境预先砍掉。
3. 读上次 overview L1 交接（lite 跳过，除非续接且 L0 信息不足）：定位未完成项与下一步。
4. 路由声明：向用户说清"场景 / 加载 skill / 禁止项 / 下一站"（见 routing.md §4.5）。
5. **场景链**（多动作）：按链声明每段场景+路径+闸门，逐段执行。前段产出写入 overview、后段先读；
   设计闸门——段1 拷问设计(9)、段2 按设计写代码(6)时，设计漏洞未解决**禁止写代码**，先问用户是否补设计；
   只读段结束不自动进改码段，遇闸门停下问。
5b. **承诺台账采集**（lite 跳过——前提确无隐含清单；凡有隐含待办清单的场景 4/5/6/7/8/9/11/12 必做）：按 `commitment-ledger.md` 跑
   `commitment_ledger.py init`——规格/差异/finding 用 `--from-list`/`--stdin` 采集，模块用 `migration_ledger.py init`，
   机器能扫的自动扫、人只补语义；台账写入 overview 交付产物。新会话先 `next`/`show` 定位断点。
   防膨胀：只卡 S0/S4/S5 三个出口，不插到每一步。
6. **样例补全识别**：用户举例（比如/例如/参考X那样/改这里）时按 `examples-to-spec.md` 判断是否启用——
   启用则在声明中说明，设计/实现阶段按四步法补全"样例之外覆盖"，补全项分类确认后再落地。
7. **活规格与学习回写**（standard/full；lite 须在"省掉"声明）：S2 确认后跑 `conductor-spec` 生成/更新六段 `change-contract.md`，`contract_check.py` 退出 0 且 Acceptance 灌入台账后才进 S3；S5 review gate 与台账收口后跑 `conductor-learn`，默认 dry-run，人工确认后再回写，禁止自动污染 skill。

## 场景 I/O 契约表（链式组合的类型系统）

构建执行计划时用本表校验"前段输出能否喂给后段输入"——契约不符停下问用户，不硬拼。
这把"设计闸门"从特例泛化为契约推导。

| 场景 | 输入契约 | 输出契约 | 路径 |
|---|---|---|---|
| 1 初始化 | 需求+技术选型 | 项目骨架+设计文档 | 改码 |
| 2 架构设计 | 需求 | 架构文档+未决清单 | 文档 |
| 3 补充设计 | 设计文档+问题清单/缺口 | 更新后设计文档 | 文档 |
| 4 项目开发 | 规格+设计 | 新功能代码+测试 | 改码 |
| 5 迭代 | 已有功能+变更要求 | 调整后代码 | 改码 |
| 6 设计驱动重构 | 设计文档（须已解决已知问题） | 符合设计的代码改动 | 改码 |
| 7 重构 | 现有代码+行为测试 | 等价重构的代码 + 全收口迁移台账 | 改码 |
| 8 解 bug | 故障现象+复现 | 修复+回归测试 | 改码 |
| 9 拷问设计/代码 | 设计文档或代码 | **问题清单**（带行号/严重度） | 只读 |
| 10 代码库理解 | 代码库 | **代码地图+调用链+断点清单** | 只读 |
| 11 文档/注释同步 | 代码签名+现有文档/注释 | 同步后文档/注释+差异清单 | 文档 |
| 12 门禁验收 | 全量变更 | **门禁报告+证据** | 验证 |
| 13 测试补课 | 已有代码（行为已知） | 新增测试+覆盖率证据 | 验证 |
| 14 文档/资源清理 | 资源路径 + 清理意图（删除/归档/移动/纯内容改） | **资源操作完成 + 变更清单**（含可逆性说明） | 文档·清理变体 |

**合法衔接**：9→3（问题清单+设计文档）；10→8/7（代码地图作背景）；3→6（更新设计）；
10→6→验证→14（先读懂文档→按设计改码→验证通过→最后删文档，**销毁排最后**，见 routing §3.5）。
**非法衔接示例**（停下问）：9 的问题清单直接喂 6（6 要设计文档）→问"是否先落实成设计更新(3)？"；
10 的代码地图喂 12（要全量变更）→地图不是变更，问意图。

## 场景 1 · 项目初始化
- **能力链**：`brainstorm`（需求→设计文档）→`plan`（设计→计划），**到计划为止，不写业务代码**。
- **契约**：设计文档喂 plan，plan 输出计划后本场景结束。
- **工具**：brainstorm 调 `grill-design-SKILL.md` 拷问技术选型；建 overviews 目录；编码规则就位。
- **禁止**：规格未确认前生成实现代码；引入未选型依赖。**下一站**：用户确认设计→项目开发。
- **新增器官**：standard/full 在 brainstorm 后跑 `conductor-spec` 出首个 change-contract（Acceptance 入台账），review gate 通过后跑 `conductor-learn` 回写；lite 跳过并声明。

## 场景 2 · 架构设计
- **能力链**：`brainstorm`（架构版：设计树展开），**止步于架构规格**，不进 `plan`/`execute`。
- **契约**：产出架构文档+未决清单，作为后续"补充设计/项目开发"输入。
- **工具**：`grill-design-SKILL.md` 逐层拷问架构决策（每分支必须有结论、不许静默假设）；加载 `architecture-contracts.md` 作约束。
- **样例补全**：用户用举例描述功能/模块时，按 `examples-to-spec.md` 归纳意图、外推同类项与边界，设计文档**显式列"样例之外覆盖"节**，补全项交用户确认。
- **产出**：架构文档（分层/模块/契约/数据流/装配入口）+未决假设清单。**禁止**：架构未确认前写实现；用"通用框架"掩盖未定选型；遗漏装配层(composition root)。
- **下一站**：架构确认→补充设计（细化）或项目开发（落地）。

## 场景 3 · 补充设计
- **能力链**：局部 `brainstorm`（**只针对缺口分支**），不重开已确认结论，不进 `plan`/`execute`。
- **契约**：输入旧设计+问题清单，输出更新后设计文档（契约匹配场景6输入）。
- **工具**：定位已有设计与未决清单→只对未决部分用 `grill-design-SKILL.md` 拷问→增量写入（标注变更点）。
- **产出**：设计补充章节+更新的未决清单。**禁止**：重写已确认且未宣布变更的设计；静默改历史结论（必须留变更记录）。
- **下一站**：补充确认→若涉及既有代码改动，进入设计驱动重构。

## 场景 4 · 项目开发
- **能力链**（最完整）：`brainstorm`→`plan`→`subagent`（条件：≥3 独立任务才派；不限改码，其他多代理场景同样适用）→每任务内嵌 `tdd`+`git`(commit，条件)→`review`（每任务间）→`verify`(S4)→`review`（终审）。subagent/git(commit) 按 cost-tiers 条件加载表可跳。
- **契约**：设计→计划→任务产出→评审结论→验证证据→全绿变更，逐级喂下一能力；任一环断裂停下。
- **工具**：S0 预检+S4 自省脚本；`tdd` 阶段遵守 coding-rules（ponytail/caveman 已内联为最小改动原则）。
- **样例补全**：`brainstorm`/`plan` 按 `examples-to-spec.md` 补全用户举例为完整规格（含异常/边界/同类项）；`execute` 按补全清单实现，别只做点名的那几个。
- **禁止**：无失败测试不写实现；魔法字符串不具名不提交；S4 未过不进 review。**下一站**：全绿后收尾→写 overview。
- **新增器官**：standard/full 在 brainstorm 后跑 `conductor-spec` 固化六段契约，review gate 通过后跑 `conductor-learn`；lite 跳过并声明。

## 场景 5 · 项目迭代
- **能力链**：`brainstorm`（轻，确认变更范围）→`plan`→`tdd`（锁行为+实现）→`review`→`verify`→收尾。
- **契约**：变更要求→影响面→任务计划→实现→评审→验证证据。
- **工具**：`impact_analysis.py --symbols/--files/--diff` 出影响面草稿（引用者+建议测试，需人工核实）；关键边必须打开源码核对；涉接口改动加 `contract-migration.md`；回归检查清单。
- **禁止**：未列影响面前改动；破坏既有公共契约（除非规格明确要求）。**下一站**：回归全绿→review→收尾。
- **新增器官**：standard/full 先跑 `conductor-spec` 产出 Delta/Affected/Acceptance，再把 Affected 喂 `conductor-impact`；review gate 后跑 `conductor-learn`；lite 跳过并声明。

## 场景 6 · 设计驱动重构（依新设计或补充设计）
- **触发**：用户给新/补充设计，据此改现有代码（区别于场景7"无新设计的纯结构优化"）。
- **能力链**：`plan`（按差异拆任务）→每条差异用 `tdd` 锁新契约(红)→改实现(绿)→`review`（逐条核接线）→`verify`→收尾；接线断裂触发 `debug`。
- **契约**：新设计→差异清单→行为测试→实现→接线核对证据。
- **工具**：①加载 `architecture-contracts.md` 做**设计差异清单**（逐条列"新设计vs现状"契约变化）；涉及接口签名/DB迁移加 `contract-migration.md` 核四同步与迁移可逆性；②每条差异先写行为测试锁新契约(红)再改实现(绿)；③改完按差异清单逐条核对接线，写入 overview。
- **禁止**：边重构边夹带设计外新功能或顺手优化（最小改动原则也禁扩大 diff）；无测试保护改结构；静默偏离设计；只改代码不改/核对设计文档。
- **下一站**：差异清单逐条勾销+全绿→review→收尾；发现新设计有漏洞→补充设计场景。
- **新增器官**：standard/full 用 `conductor-spec` 固化新旧设计 Delta 与 Invariants，Affected 喂 `conductor-impact`；review gate 后跑 `conductor-learn`；lite 跳过并声明。

## 场景 7 · 项目重构
- **能力链**：`inventory`（盘点建台账）→`tdd`（行为基线锁等价性）→逐块改结构+差分→`review`→`verify`（行为等价证据）→收尾。
- **契约**：现有代码+行为测试→等价重构代码→等价性证据+**全收口的迁移台账**。
- **工具**：**迁移完整性守卫**——先读 `../../conductor-ledger/references/commitment-ledger.md`（通用框架）再读 `../../conductor-ledger/references/migration-integrity.md`（场景7特化），主用 `migration_ledger.py`（底层=承诺台账 shim）：
  ①`init` 扫码建台账（清单来自代码非 AI 印象，`kind` 区分 entry/route/module/config，入口路由优先迁）；
  ②基线 characterization test 锁行为（证据填台账 `evidence`）；③逐块迁移+新旧差分对跑，一次一项；
  ④`check --path src --strict` 收尾门禁（pending/in_progress/无证据/skipped 无理由/drift 一律 FAIL）；
  ⑤中断写 `status=in_progress`+`checkpoint`，换会话先 `next` 定位续接点。
  ⑥**源码纯净存量基线**：重构前 `source_purity.py baseline --path src` 快照老代码的 fake/不具体类型，
  改到某文件时 `check --scope <changed> --strict` 才让该文件的存量进入负责范围——**避免为清存量而扩大 diff**。
  `impact_analysis.py` 出影响面；最小改动原则砍复杂度（原 ponytail 已内联）；涉接口/DB 加 `contract-migration.md`。
- **禁止**：**夹带新功能**；无测试保护改结构；扩大 diff 到无关代码；**只搬看得见的模块、不核台账**；
  **迁移中新增模块不跑 `init --merge` 纳入台账**（即 drift 漏登记）；为过闸门把 pending 刷成 verified（evidence 会露馅）。
- **下一站**：`check --strict` 退出 0 + 行为等价 + 独立 review 清零 → review→收尾。
- **新增器官**：standard/full 在 ledger shim 后跑 `conductor-spec`，把迁移 Invariants 与 Acceptance 固化并喂 `conductor-impact`；review gate 后跑 `conductor-learn`；lite 跳过并声明。

## 场景 8 · 解 bug
- **能力链**：`debug`（4阶段根因）→`tdd`（复现测试先红后绿）→`verify`（原bug测试+回归）→`review`→收尾。
- **契约**：故障现象→根因→复现测试→修复→回归证据。
- **工具**：`engineering-debugging.md` 的**最小复现构造**（issue→缩到最小→写成必红测试→才追根因）；根因台账（现象/假设/证据/结论）；回归证据（复现测试先红后绿）。
- **禁止**：未造出可运行最小复现就猜改；只修表象不加复现测试。**下一站**：复现测试转绿+无新回归→review→收尾。
- **新增器官**：standard/full 在 debug 出根因后跑 `conductor-spec`（轻量契约：根因 + 回归 Acceptance）；review gate 后跑 `conductor-learn`；lite 跳过并声明。

## 场景 9 · 拷问代码 / 设计（纯只读）
- **能力链**：无（不改代码）。**只读路径**：S0/S1→只读分析→写 overview→结束，不进 S2/S3/S5。
- **主导**：拷问设计→器官 `conductor-brainstorm`（自带 `grill-design-SKILL.md`）出设计树+未决清单；拷问代码→`conductor-review` 七维方法 + 缺口台账法。
- **禁止**：改任何生产代码；把"发现问题"变成"顺便修了"。**下一站**：结构化问题清单→用户决定是否转迭代/重构/解bug。

## 场景 10 · 代码库理解（纯只读）
- **能力链**：无。**只读路径**：S0/S1→只读分析→写 overview→结束。
- **主导**：①`architecture-contracts.md` 接线四问逐模块核；②`scan_gaps.py` 拿断点线索（弱信号需核实）；③关键调用链打开源码核对。
- **产出**：模块职责+调用链+断点清单+理解笔记→写入 overview。**禁止**：改代码；只看单文件下结论；把静态推断当已验证事实（关键边必须打开源码核对）。
- **下一站**：用户决定转拷问/迭代/重构/解bug。

## 场景 11 · 文档/注释同步（文档路径）
- **能力链**：局部 `brainstorm`（只核差异）→改文档/注释→`verify`（核签名，不跑新功能 tdd）。**路径**：S2→S3'(只改文档)→S4→S5。
- **契约**：代码签名+现有文档/注释→差异清单→同步后文档/注释。
- **覆盖范围**（均为"说明性文字与代码一致"）：①独立文档 .md/设计文档与代码不符→修订文档；②代码内注释/docstring（补注释、修过时注释、补 docstring、注释与签名不符）→修订注释。**不改代码行为**，故**不触发 S3 的 TDD、不触发 S5 独立 review**；改后按 `coding-rules-common.md` §0/§3 注释方案核对。
- **工具**：`grill-design-SKILL.md` 拷问完整性 + `architecture-contracts.md` 核契约；差异逐条勾销拿行号证据。
- **样例补全**：用户点名改一处时按 `examples-to-spec.md` §4B **全文搜同概念其他出现**（其他章节/文档/索引/示例；注释则搜同模块同类函数/字段 docstring），列清单确认后一次改全。
- **禁止**：只改点名处留同概念其他不一致（G07/G13/G15）；只改代码不改文档；静默改历史结论；**补注释夹带代码逻辑改动**（改行为走场景5）。
- **下一站**：差异全勾销+签名核对通过→S5 收尾。

## 场景 12 · 门禁验收 / 发布（验证路径）
- **路径**：跳过新功能设计，S4 全量验证→S5 交付判定。**能力链**：无（只验证）。
- **主导**：`preflight.py`→`verify.py --lang <每个语言>`→`scan_gaps.py`（conductor-review）→`debt_ledger.py`（conductor-ledger）→`conductor-review` 七维审查（Blocker 清零门禁）。
- **出口**：门禁全绿+全部证据入 overview，否则**禁止合并/发布**。涉及发布按 release-checklist（conductor-git 自带）走版本/CHANGELOG/tag/回滚，`release_notes.py --since <tag>` 出草稿。
- **禁止**：带 Critical/阻塞项收尾；用"测试大概没问题"代替退出码。**下一站**：全绿→交付→写 overview。

## 场景 13 · 测试补课（验证路径，TDD 变体）
- **路径**：S2(锁行为)→S3'(只补测试)→S4(跑覆盖率)→S5。
- **能力链**：`tdd` 变体——先补 characterization test 锁现有行为(红)，**不新增业务实现**(绿来自已有代码)→`verify`（跑覆盖率）。
- **契约**：已有代码→行为测试→覆盖率证据。**工具**：`test-strategy.md`；按达标口径核对覆盖率/通过率；识别假绿。
- **禁止**：为凑覆盖率写无断言测试；借机改实现行为（除非测试暴露真 bug 且用户确认）。**下一站**：覆盖率达阈值+全绿→S5。
- **新增器官**：standard/full 用 `conductor-spec`（轻量）锁定覆盖率 Acceptance；review gate 后跑 `conductor-learn` 回写测试盲区；lite 跳过并声明。

## 场景 14 · 文档/资源清理（文档路径·清理变体）

- **触发**：删除/归档/移动文档或资源，或改动与代码一致性无关的文档内容（纯整理、重命名、搬家、清临时产物）。区别于场景 11（让文档去对齐代码）。
- **路径**：S1 → 确认无消费者依赖该资源 → 执行清理 → 写 overview → **结束**。无代码改动，**不跑 TDD、不跑 verify、不触发独立 review**。
- **能力链**：无（或前置一个只读理解节点确认影响面）；销毁操作本身不是工程能力。
- **契约**：输入=资源路径+清理意图，输出=资源操作完成+变更清单（含可逆性说明：git 可恢复？有备份？）。
- **时序纪律**（见 routing §3.5）：若本场景出现在场景链中、且有其他节点要用这个资源，**销毁排到最后**，闸门=那些节点已完成且验证通过。禁止按字面顺序先删后用。
- **工具**：删除/移动前确认资源是否被引用（grep / `impact_analysis.py`）；不可逆操作无确认不执行。
- **禁止**：资源还有消费者就删除；无确认执行不可逆操作；借"清理"夹带代码/行为改动（那走场景 5）。
- **下一站**：变更清单写入 overview「变更文件清单」→ 结束，或回到主任务链后续节点。

## 只读出口（只读路径专用）
只读路径（9/10）出口**不是"测试全绿"**，而是"发现清单/代码地图/证据台账已交付且每条带源码位置或证据"；S4 走只读变体（不跑 verify）。
禁止对只读场景套用"未达标不许进 review"的改码门禁——会空转或误判。

## 缺口台账法（S4 自省专用）

脚本生成草稿，人工逐条核实——脚本给线索，判断归 AI，两者都不省：
```bash
python ../../conductor-review/scripts/scan_gaps.py --path src     # 缺口台账草稿
python ../../conductor/scripts/verify.py --lang <lang>            # 验证命令退出码（薄 shim）
python ../../conductor-ledger/scripts/debt_ledger.py --path src   # 技术债台账草稿
python ../../conductor/scripts/commitment_ledger.py check --ledger .commitment-ledger.json --strict  # 承诺台账收口门禁（全场景，零未勾销，薄 shim）
python ../../conductor/scripts/migration_ledger.py check --ledger .migration-ledger.json --path src --strict  # 迁移收口门禁（场景7 shim）
```
> 技术债登记口径见 `tech-debt-ledger.md`——债标记≠已登记，未关闭项必须进 overview「未完成项」。

逐条核对（每项需证据：文件:行号/测试输出/覆盖率），拿不出不得标完成：
1. **功能遗漏**：设计/需求每条承诺有无对应实现？（对照 `architecture-contracts.md`）
2. **功能断点**：模块"接口就绪"是否真被装配层调用？（scan_gaps 的 install 无调用者/协议无实现是弱信号，需人工确认）
3. **测试覆盖率**：达阈值？按 `test-strategy.md` 达标口径核对，警惕假绿。
4. **通过率**：测试全绿？有无 flaky/skip/xfail 掩盖？若报错，先判根因——代码 bug 必须修；环境缺失（Docker/DB 连不上）则按 `test-strategy.md` §5.5 原则三告知用户、登记「环境阻断」后可暂忽略，禁止静默跳过或伪装成通过。
5. **规则符合**：魔法字符串、注释完整性、类型明确、长度基线——以 `verify.py` 退出码为证据。
6. **安全红线**：按 `security-redlines.md` 核对密钥/注入/危险路由/成本闸门。
7. **样例补全**：`examples-to-spec.md` 的补全项是否都落地、有证据？禁止只做列举项就宣称完成。
台账写入 overview「验证结果」，失败项列「未完成项与下一步」。
