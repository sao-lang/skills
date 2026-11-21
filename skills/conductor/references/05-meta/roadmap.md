# 路线图 · 场景与流程增强记录

> 记录已激活与候选的场景/机制，便于追踪演进。
> 本文件是历史决策记录；当前器官/脚本/路径以 `../01-routing/organ-registry.md` 与 `skill-matrix.md` 为准，旧路径仅作追溯。
> 状态：`🟢 已激活`（已进 SKILL.md、../../../conductor-router/references/routing.md、../../../conductor-router/references/scenarios.md 生效）/ `🟡 候选`（已识别未实现）。
> 当前生效工作流：**十四场景 + 五路径（含文档·清理变体）+ S0–S5**。

## 一、已激活（🟢，方案 A 全部落地于 2026-11-19）

### 场景 10 · 代码库理解（只读路径）
- 定位：补"先搞懂"缺口；加载 `graphify` + `scan_gaps.py` + `../../../conductor-impact/references/architecture-contracts.md`。
- 产出：模块职责 + 调用链 + 断点清单 + 理解笔记 → overview。
- 已写入：`../../../conductor-router/references/scenarios.md` 场景 10、`../../../conductor-router/references/routing.md` 判定表、`SKILL.md` 场景表。

### 场景 11 · 文档同步（文档路径）
- 定位：治本项目 G07/G13/G15 类"文档-代码不一致"；加载 `grill-design` + `architecture-contracts`。
- 产出：文档-代码差异清单逐条勾销，拿行号证据。
- 已写入：同上三处。
- 2026-11-19 扩展：场景 11 更名「文档/注释同步」，覆盖代码内注释/docstring 补全与修订（不改行为→不触发 TDD 与独立 review 门禁）；同步更新 SKILL.md 场景表、scenarios.md I/O 契约表与场景 11、routing.md 锚点表与消歧条款。

### 场景 12 · 门禁验收 / 发布（验证路径）
- 定位：独立化散落在 S5 的门禁；加载 preflight + verify + scan_gaps + review 全套。
- 出口：门禁全绿 + 证据入 overview，否则禁止合并/发布。
- 已写入：同上三处。

### 场景 13 · 测试补课（验证路径，TDD 变体）
- 定位：给已有代码加 characterization test，区别于 TDD 写新实现；加载 `../../../conductor-tdd/references/test-strategy.md`。
- 禁止：无断言凑覆盖率、借机改实现行为。
- 已写入：同上三处。

### 机制 1 · 路径字段（改码/只读/文档/验证）
- S1 除判场景外必判路径，决定后续阶段。已写入 `../../../conductor-router/references/routing.md` §2.5、`SKILL.md` 场景×阶段矩阵。

### 机制 2 · 只读出口
- 只读路径出口 = "清单已交付 + 证据可追溯"，非"测试全绿"；S4 拆改码/只读两变体。
- 已写入 `SKILL.md` 与 `../../../conductor-router/references/scenarios.md` 的"只读出口"。

### 机制 3 · 场景 × 阶段矩阵
- 散落的裁剪规则收敛成统一矩阵，作为 S1 硬输出。已写入 `SKILL.md` 与 `../../../conductor-router/references/routing.md`。

### graphify 接入（场景 10/9）
- 市场 skill `graphify`（代码知识图谱问答）+ 开源 `pip install graphifyy`。
- 已写入 `SKILL.md` 的"代码理解工具"段、`../01-routing/skill-matrix.md` 的 skill 清单、场景 10 步骤。
- 纪律：只给带源码位置的上下文非验证答案；冷启动有成本，短任务不用；不替代 scan_gaps。

### 依赖安装 + skill 加载纪律（2026-11-19）
- 背景：其他会话用 conductor 时 AI 未加载 handoff。根因是 handoff 当时未安装（只给了仓库地址）。
- 已装齐 11 个 skill：superpowers / grill-design / grill-me / code-quality-review /
  handoff / metago-code-review-deep / graphify（市场）+ ponytail / ponytail-review /
  caveman / caveman-compress（从 GitHub 仓库复制到用户级目录）。
- 修复软约束缺陷：SKILL.md 新增"skill 加载纪律"段——先 preflight 确认存在、
  加载失败必须显式降级并写 overview、禁止假装加载、关键依赖缺失要问用户。
- preflight 复核：8 个 skill 缺失已清零；剩余 18 项为语言验证工具缺失（另案）。

## 二、场景链（🟢 已激活 2026-11-19）

- 触发：用户一句话含多个有序动作（"先检查设计，然后写代码"）。
- 能力：解析为有序场景链，逐段判场景+路径，前段产出喂给后段，设计闸门未过禁止写代码。
- 已写入 `../../../conductor-router/references/routing.md` §3.5（切分规则/链内闸门/无顺序词默认）、声明模板（链版）、
  `SKILL.md` S1、`../../../conductor-router/references/scenarios.md` 通用前置的场景链纪律。
- 示例："先检查 M4 设计是否完整，然后根据 M4 设计方案写代码" = 场景9（只读拷问设计）
  → 设计闸门 → 场景6（按设计改码）。

## 二·补、语义路由改造（🟢 已激活 2026-11-19）

