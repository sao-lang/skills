# 承诺台账 · 全场景防漏守卫（横切防线）

> 用途：在**所有场景**里防止 AI 漏东西——漏模块、漏需求、漏调用方、漏症状、漏差异、漏 finding。
> 定位：横切 S0/S4/S5 三个公共节点，不写进单个场景；凡有"隐含待办清单"的场景都适用。
> 核心认知：**漏东西的本质是同一个**——输入里隐含的承诺没被逐条勾销。AI 的上下文会丢会压缩，
> 靠"记住还有哪些"必然漏。解法是把记忆外置成机器可校验的台账，判定权交给机器。

## 一、为什么是所有场景，不是逐个场景打补丁

不同场景的"承诺"长得不一样，但结构相同：

| 场景 | 隐含的承诺是什么 | 采集来源（机器优先） |
|---|---|---|
| 4 项目开发 | 规格每条需求（含边界/异常） | 设计规格的列表项 → `--from-list` |
| 5 项目迭代 | 变更要求 + 每个受影响调用方 | 变更点 → `impact_analysis.py` 输出 → `--stdin` |
| 6 设计驱动重构 | 设计差异清单逐条 | 差异清单 → `--from-list` |
| 7 项目重构 | 每个模块行为等价 | 源码扫描 → `--from-modules`（用 `migration_ledger.py` shim） |
| 8 解 bug | 复现 + 根因 + 每个回归 | 症状清单 → `--from-list` |
| 11 文档/注释同步 | 每处文档-代码差异 | diff/差异清单 → `--stdin` 或 `--from-list` |
| 9/12 审查/门禁 | 每个 finding / 门禁项 | review 清单 → `--stdin` |

**共性**：都是"一份清单要逐条勾销"。所以只需一套机制，挂在所有场景必经的三个阶段节点上——
加新场景自动继承，不漏装。这就是"所有场景"的答案：**在阶段层做，不在场景层做**。

## 二、五类根因 → 三道横切防线

AI 漏东西有五类根因，三道防线分别覆盖：

| 防线 | 挂在哪个公共节点 | 覆盖的根因 | 机制 |
|---|---|---|---|
| **① 外置事实** | S0 会话开始 | 记不住 / 看不见 | 读完输入就采集承诺进台账；清单来自机器扫描/已有文档，不靠 AI 复述 |
| **② 证据判定** | S4 自省补强 | 想当然 / 自查盲 | 每条待办标 verified 必须挂证据（命令+退出码 / 文件:行号 / report: 路径）；拿不出=没完成 |
| **③ 换眼验证** | S5 交付前 | 查不出 / 自查盲 | 独立 review（全新上下文）+ 运行时验证（契约/集成/差分），专打静态盲区 |

台账主要解决①②；③由既有 `independent-review.md`（独立 review 门禁）与
`architecture-contracts.md`（接线四问）承担，两者叠加而非互相替代。**静态盲区
（反射/字符串引用/跨进程契约/副作用）单靠台账抓不到，必须靠③的运行时验证**。

## 三、台账怎么用（三步闭环）

### 1. S0 采集——机器能扫的自动扫，人只填语义
```bash
# 开发/重构：从设计规格列表提取承诺
python ../scripts/commitment_ledger.py init --ledger .commitment-ledger.json \
  --from-list docs/spec.md --list-source spec --project "<任务>"
# 迭代/解bug：把影响分析 / review / 差异清单的输出灌进来
python ../../conductor-impact/scripts/impact_analysis.py --symbols Foo | \
  python ../scripts/commitment_ledger.py init --ledger .commitment-ledger.json --stdin --stdin-source impact
# 场景7 重构：用兼容 shim（底层同一引擎）
python ../scripts/migration_ledger.py init --path src --merge
```
- **增量合并**：重跑 `init` 默认保留已填的 `status/evidence/reason/checkpoint`，只补新增项——
  这同时解决了"中途新增模块/需求被漏"（drift）和"重复劳动"。
