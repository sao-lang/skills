# 迁移完整性守卫 · 场景 7 特化

> **先读通用文档 `commitment-ledger.md`**——本文件只讲场景 7（重构/迁移）的特化差异，
> 通用机制（三道横切防线、台账状态机、证据校验、防膨胀纪律、完成判定）都在那边。
> 定位：按需加载——场景 7 项目重构全程读本文件 + 通用文档；其他场景只读通用文档。
> 核心认知（通用）：**漏东西的本质是隐含承诺没被逐条勾销**，解法是把记忆外置成机器可校验的台账。
> 本文件特化点：承诺=每个模块行为等价；采集用 `migration_ledger.py`（底层统一引擎的 shim，
> 固定 `source=module`）；证据以"变更前后行为等价 + 差分对跑"为主。

## 为什么需要它（针对的失败模式）

| 失败模式 | 根因 | 本守卫的对策 |
|---|---|---|
| 漏模块 | AI 凭印象列清单，上下文一压缩就忘 | 清单来自代码扫描，`migration_ledger.py init` 生成台账作为唯一事实源 |
| 迁移中新增模块被漏 | 边迁边加文件，没人回头对齐清单 | `init --merge` 增量合并 + `check` 查 drift（磁盘有、台账无） |
| 功能遗漏 | 只看代码结构，没锁住"现在的行为" | 迁移前 characterization test 锁等价性（见 §2） |
| 语义漂移 | 单测绿但新旧行为不一致（空值/乱序/时区/错误码） | 新旧差分对跑，逐字节比对（见 §3） |
| 断点丢失 | 会话中断/压缩后不知迁到哪 | `status=in_progress` + `checkpoint` 字段 + `next` 命令定位续接点 |
| AI 自说自话 | "我觉得迁完了"无证据 | `check --strict` 机器判定：pending/无证据/无理由一律失败 |

## 五步法（场景 7 的执行骨架）

### §0 前提：主线已定
本守卫只解决"沿着既定主线不漏不丢"，不负责方向选择。方向未定 → 先走场景 2/6（架构/设计），
别用本守卫硬跑。与场景 7 能力链的关系：`inventory → 基线 → 逐块迁移 → 闸门 → 断点` 内嵌在
`tdd → 改结构 → review → verify → 收尾` 中——基线即 TDD 的锁行为环节，闸门在 verify/S5。

### §1 盘点（inventory）—— 让清单来自代码，不来自印象
```bash
python ../scripts/migration_ledger.py init --path src --project "<迁移名>"
# 迁移过程中又新增/改名了模块 → 必须增量合并，否则新模块不在台账里 = 漏
python ../scripts/migration_ledger.py init --path src --merge
```
- 产出 `.migration-ledger.json`：每项 = `{id(相对路径), kind, deps, status, checkpoint, evidence, reason, note}`。
- `kind` 区分 entry/route/module/config——**入口与路由优先迁**（它们最容易被外层引用、断了就是功能断点）。
- `deps` 是 import 抽出的弱信号，**仅供排序参考，必须打开源码核对**，不当已验证事实。
- 台账是唯一事实源：会话压缩、换新 agent 都不影响；每轮开始先读台账，不靠记忆。

### §2 行为基线（baseline）—— 先记录"现在怎样"，再谈"应该怎样"
迁移前对老系统建立 characterization test（见 `test-strategy.md`）：
- 输入→输出快照（golden 文件）、API 契约（schema）、关键查询结果、UI 截图、端到端旅程日志。
- 有真实流量就录制脱敏后回放（最有效的功能清单）。
- **没有基线就没有"无遗漏"的判据**——基线测试必须能在新实现上跑，失败即红灯。
- 这些基线测试是 `evidence` 的主要来源；把命令+退出码写进台账对应项。