- 背景：关键词逐行匹配无法泛化（换说法就漏）。改为语义判定 + 置信度 + 可纠正。
- 语义三问（产出物/对象/时序）替代关键词，答案与措辞无关；意图锚点表降级为"语义参考非穷举"。
- 结构化路由决策：场景链[]/路径/置信度(必填)/依据(语义)/待澄清/闸门。
- 置信度分级：高≥0.8 直接走、中 0.5–0.8 声明确认、低<0.5 必须问用户给候选。
- 声明模板带置信度与语义依据；可纠正兜底不变。
- 已写入 `../../../conductor-router/references/routing.md`（§2 语义三问/§2.1 锚点表/§4 结构化决策/§4.5 声明模板）、`SKILL.md` S1。

## 二·重构、路由升级为规划器（🟢 已激活 2026-11-19）

- 认知转变：路由不是"匹配场景"而是"规划执行图"（节点=场景/边=链分支/模式=路径）。
- 有限结构算子表（顺序/条件/否定/并行/回指）是唯一枚举项；业务语义交语义理解。
- 场景 I/O 契约表（../../../conductor-router/references/scenarios.md）：链式组合做类型校验，把"设计闸门"从特例泛化为契约推导，契约不符停下问。
- 决策结构加 `假设[]` 字段，必须明示让用户否决；失败降级到只读，绝不猜改码场景。
- 执行中重规划：每节点完成后重评后续是否适用。
- 已写入 ../../../conductor-router/references/routing.md（§1 五层管线/§1.5 结构算子/§4 假设/§5 重规划/§6 降级纪律）、
  ../../../conductor-router/references/scenarios.md（I/O 契约表）、SKILL.md S1。

## 二·终、superpowers 内化 + 项目自包含（🟢 已激活 2026-11-19）

- 目标：消除"治理外壳 + 外部工程内核"两套工作流，让 conductor 成为唯一流程主控。
- 工程纪律内化：superpowers 的 7 步工作流 / 写计划 / TDD / 系统化调试 / 代码评审 / 4 理念，
  提取为 conductor 自己的 `engineering-{workflow,tdd,debugging,code-review}.md`（含来源致谢）。
- 全文改造：SKILL.md（定位/阶段矩阵/铁律）、references/01-routing/skill-matrix.md（加载表/清单/加载原则）、
  ../../../conductor-router/references/scenarios.md（委托内核→本 skill 执行）、../../../conductor-tdd/references/test-strategy.md、../../../conductor-memory/references/overview.md、preflight.py
  （移除 superpowers 依赖检查）。
- 项目自包含：conductor 用到的全部外部工具 skill 搬进 `.agents/skills/`，
  不再依赖用户级安装。
- 效果：外部流程主控依赖归零；缺工具只影响该工具，不影响流程本身。

## 二·终2、superpowers 能力逐项整合 + 场景能力链（🟢 已激活 2026-11-19）

- 背景：上一轮只把方法论提取成 4 份 engineering 文档，未逐个盘点 skill、未编排进场景——流程是空的。
- 新增 `../02-engineering/engineering-catalog.md`：原始 superpowers 15 个 skill 逐个交代去向——
  11 个整合为具名能力、1 个并入场景链并行算子（dispatching-parallel-agents）、
  3 个舍弃（using-superpowers 入口/诊断自检/写 skill 元能力，均给理由）。
- 具名能力各有输入输出契约（`brainstorm/plan/execute/tdd/debug/review/receive-review/verify`；当前全表见 `../02-engineering/engineering-catalog.md`）。
- 重写 ../../../conductor-router/references/scenarios.md：13 场景全部写成显式**工程能力链** + 契约传递；
  纯只读场景（9/10/12）明确"能力链：无"。
- 效果：回答了"superpowers 的 skill 去哪了"和"怎么按它的流程工作"——场景链即答案。

## 二·终3、补齐 git 相关纪律（🟢 已激活 2026-11-19）

- 背景：用户指出遗漏 git 提交相关 skill。核查：superpowers 无独立 "git commit" skill，
  但 git 纪律散落在上游的隔离与分支收尾两个 skill 里，
  上一轮整合时压成了一句话，丢失了全部防呆细节。
- 补进 `../../../conductor-brainstorm/references/engineering-workflow.md`（2026-11-21 已改名为 brainstorm-plan.md，隔离/分支收尾内容后经决策移除）：
  - 隔离工作区详解——检测已有隔离(含 submodule 陷阱)、原生工具优先、
    gitignore 先验并提交、目录优先级、沙箱 fallback、征求同意。
  - 分支收尾详解——验当前树测试、探环境三态、确认 base branch、精确菜单、
    discard 需输入确认、禁擅自 force-push、清理所有权判断、6 条 git 红线。

## 二·终4、新增 git 提交规则（🟢 已激活 2026-11-19）

- 新增 `../04-guards/git-commit-rules.md`：提交时机（TDD 绿后/任务完成/收尾前）、Conventional Commits + 中文格式、
  暂存纪律（禁 `git add -A` 盲加、只 add 本次文件、两步核对 status/diff --cached、破坏性改动警惕）、
  8 条红线、提交前检查清单、提交后核对 HEAD。
- SKILL.md 挂载：S3/S5 阶段加载；强制机制从三道锁扩为四道锁（新增锁 4 提交前门禁）。
- 动机：项目反复出现"工作区混入其他会话改动"，此前提交靠人工小心，现固化为规则。

## 二·终5、样例归纳补全规则（🟢 已激活 2026-11-19）