- 采集来源可叠加（`--from-modules` + `--from-list` + `--stdin` + `--manual`），每条带 `source` 字段。

### 2. 执行中——一次一条，完成即勾销
每完成一条承诺，在台账里把 `status` 改：
```
pending ─开始─> in_progress ─验证通过─> verified（必须填 evidence）
   │                 │
   │                 └──中断─> in_progress + checkpoint（迁到哪/下一步/改了哪些文件）
   └──确认无需做─> skipped（必须填 reason）
```
- **禁止刷状态过闸门**：把 pending 直接改成 verified 但没有 evidence，`check` 会拦下。
- 换会话/换 agent：先 `next`（in_progress 断点项优先）定位续接点，不靠记忆。

### 3. S4/S5 闸门——零未勾销才放行
```bash
# 日常核对（恒 0，看缺口）
python ../scripts/commitment_ledger.py check --ledger .commitment-ledger.json --modules src
# 收尾门禁（有缺口即退出 1，禁止 finish / 标完成）
python ../scripts/commitment_ledger.py check --ledger .commitment-ledger.json --modules src --strict
```
`--strict` 失败条件（任一即 FAIL）：
1. 有 `pending`（未勾销承诺）；
2. 有 `in_progress`（中断未收口）；
3. `verified` 的 evidence 为空 / 无可核对线索 / `report:` 指向文件不存在（假完成）；
4. `skipped` 无 reason（不能静默跳过）；
5. drift——磁盘/来源里有、台账未登记的项（重跑 `init` 纳入）。

`check --modules src` 的 drift 只对 `source=module` 的条目生效；纯文档/规格任务不传 `--modules`。

## 四、防止防漏机制本身变成麻烦（硬纪律）

防漏机制如果太重，AI 会刷状态造假、人会嫌烦绕过，防线形同虚设。三条平衡原则：

1. **机器能扫的绝不让人填**。模块来自源码扫描，需求/finding 来自已有文档或脚本输出，
   AI 只补"这条需求隐含异常路径"这类语义判断。人填得越多越不可靠。
2. **门禁只卡三个出口**。S0 采集、S4 核证据、S5 放行——插在每一步会让人崩溃。
   日常用 `check`（恒 0）看缺口，只有收尾用 `--strict`。
3. **允许显式豁免但留痕**。`skipped + reason` 是合法出口，机器校验理由非空即可；
   这比"伪装成 verified"诚实得多。

## 五、与现有能力的关系（收敛后的分工）

| 能力 | 角色 | 与台账的关系 |
|---|---|---|
| `commitment_ledger.py` | 统一引擎（存储/状态机/门禁/断点） | 核心 |
| `migration_ledger.py` | 场景7 兼容 shim，固定 `source=module` | 底层委托给统一引擎 |
| `examples-to-spec.md` | 提取器：把用户举例补全为完整需求 | 补全结果应进 `--from-list`/`--manual` |
| `impact_analysis.py` | 提取器：变更影响面 | 输出经 `--stdin` 进台账 |
| `scan_gaps.py` / review 清单 | 提取器：缺口/finding | 输出经 `--stdin` 进台账 |
| `contract-migration.md` / `architecture-contracts.md` | 换眼验证：接线/契约静态盲区 | 与③叠加 |
| `independent-review.md` + `review_gate.py` | 换眼验证：独立审查门禁 | 与③叠加，Blocker 清零才 finish |
| `test-strategy.md` / `verify.py` | 证据来源：测试命令+退出码 | 填 evidence，只认 verify.py 输出 |

## 六、完成判定（拿证据才标完成）
- `check --strict` 退出 0（台账全勾销、无 drift）；
- 每条 verified 有可核对证据，写入 overview「验证结果」；
- 静态盲区经③的运行时/独立验证核对通过（行号/命令证据）；
- 独立 review 门禁 `review_gate.py` 通过（Blocker 清零）；
- 任一不满足 → 不得标完成、不得 finish。

> 台账文件 `.commitment-ledger.json` / `.migration-ledger.json` 是项目本地状态，建议加入 .gitignore。