### §3 逐块迁移 + 差分对跑 —— 一次一块，新旧对拍
- 一次只迁一个模块（台账一项），输入输出契约先定死。
- 新老实现同时吃同一批输入，逐字节比对输出（差分测试）——抓单测覆盖不到的边角：
  空值、乱序、时区、错误码文案、并发边界。
- 配 feature flag / 影子流量做灰度，任何时刻能切回老实现。
- 每迁完一项：把该项 `status` 改 `verified`，`evidence` 填基线测试证据 / 差分报告路径
  （`report: path/to/diff.md`，文件须真实存在，`check` 会验证）。

### §4 闸门（gate）—— 判定权交给机器
```bash
# 日常核对（恒 0，看缺口）
python ../scripts/migration_ledger.py check --ledger .migration-ledger.json --path src
# 收尾门禁（有 pending/in_progress/无证据/skipped 无理由/drift → 退出 1，禁止收尾）
python ../scripts/migration_ledger.py check --ledger .migration-ledger.json --path src --strict
```
`check --strict` 的失败条件（任一即 FAIL）：
1. 有 `pending` 项（未迁移）；
2. 有 `in_progress` 项（迁移中断未收口）；
3. `verified` 项 evidence 为空 / 无可核对线索 / `report:` 指向的文件不存在（假完成）；
4. `skipped` 项无理由（不能静默跳过）；
5. drift：磁盘存在但台账未登记的模块（迁移中新增被漏）——重跑 `init --merge` 纳入。

机器判定之外，仍需人工核对（脚本只给草稿+信号）：
- **功能链路断点**：模块"接口就绪"是否真被装配层调用（`scan_gaps.py` install 无调用者是弱信号）。
- **端到端旅程**：每条关键用户旅程在新系统里走通，不只单模块能跑。
- **接口/DB 契约**：涉接口签名/DB 迁移加读 `contract-migration.md` 核四同步与可逆性。
- 以上证据写入 overview「验证结果」，与独立 review 门禁（`review_gate.py`）叠加，不互相替代。

### §5 断点续接 —— 任何时刻可停可续
```bash
# 会话中断/压缩后，先定位断点，不靠记忆
python ../scripts/migration_ledger.py next --ledger .migration-ledger.json --limit 5
```
- 中断时把当前项设为 `in_progress`，`checkpoint` 写清"迁到哪、下一步做什么、已改了哪些文件"。
- 换会话/换 agent：①读台账 ②`next` 取下一批（优先输出 in_progress 断点项）③只看那一个模块的源码。
- checkpoint 落在绿灯状态：每个闸门过了才往前走，不积累红灯。
- 回滚单位 = 一个模块 + 一个 feature flag，不做大爆炸切换。

## 台账状态机

```
pending ──开始迁移──> in_progress ──迁移+验证通过──> verified
   │                       │
   │                       └──中断──> in_progress + checkpoint（可续）
   └──确认无需迁移──> skipped（必须填 reason）
```
- `verified` 必须有 `evidence`；`skipped` 必须有 `reason`；`in_progress` 建议有 `checkpoint`。
- 状态只能由执行者据实更新，禁止为了过闸门把 pending 直接刷成 verified（evidence 会露馅）。

## 给 AI 的会话级约束（S1 种下，全程生效）
> 本项目走迁移/重构：唯一事实源是 `.migration-ledger.json`。每轮先 `next`/`check` 定位断点，
> 一次只处理台账一项，不动其他文件。完成后写 `status=verified` + `evidence`，
> 发现契约外行为先停下报告，不自行决定。收尾前 `check --strict` 必须退出 0。
> 清单来自代码不靠记忆，证据来自命令退出码不靠"我觉得"。

## 完成判定（拿证据才标完成）
- `check --strict` 退出 0（台账全收口、无 drift）；
- 基线测试 + 差分报告证据入 overview「验证结果」；
- 功能链路断点与端到端旅程人工核对通过（行号/命令证据）；
- 独立 review 门禁 `review_gate.py` 通过（Blocker 清零）；
- 任一不满足 → 不得标完成、不得收尾。