- 背景：用户举例设计功能时，AI 只做列举项、不补未列举同类；改文档/代码时只改明说那处、不改关联处。
- 新增 `../../../conductor-brainstorm/references/examples-to-spec.md`：核心认知"用户举例 ≠ 完整需求"；触发信号（比如/例如/参考 X 那样/改这里但同类位置）；
  四步法（归纳意图→按 6 维度外推→分类呈现先确认→落地核对）；三类场景侧重（设计/文档关联项/代码关联项+异常）。
- 关键平衡：补全 ≠ 擅自扩大——同类项可补并记录依据，判断项先问用户；禁止只做列举项、禁止假补全。
- SKILL.md 挂 S1 识别/S2 补全/S3 关联核/S4 核对；scenarios 通用前置+设计/文档/开发场景+缺口台账第 7 项。

## 二·终6、补全提取细节 + references 索引（🟢 已激活 2026-11-19）

- 背景：用户质疑压成能力后丢失细节是否影响功能。逐条对比原文（原始 11 skill ~4400 行 vs 提取 245 行，压 95%）。
- 修正上一轮误判：subagent-driven 不是"废了"（通用 agent 会派子代理），而是缺三条护栏；
  brainstorming 真正致命的是"先调查再开口/别问已回答的"，不是 Red Flags。
- 补进细节（不简化、对照原文）：
  - ../../../conductor-tdd/references/engineering-tdd.md：Verify RED（fail vs error）/Verify GREEN（跑全项目套件，漏报即失真）/
    5 条最狠借口/红旗清单
  - ../../../conductor-brainstorm/references/engineering-workflow.md（现 brainstorm-plan.md）：brainstorm 先调查再开口+首条消息+回述+两条红旗；
    writing-plans 的 Interfaces(Consumes/Produces)+计划头+Self-Review 五问
  - ../../../conductor-review/references/engineering-code-review.md：subagent 派单契约(brief 唯一需求源/记 BASE/不许自派 reviewer/
    显式选 model)+fix-loop+完成台账+借口表
- 整理 references：新增 references/05-meta/README.md 索引（25 份按五类导航、加载优先级、冲突规则）；
  来源致谢里的上游文件名加限定词避免误当本地引用；SKILL.md 挂索引指针。

### review_gate.py 机器强制独立 review（🟢 已激活 2026-11-19）
- 背景：独立 review 门禁虽写入 SKILL.md，但仍是纪律门禁靠自觉；用户多次观察到 AI 跳过步骤。
- 方案：新增 `scripts/review_gate.py --overview <path>`，机器校验 overview 的「独立 review 结果」章节 + Blocker 清零结论 + 报告路径引用 + 报告文件真实存在（防假证据）；非改码场景 `--waived` 显式豁免。退出码非 0 禁止收尾。
- 已写入：`SKILL.md`（脚本清单/S5/独立review门禁小节/铁律8）、`../01-routing/skill-matrix.md`（脚本表）、`../../../conductor-router/references/scenarios.md`（门禁总述）。5 组测试覆盖（无章节/无结论/报告不存在/完整/豁免）全通过。

### overview 分层加载（🟢 已激活 2026-11-19）
- 背景：实际 overview 半天从 91 行涨到 183 行 / 21.7KB，全量加载浪费 token；规范要求"引用不复制"却未执行，完整 review 报告被抄进主文件。
- 方案：overview 分 L0 索引卡（≤12 行：场景/闸门/产物/未完成项/下一步）+ L1 摘要 + L2 详情引用；>30 行详情独立成 `.xxx.md`。S0 续接先只读 L0，按需读 L1/L2，禁止全量。
- 已写入：`../../../conductor-memory/references/overview.md`（模板+加载协议+纪律第6条 L0 必填）、`SKILL.md`（S0 加载协议 + 会话记录节）。

### 五项新能力 + SKILL.md 瘦身（🟢 已激活 2026-11-20）
- 起因：用户反馈每次加载 conductor 消耗大量 token（SKILL.md 20KB 每次必读），且缺变更影响分析/技术债台账/接口迁移守卫/发布编排/缺陷复现入口。
- 形态决策：全部做成**脚本 + reference 内化**，不新建独立 skill——脚本按需执行、reference 按需加载，都不占每次常驻 token，符合"唯一主控 + 项目自包含"。
- 新增能力：
  - `scripts/impact_analysis.py`：符号/文件/diff → 引用者 + 建议测试草稿（场景 5/7，S1 影响面）。
  - `scripts/debt_ledger.py` + `../../../conductor-ledger/references/tech-debt-ledger.md`：技术债标记扫描 + 债指数量化 + 台账字段（S4/S5，进 overview 未完成项）。原 P2「技术债治理」在此落地。
  - `../../../conductor-impact/references/contract-migration.md`：接口契约四同步 + DB 迁移可逆性/锁表/兼容清单（场景 6/12，S2/S4）。
  - `../04-guards/release-checklist.md` + `scripts/release_notes.py`：版本/CHANGELOG/tag/回滚清单 + conventional commits 生成草稿（场景 12/S5）。
  - `../../../conductor-debug/references/engineering-debugging.md` 增强「最小复现构造」章节（场景 8）——原 P2 未列，因与已有 debugging skill 重复，选择增强而非新建。
- 独立 review 完整规则从 SKILL.md 下沉到 `../../../conductor-review/references/independent-review.md`，SKILL.md 锁5/铁律8 只留指针。
- **SKILL.md 瘦身**：20,002 → 11,539 字节（-42%），201 → 115 行；铁律8条/13场景/门禁机制/全部 reference 指针保留，解释性文字（起因/根因/分工细节）下沉到 reference。
- 挂载同步：README 索引（26→30 份，D 类 6→10）、skill-matrix（阶段矩阵+脚本表）、scenarios（场景 5/6/8/12 + 门禁指针 + 缺口台账法）、overview 模板（技术债字段）。

### 新增场景14 + 时序推导（🟢 已激活 2026-11-20）
- 起因：用户反馈两类问题——① 删文档/改无关文档这类操作在13场景里无归属（场景11是"文档对齐代码"，语义不同），被判"以上都不匹配"；② 场景链按字面顺序建链，导致"删除M6文档，根据M6文档改代码"会先删后改（删了就没法读），且漏掉"先通读M6"这个隐含步骤。
- 新增场景14「文档/资源清理」：删除/归档/移动/改无关文档；走文档·清理变体路径（S1→确认无消费者依赖→执行→写overview→结束），无代码改动不跑 TDD/verify/独立review。时序纪律：在场景链中销毁排最后，闸门=消费者节点已完成且验证通过。
- **时序推导规则**（routing §3.5，核心）：链的执行顺序看依赖不看字面顺序——生产者先于消费者（"根据X做Y"隐含"先理解X"要补出来）、销毁操作最后、改码必带验证、闸门内联、字面与依赖冲突按依赖重排并向用户说明。用用户 M6 例子做示范。
- 语义三问扩产出物（删除/归档状态）与对象（资源存在性→14）；意图锚点表加场景14；消歧加第8/9条（清理vs同步、销毁位置）。
- 路径 4→5（新增文档·清理变体）；场景 13→14；同步 router-prompt（自包含提示词加时序规则+场景14，管线编号4→5顺延）、SKILL.md 场景表+矩阵、scenarios I/O契约+详情、README、roadmap 计数。
- 挂载同步：engineering-catalog（13→14）、meta README（13→14）、roadmap 抬头（十四场景+五路径）。

### overview 会话指针锚定（🟢 已激活 2026-11-20）
- 起因：用户反馈 overview 每轮对话一个导致文档爆炸；先加了语义判定（记什么/不记什么、一会话一文档），但语义判定是软约束不可靠。用户要求"用会话 ID 做文件名 hash，同会话不同对话按规则找文件"。
- 关键决策：**不用任何厂商环境变量**（`CODEBUDDY_SESSION_ID` 等各家不统一，无跨 agent 通用 key）。用户拍板用**会话指针文件** `.conductor-session.json` 自维护会话 UUID——零外部依赖、所有 agent 都能读写文件、支持跨天、边界用户显式控制。
- 新增 `scripts/overview_path.py`：S0 跑它定位 overview——读指针 UUID 取前 8 位 hash 做文件名前缀，同会话多轮归同一文件（与主题无关）；`--new-session` 开新会话、`--end-session` 结束、`--detect-only` 看状态。会话 ID 用 Python 标准库 uuid4，无外部依赖。
- 挂载：SKILL.md（触发后第一步+S0阶段+会话记录节）、overview.md（新建vs追加段重写为指针机制）、scenarios 通用前置、skill-matrix（阶段表+脚本表）、README（脚本数 8→9）。
- 注：`.conductor-session.json` 是本地会话状态，建议加入项目 .gitignore（非项目资产）。

### 环境依赖功能不砍 + 真实测试入口（🟢 已激活 2026-11-20）
- 起因：用户反馈——没开 Docker 时 AI 把只能在真实环境验证的功能直接砍掉不写；开了 Docker 叫它跑真实测试，它仍复用原 mock 命令。核心是"实现功能"与"验证功能"被混淆。
- 核心规则（`../../../conductor-impact/references/architecture-contracts.md` §4.5）：**无真实环境 ≠ 砍功能**——依赖 Docker/DB/Redis 的功能照常写生产 adapter，只在真实环境能验证的部分登记「待真实环境验证」未完成项；禁止"环境不支持所以不做"和"只写 fake 标完成"两错误出口。用户要真实测试时跑真实入口（`tests/integration/`），不是复用 mock 命令；若发现功能被砍先补实现。
- 新增 `scripts/env_probe.py`：探测 docker daemon / compose 文件 / 集成测试目录 / DB-Redis 依赖信号，输出 needs_real_env + recommended_real_test_cmd，供 S0 写 overview 环境节、用户要真实测试时给入口。故意不纳入 httpx/requests（外部 API 适配器有正常默认实现，纳入会误报）。
- 挂载：SKILL.md（S0/S2/S4 阶段 + 脚本清单 + 铁律第8条）、scenarios 通用前置 2b、skill-matrix（S0+脚本表）、test-strategy §5.5、README（脚本9→10+特性行）。
- 断点模式清单加「环境缺失砍功能」（对照设计规格查生产代码是否仍有真实实现）。

### 迁移完整性守卫 · 场景7 防漏/防断点（🟢 已激活 2026-11-21）
- 起因：用户提问"主线已定后，怎么保证迁移中 AI 不漏模块、功能无遗漏和断点"。核心认知：风险不在方向，在边角没被枚举出来；AI 上下文会丢会压缩，靠记忆必漏。需把记忆外置成机器可校验的台账。
- 形态决策：沿用"脚本 + reference 内化"，不新建独立 skill（符合唯一主控 + 项目自包含）。
- 新增 `scripts/migration_ledger.py`：三子命令——`init` 扫码建台账（清单来自代码非印象，kind 区分 entry/route/module/config，deps 弱信号仅供排序）、`next` 按依赖层序输出下一批（中断项优先=断点续接）、`check --strict` 收尾门禁（pending/in_progress/verified 无有效证据/skipped 无理由/drift 漏登记一律 FAIL）。证据支持 `report:` 路径并校验文件真实存在（防假完成，同 review_gate 哲学）。
- 新增 `../../../conductor-ledger/references/migration-integrity.md`：五步法（盘点→行为基线→逐块迁移+差分→闸门→断点）+ 台账状态机 + 会话级约束提示词 + 完成判定。
- 挂载：SKILL.md（场景表第7行/S1建台账/S4收口门禁/脚本清单/铁律第9条）、scenarios（场景7 能力链重写+I/O契约+缺口台账命令）、skill-matrix（S1/S4+脚本表）、05-meta README（索引+计数 30→31、D类 10→11）。
- 测试：依赖层序（repo→service→main）、假证据拦截、report 文件存在校验、drift 检测、`init --merge` 保留已迁状态且新模块进 pending——全通过。
- 台账文件 `.migration-ledger.json` 是项目本地状态，建议加入 .gitignore。

### 承诺台账收敛 · 全场景防漏（🟢 已激活 2026-11-21）
- 起因：用户问"所有场景怎么避免 AI 漏东西"。核心认知：漏东西的本质跨场景相同——隐含承诺没被逐条勾销。不在 14 场景逐个打补丁，改在 S0/S4/S5 三个公共节点建横切防线（加新场景自动继承）。
- 形态决策：把上一轮的场景7专用台账**泛化为全场景引擎**，不新建第二套。
- 新增 `scripts/commitment_ledger.py`：统一引擎（存储/状态机/门禁/断点）+ 多来源采集器（--from-modules 源码扫描 / --from-list 文档列表项 / --from-json / --stdin 供 impact_analysis 与 review 输出灌入 / --manual）；四子命令 init/next/check/show。防膨胀三纪律内化：机器扫优先、门禁只卡三个出口、skipped+reason 豁免留痕。
- `scripts/migration_ledger.py` 降级为兼容 shim（固定 source=module，底层委托统一引擎），既有场景7文档与调用不破。
- 新增 `../../../conductor-ledger/references/commitment-ledger.md`（通用框架：五类根因→三道防线→场景适配表→防膨胀→收敛后分工）；`../../../conductor-ledger/references/migration-integrity.md` 降级为场景7特化指针（先读通用文档）。
- 挂载：SKILL.md（全场景横切行 + S0 采集/S4 核证据/S5 零未勾销 + 脚本清单 + 铁律9泛化）、scenarios（通用前置 5b + 缺口台账命令 + 场景7工具指针）、skill-matrix（S0/S4/S5 + 脚本表 11→12）、05-meta README（索引 + 计数 31→32、D类 11→12）、routing/router-prompt（场景7 迁移信号已在上一轮加）。
- 测试：通用台账多来源采集、stdin 灌入、增量合并保留已迁状态+新项进 pending、假证据拦截、drift、check --strict、shim 兼容（PASS/FAIL 各路径）全通过。
- 收敛后分工：commitment_ledger=引擎；migration_ledger=场景7 shim；examples-to-spec/impact_analysis/scan_gaps=提取器；contract-migration/architecture-contracts/independent-review=换眼验证；test-strategy/verify.py=证据来源。

### 源码纯净门禁 · fake 实现与动态类型（🟢 已激活 2026-11-21）
- 起因：用户反馈两个反复出现的问题——① 无真实环境（如 pgsql 连不上）时 AI 在 src/ 写 InMemoryStore 内存版冒充生产 adapter，污染源码；② 大量用 Any/object/dict[str, object] 不具体类型。
- 诊断：规则文本其实完备（architecture-contracts §4.5 / test-strategy §2,§5.5 / coding-rules-common §1），但全是软约束——verify.py 只跑 linter（多数项目没配严格规则，Any 不报错）、scan_gaps 只认 Fake/Stub/Mock 前缀（换名 InMemory/内存版就绕过）。缺专门的源码模式扫描门禁。
- 新增 `scripts/source_purity.py`：扫生产源码（自动排除 tests/）两类污染——fake_impl（类名/变量声明/意图注释/文件名含 InMemory/Memory/Fake/Stub/内存版/测试用/待换真实实现等）与 dynamic_type（按语言的 Any/object/interface{}/dynamic/Object）。三粒度留痕豁免（行内/块级/文件级 purity-exempt，理由≥4字符）。默认恒 0，--strict 有未豁免命中即 1。支持 --format json / --lang / --allow-pattern。
- 新增 `../04-guards/source-purity.md`：规则正文 + 正确做法（无环境时照真实基础设施写生产 adapter、fake 只在 tests/、待真实环境验证登记）+ 类型具名别名方案 + 豁免纪律 + 完成判定。
- 挂载：SKILL.md（锁3 + S4 + 脚本清单 + 铁律8 + references 32→33）、test-strategy §2、architecture-contracts §4.5、coding-rules-common §1（均加机器门禁指针）、skill-matrix（脚本表 + S3/S4）、05-meta README（索引 + 计数 32→33、D类 12→13）。
- 测试：内存实现/Any/dict[str,object]/意图注释全命中、tests/ 排除、行内/块级/文件级豁免、空理由(<4字符)不生效、strict PASS/FAIL 路径全通过。
- 定位：与 verify.py（格式化/类型/覆盖率）、commitment_ledger（零未勾销）、review_gate（独立review）叠加，互不替代。

### 源码纯净 v2 · 数据驱动规则库 + 存量基线（🟢 已激活 2026-11-21）
- 起因：用户指出三个缺口——① 不具体类型不止 Any/object/dict[str,object]（还有 Callable[...,Any]、裸容器、unknown、Function、Object[] 等多形状）；② 不止 Python 其他语言也有；③ **重构时老代码本就有这些，AI 不会处理**（不能要求全仓清零，否则违反禁扩大 diff）。
- 重写 `scripts/source_purity.py`：
  - 数据驱动规则库——27 条内置 Rule（id/category/lang/pattern/desc/severity），error 卡门禁 / warn 只提示；覆盖 fake 信号 + 多语言不具体类型多形状（Python 6 条、TS 4 条、Go 3 条、Rust/Dart/Java/Kotlin/C#/Ruby/PHP）；`--rules custom.json` 追加、`--disable-rule` 禁用、`rules` 子命令列出。
  - 子命令化 scan/baseline/check/rules（无子命令兼容旧调用）。
  - **存量基线**：`baseline` 写 `.purity-baseline.json`（指纹=文件:行号:规则id 的 hash）；`check --baseline` 只卡新增、存量单列 TODO；`--scope <changed.txt>` 让改到的文件的存量升级为需负责（改哪负责哪）——解决重构场景存量处理与禁扩大 diff 的矛盾。
- `source-purity.md` 重写：规则库表 + 基线工作流 + 三情形正确做法 + 留痕豁免 + 完成判定。
- 挂载：SKILL.md（锁3/S4/脚本清单/铁律8）、scenarios 场景7加⑥存量基线、skill-matrix（脚本表+S4）。
- 测试：27规则加载、多形状命中、多语言、自定义规则、旧调用兼容、基线三态（纯存量PASS/新增FAIL/scope升级FAIL）、无基线全新增FAIL——全通过。
- 关键决策：门禁在重构场景不能要求全仓清零——用基线把"存量"与"新增/本次改动"分开，符合"改哪负责哪"+禁扩大 diff。

### 源码纯净 v2.1 · 意图空白（无注释占位 / 未用参数）（🟢 已激活 2026-11-21）
- 起因：用户指出两类"信息缺失"——① 分模块开发时，本模块功能依赖其他未开发模块，写了占位但没注释依赖谁/谁补，AI 误读为"功能没做"；② 函数参数声明了没用、又没注释给谁用/其他模块是否要传，信息为零。
- 认知：占位与未用参数**本身合法**（跨模块依赖/接口对齐/回调签名），缺的是**意图信息**，不是代码。判定核心=有信号+无解释注释+无豁免。
- 新增 `scripts/intent_gaps.py`：函数级语义扫描（Python AST 精确）。两规则——`unexplained_placeholder`（pass/.../NotImplementedError/空return 且无意图注释）、`unused_param`（参数声明未用且无说明）。合法豁免：意图注释（依赖/待接入/由…实现/预留/接口约定）、abstractmethod/overload/Protocol、_前缀/self/cls、docstring 点名、purity-exempt。v1 只精支持 Python，其他语言靠 lint/人工（文档明示不假装覆盖）。
- 集成：`source_purity.py scan/check` 默认自动合并 intent_gaps（Hit 结构兼容，共用存量基线/豁免），`--no-intent` 可关；intent_gaps 缺失/报错静默跳过不中断主门禁。
- 挂载：SKILL.md（脚本清单+铁律8）、skill-matrix（脚本表）、source-purity.md（新增 §二·补 意图空白 + 完成判定），无新 reference 文档。
- 测试：无注释占位命中、有依赖注释跳过、未用参数命中、abstract/_前缀/docstring 豁免、集成合并、--no-intent、strict 全通过。
- 关键决策：行级模式（正则）与函数级语义（AST）分脚本、统一门禁——职责清晰且存量基线/豁免机制复用。

### 成本档位 · lite / standard / full（🟢 已激活 2026-11-21）
- 起因：用户反馈"一次运行最低四五十积分就没了"。诊断：入口 SKILL.md 9834 字符每轮全量注入；S0 强制 handoff/env_probe/承诺台账；S5 强制全新上下文独立 review 子代理——小改动跑全套是结构性空转，不是某一条规则写错。
- 形态决策：不删门禁，改为**按风险判档**——低风险小改动走 lite，高风险仍走 full；省掉的每一步必须在路由声明列出来，可纠正、可审计。
- 新增 `../../../conductor-router/references/cost-tiers.md`：三档判定条件（规模/接口/清单/环境/设计/用户要求/置信度）、逐节点裁剪表、不可裁底线、lite 一行式声明、三问轻量复核与升档规则。
- `review_gate.py` 加 `--lite`：校验 overview 的「轻量复核（lite）」章节（档位标记 + Blocker 清零 + ≥3 条复核项 + ≥2 条行号/退出码证据），与 `--waived` 互斥，防"省成本"变"省门禁"。
- 入口瘦身：SKILL.md 9834 → 3668 字符（-63%），场景表压缩、阶段矩阵改为要点、脚本清单收为一行；细节全部下沉到既有 reference，铁律与五道锁保留但合并为短句。
- 挂载：SKILL.md（成本档位表 + S0–S5 按档裁剪 + 锁5 + 参考计数 33→34）、routing.md（§2.3 判档顺序 + 决策/声明模板加档位与"省掉"）、router-prompt.md（档位字段 + 管线 3.5）、scenarios.md（顶层裁切说明 + 通用前置 2b/3/5b 条件化 + review 门禁 lite 例外）、independent-review.md（档位裁切引言）、skill-matrix.md（矩阵裁剪说明 + review_gate --lite）、05-meta README（A 类 5→6、总数 33→34）、根 README。
- 测试：`review_gate.py --lite` 的 PASS/FAIL（缺章节/缺档位/未清零/复核项不足/证据不足/与 --waived 冲突）全通过；原默认门禁与 `--waived` 路径保持兼容。
- 关键决策：省的是**重复声明、全量工程文档、无关扫描、外部 skill 与独立子代理**；不省规格确认、TDD、verify.py 证据、source_purity 门禁、review 门禁与 overview L0。lite 一旦越界立即升档，不能用补跑糊弄。

### 器官化重构 · 机体—器官—环境（🟢 已激活 2026-11-21）
- 起因：用户指出三件事——① 两个状态文件内容有问题且耗 token；② overview 每次生成/读取太多；③ 想按 superpowers 那样把能力拆成 skill，"conductor 是生物、其他 skill 是器官、场景是工作环境"，并质疑协作 skill 从未被真实验证。
- 形态决策：conductor 降级为机体（状态机+门禁+决策权），新增 `skills/conductor-*`（与 conductor 同级） 下 10 个器官 skill（router/brainstorm/spec/tdd/review/learn/ledger/overview/impact/debug），每个只写 I/O、加载时机、降级；14 场景成为环境（只声明器官链）。`references/` 明确为"共享组织"，不是第二个大脑。
- 新增 `../01-routing/organ-registry.md` 作为器官总线：8 器官映射、阶段调用表、废弃 skill 清单、状态文件纪律、测试入口。SKILL.md 重写为 3023 字符，器官各 685–979 字符。
- 状态瘦身：`overview_path.py` 指针改为 `{"sid":"8位短hash"}`，兼容旧 session_id，`--end-session` 直接删文件，首次生成自动追加 4 个本地状态文件到 `.gitignore`；`commitment_ledger.py` 紧凑 JSON（省略空字段/重复 id/pending 默认），40 条示例 9060→1755 字符（-81%），`show/check` 完全兼容。
- overview 两-tier：主文件只留 L0（≤8 行）+ review 章节，环境/L1/决策/证据/变更清单进 `.details.md`；`../../../conductor-memory/references/overview.md` 模板从 10.8k 压到约 3k 字符；`find_existing` 排除 `.details.md`。
- 协作 skill 裁剪：`metago-code-review-deep` 删营销/FAQ/重复分级表，只留五维+四级报告；`graphify` 删协议/license/竞品/FAQ 尾部（9370→5514 字符）；`grill-me` / `ponytail-review` / `caveman-compress` 标 DEPRECATED 并移出加载矩阵（不物理删除）；`ponytail` 明确不覆盖流程决策。
- 测试补位：新增 `scripts/organ_contract_test.py` 与 `preflight.py --verify-organs`，验证器官接线、契约、降级路径、状态文件压缩与两-tier 模板；明确**不替代真实 LLM 会话效果评估**，后者用场景冒烟清单人工复核。
- 关键决策：拆分的是"能力加载权"，不是"决策权"——器官给结论和证据，放行永远在 conductor；废弃 skill 只标记不删除，避免破坏既有安装；状态文件压缩但保留机器门禁可解析性。

### 器官化二次收敛 · 测试后筛选 + 文件真拆分（🟢 已激活 2026-11-21）
- 用户追加要求：先测试筛选协作 skill，留下的改名并入器官；conductor 文件真拆到器官；每个器官可独立工作；做完测效果。
- 新增 `scripts/collaboration_skill_audit.py`：按"被调用+3 / 产出门禁证据+3 / 与器官重复-2 / 超体积-1"打分。结果：grill-design / code-quality-review / handoff = 6 → 改名并入 `conductor-brainstorm` / `conductor-review` / `conductor-memory`（原 conductor-overview，后与 learn 合并更名）；graphify / ponytail = 3，caveman 等 ≤1 → 全部废弃留桩。
- 真拆分：conductor/references 下 routing/cost-tiers/router-prompt/scenarios、workflow/tdd/coding-rules、independent-review/code-review/security、commitment/migration/debt、overview、architecture/contract-migration、debugging 等复制到各器官 references/，conductor 原路径改成一行兼容指针；verify/review_gate/commitment_ledger/migration_ledger/overview_path/impact_analysis 复制到器官 scripts/，器官自包含。
- 修复器官脚本跨目录依赖：ledger 自带 overview_path 副本；tdd 的 verify.py 改用器官内扁平 references 路径。
- 测试：`organ_contract_test.py` 27/27 PASS（8 器官契约+自包含+3 个改名并入文件+注册表+状态文件）；新增 `organ_effect_test.py` 8/8 PASS（方法器官步骤断言；overview/ledger/review/impact/tdd 真实输入→输出冒烟）；preflight --verify-organs PASS。contract/effect 测试都不替代真实 LLM 会话评估。
- 关键决策：筛选用可复跑脚本而非印象；器官独立=自带方法+脚本+可单独出证据，放行权仍在 conductor。
- **最终修正（用户指出"没删除无关东西"）**：上面"留桩/兼容指针"方案作废。已物理删除全部 10 个原协作 skill 目录（项目+全局）——其中 grill-design/code-quality-review/handoff 的方法已并入器官，其余 7 个判定废弃；同时删除 conductor 内所有"已拆分"兼容指针文件，conductor/references 只剩 8 份机体文档；所有旧路径引用已改写为器官相对路径并校验 0 断链。历史条目保留原貌，以本条为准。

## 三、P2 候选（🟡，有真实需求再加）

- 安全审计（只读，加载 `../../../conductor-review/references/security-redlines.md`）
- ~~技术债治理~~（🟢 已落地，见上「五项新能力」）
- 依赖升级 / 迁移（运行时/框架升级 + 废弃 API 排查）—— 部分由 `../../../conductor-impact/references/contract-migration.md` 覆盖
- 独立 code review（只要分级清单，不进修复——已有 code-quality-review + metago）
- 会话续接（读 handoff + overview 恢复上下文）
- 原型 / POC（明确标记丢弃 or 转正式，禁止混入生产）
- ~~`knowledge-graph-rebuilder`~~（用户已明确放弃，不要复活）

## 四、激活原则

新增场景前先判：它走哪条路径？现有三机制是否够用？若不够，先补流程机制再加场景——
否则新场景会在 S3/S4 卡死或空跑（这是方案 A 的教训）。

## 五、2026-11-21 第三轮：脚本分流 + conductor-sync 器官 + subagent 泛化

- 背景：用户指出 conductor 本体脚本"很多和 conductor 关系不大"；统一安装/更新应独立成 skill；subagent 不应限于改码。
- **脚本分流**（本体只留 preflight/env_probe + 6 shim）：
  - `scan_gaps.py` / `source_purity.py` / `intent_gaps.py` → `conductor-review/scripts/`（代码审查机器证据归 review；04-guards/source-purity.md 一并迁入）
  - `debt_ledger.py` → `conductor-ledger/scripts/`；`release_notes.py` + release-checklist.md → `conductor-git/`
  - 04-guards 目录清空删除；conductor 本体 scripts 只剩 2 个本体脚本 + 6 个薄 shim
- **新增 `conductor-sync`（第 13 器官）**：统一安装/更新 conductor 家族到全局目录（sync-global.py 默认同步 conductor+conductor-*）+ 完整性三测试（organ_contract / organ_effect / script_parity）+ collaboration_skill_audit 迁入；SKILL.md + references/install-verify.md。
- **subagent 泛化**：不限改码——任何可拆成独立/自包含/可验证单元的多代理场景（调研/分析/文档/审查）都按判据派发；brief 模板分改码/非改码两类；复核分改码两段评审与非码两查。conductor 侧 registry/matrix/catalog/cost-tiers/scenarios 同步改写。
- 测试基线：organ_contract 39/39（含 conductor-sync 契约）、organ_effect 15/15（含 install-verify 方法断言）、script_parity 18/18（SHIM_DIR 修正为 conductor 本体）。

## 六、2026-11-21 第四轮：器官合并 13→11，release 定位扩为版本动作

- 背景：用户问 release 是否单独成 skill，担心器官过多；确认合并方向并给合并后的 skill 改名。
- **release 去向**：不单独成 skill，留在 conductor-git；其职责定位从"git 操作器官"扩为"**版本动作器官**"（提交 + 发版：版本/CHANGELOG/tag/回滚）。release-checklist.md + release_notes.py 上一轮已迁入，本轮仅更新定位描述。
- **spec 并入 brainstorm**（名称保持 `conductor-brainstorm`）：同属 S2，澄清输出即规格输入，流水线相邻；change-contract-template / spec-method / contract_check.py 随迁；lite 档本就跳过契约固化，条件加载不变。
- **overview + learn 合并为新器官 `conductor-memory`**：短期记忆（两-tier 会话记录）+ 长期记忆（经验沉淀回写），输入输出直接衔接、lite 档同进退；overview_path.py / learn_capture.py 双脚本齐备。
- **不合并**：impact✗review（S1 规划 vs S5 验收）、debug✗tdd（场景 8 可纯诊断）、router/ledger/subagent/sync（枢纽/横贯/横切/基础设施）。
- 同步更新：organ-registry（11 器官）、skill-matrix、05-meta/README、conductor SKILL.md 场景链、router scenarios/cost-tiers、preflight ORGAN_SKILLS、三测试脚本（ORGANS/effect 断言/parity 映射）、overview_path shim 指向 conductor-memory、根 README。
- 测试基线：organ_contract 39/39、organ_effect 16/16、script_parity 18/18。
