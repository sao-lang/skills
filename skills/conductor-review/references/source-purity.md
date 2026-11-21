# 源码纯净守卫 · 数据驱动规则库 + 存量基线 + 意图空白

> 用途：拦住四类反复污染生产源码、让 AI 与后人误读的问题——
> ① 无真实环境时用内存/假实现冒充生产 adapter；② 不具体类型（各语言多形状）散落签名；
> ③ **跨模块占位无注释**（依赖谁/谁补/何时接入没写，AI 误读为"功能没做"）；
> ④ **参数声明了没用又没注释**（给谁用/其他模块是否要传/预留，一片空白）。
> 定位：S3 写码时按需加载；S4 自省跑门禁；**重构场景用存量基线，只负责改到的文件**。
> 与 `../../../conductor-impact/references/architecture-contracts.md` §4.5、`../../../conductor-tdd/references/test-strategy.md` §2/§5.5、`../../../conductor-tdd/references/coding-rules-common.md` §1 同源——
> 那些是规则正文，本文件是把它们变成退出码的门禁，并解决"老代码本就有、重构时怎么办"。

**两个脚本、一条命令**：`source_purity.py`（行级模式：类型/fake）+ `intent_gaps.py`（函数级语义：占位/未用参数）；
`source_purity.py scan/check` 默认自动合并两者（用 `--no-intent` 关闭）。存量基线对两者统一生效。

## 一、为什么规则写了还拦不住 / 为什么需要基线

- 规则文本本就完备，但都是**软约束**：`verify.py` 只跑 linter（多数项目没配严格规则，Any 不报错），
  `scan_gaps.py` 只认 `Fake/Stub/Mock` 前缀——换名字或换类型形状就逃逸。→ 需要**数据驱动规则库**。
- **重构场景的特殊矛盾**：老代码里本来就有大量不具体类型/临时实现。若门禁要求"全仓零命中"，
  AI 要么被迫大规模改无关代码（违反场景 7「禁扩大 diff」），要么直接放弃门禁。→ 需要**存量基线**：
  记录现状为基线，只卡**新增**污染；重构改到哪个文件，才负责那个文件的存量（符合"改哪算哪"）。

## 二、数据驱动规则库

内置 27 条规则，每条 = `{id, category, lang, pattern, desc, severity}`， severity=error（卡门禁）/ warn（只提示）：

| 类别 | 覆盖形状（举例） |
|---|---|
| fake_impl | 类名/变量声明含 InMemory/Memory/Fake/Stub/Mock/Dummy/Ephemeral/LocalOnly；意图注释"内存版/测试用/待换真实实现/in-memory/placeholder"；文件名 signal |
| dynamic_type · Python | `: Any`/`-> Any`/`: object`；`Dict[str, Any]`/`Callable[..., Any]`/`Optional[Any]` 等容器与泛型兜底；裸 `dict/list/tuple`（warn）；`typing.Any` 导入（warn） |
| TS/JS | `any`/`as any`/`any[]`/`Promise<any>`；`unknown`（warn）；`object`/`{}`/`Function`/`Record<string, any>`；裸数组（warn） |
| Go | `interface{}`/`any`；`map[string]any`/`[]interface{}`/`chan any`；函数参数 any（warn） |
| Rust/Dart | `dyn Any`/`Box<dyn Any>`；`dynamic`/`Object?` |
| Java/Kotlin/C# | `Object`/`Map<String,Object>`；裸泛型（warn）；`Any`（Kotlin）；`object/dynamic`（C#） |
| Ruby/PHP | YARD 注释缺类型（warn）；`mixed` |

```bash
python ../scripts/source_purity.py rules --lang python     # 列出生效规则
```
**扩展**（项目特有反模式）：`--rules custom.json` 追加规则，`--disable-rule <id>` 禁用某规则：
```json
{"rules":[{"id":"my.badtype","category":"dynamic_type","lang":"*",
          "pattern":"LegacyPayload","desc":"项目旧类型待清理"}]}
```
**验收**：新增规则后跑 `rules` 确认已加载，再 `scan` 确认能命中样例。

## 二·补、意图空白（函数级语义扫描）

行级正则抓不到"函数体结构"类问题，由 `../scripts/intent_gaps.py` 用 Python AST 精确分析
（其他语言降级为人工核对，见下方边界）。`source_purity.py scan/check` 默认自动合并其结果。

### 1. unexplained_placeholder —— 跨模块占位无注释
**问题**：设计分模块，本模块某功能依赖其他未开发模块，代码里写了 `pass` / `...` /
`raise NotImplementedError` / 空 `return` 占位，但没写"依赖谁、谁来补、何时接入"——
AI（和后人）读代码时误以为"这功能没做"，要么重复实现、要么误判为 bug。
**正确做法**：占位处写清意图，例如：
```python
def get_user(self, uid: str):
    # 依赖 auth 模块提供鉴权后接入（M3 交付后启用）
    pass
```
**合法豁免**（不算命中）：函数上方紧邻注释/docstring/函数体内注释含意图信号
（依赖/待接入/由…实现/预留/后续补/接口约定等）、`@abstractmethod`/`@overload`/Protocol 接口签名、
`purity-exempt` 留痕。

### 2. unused_param —— 参数声明未用且无说明
**问题**：参数声明了但函数体没引用，又没注释它是给谁用的、其他模块是否会传、是否预留——
信息为零，无法判断是接口契约还是死参数。
**正确做法**：写清用途，或用 `_` 前缀约定表示忽略：
```python
def calculate(self, flag: bool, _reserved_for_v2: str):  # flag 由调度模块传入，当前仅记录
    ...
```
**合法豁免**：参数名 `_` 前缀 / `self` / `cls`；docstring 的 `Args:` 里点名并说明；
抽象/接口方法；`purity-exempt` 留痕。

```bash
python ../scripts/intent_gaps.py --path src                # 单独跑
python ../scripts/intent_gaps.py --path src --strict --format json
```
**语言边界**：v1 精准支持 Python（AST）；TS/Go/Java 等的占位/未用参数由 lint 规则
（如 TS `noUnusedParameters`、Go 编译器未用参数检查）或人工核对承担——本脚本不假装覆盖。

## 三、门禁命令

```bash
# S3 写码后即时自查
python ../scripts/source_purity.py scan --path src
python ../scripts/source_purity.py scan --path src --strict          # 严格：error 命中即 1
# S4 常规收尾（无基线时全部算新增）
python ../scripts/source_purity.py check --path src --strict
# 查特定语言 / JSON 输出
python ../scripts/source_purity.py scan --path src --lang python --format json
# 关闭函数级语义扫描（只看行级类型/fake 模式）
python ../scripts/source_purity.py scan --path src --no-intent
# 单独跑意图空白扫描
python ../scripts/intent_gaps.py --path src --strict
# 旧式调用仍兼容
python ../scripts/source_purity.py --path src --strict
```
> 一条 `source_purity.py scan/check` 同时覆盖行级模式（类型/fake）与函数级语义（占位/未用参数），
> 两者命中都进同一个门禁、同一份存量基线。intent_gaps 缺失或报错时静默跳过主门禁不中断（stderr 提示）。

## 四、存量基线（重构场景核心）

```bash
# 1) 重构开始前：快照当前污染为基线（一次性）
python ../scripts/source_purity.py baseline --path src --out .purity-baseline.json
# 2) 重构过程中/收尾：只卡新增；存量单列 TODO，不强迫一次清零
python ../scripts/source_purity.py check --path src --baseline .purity-baseline.json --strict
# 3) 改到了某个老文件：让它的存量进入"本次需负责"范围
git diff --name-only > changed.txt
python ../scripts/source_purity.py check --path src --baseline .purity-baseline.json \
  --scope changed.txt --strict
```

判定语义：
- **真新增**（不在基线）：命中即 FAIL，必须处理——这是门禁的主战场。
- **存量**（在基线、且本次没改到）：单列「存量 TODO」，不卡门禁，登记进 overview 未完成项即可。
- **改到的文件**（`--scope` 命中）：其存量**升级为本次需负责**，必须清理——这就是"重构时 AI 不会处理存量"的解法：
  你改哪个文件，那个文件的老问题就躲不过门禁。
- 基线文件 `.purity-baseline.json` 是本地状态，建议进 .gitignore。

**指纹机制**：基线按 `文件:行号:规则id` 的 hash 记录。改动会使行号变化——所以 `--scope` 让整文件存量进入负责范围，
不依赖指纹精确匹配；纯新增判定仍按指纹（同一位置同一规则算存量）。

## 五、正确做法（不是"绕过扫描"，是"真的写对"）

### 情形 1：功能依赖真实环境，但开发时连不上（pgsql 场景）
错误：在 `src/` 写 `InMemoryUserRepo` 冒充 adapter，测试全绿。
正确：① `src/` 照真实基础设施写生产级 adapter（真 SQL/真协议/真错误语义）；② fake 只放 `tests/`（自动排除）；
③ 真实环境才能验证的部分登记「待真实环境验证」未完成项；④ 后续开真环境跑 `tests/integration/`。
判定：功能已实现+未验证 = 对；只写 fake 标完成 = 功能缺失断点。

### 情形 2：确实无法静态描述的类型
按 `../../../conductor-tdd/references/coding-rules-common.md` §1 用**具名别名集中定义一处**，业务签名用具体类型：
`type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]`（Python），
TS 同理用 `JsonValue`，Go 用 `json.RawMessage`，Rust 用 `serde_json::Value`——仅边界别名处豁免。

### 情形 3：重构遇到存量污染
先 `baseline` 快照 → 只清理本次改到的文件（`--scope`）→ 其余存量登记 TODO 可分批处理。
**禁止**用"老代码就这样"当理由把新增也豁免掉；**禁止**为过门禁把整仓存量一次性刷 `purity-exempt`。

## 六、留痕豁免（必须写理由，≥4 字符）

```python
class InMemoryCache:  # purity-exempt: 这是 L1 进程内缓存，非 DB 替身，生产确需
def parse(raw: dict[str, object]) -> ...:  # purity-exempt: 外部 JSON 边界，已按 JsonValue 收窄
```
三粒度：行内 `purity-exempt: <理由>` / 块级 `purity-exempt-begin/end` / 文件级 `purity-exempt-file: <理由>`（文件首 5 行）。
项目级固定例外用 `--allow-pattern '<正则>'`，须在 overview 登记依据。
每条豁免理由进 overview「验证结果」供审计；空理由（<4 字符）不生效，机器会当成未豁免。

## 七、完成判定
- S3 写码后 `scan` 自查，新增污染当场处理（类型/fake + 占位/未用参数）；
- S4 `check --path src --strict`（重构场景带 `--baseline` + `--scope`）退出 0；
- **每个跨模块占位都写明依赖谁/谁补/何时接入；每个未用参数都写明给谁用/是否预留**——
  不能让下一个人（或 AI）面对"未解释的空白"猜意图；
- 存量 TODO 与豁免理由进 overview，可追溯；
- 与 verify.py、commitment_ledger check、review_gate 叠加，互不替代；
- 任一不满足 → 不得标完成、不得进 review。

> 规则库是模式扫描（草稿+信号），有误报（如 `LocalConfig` 命中 fake）。
> 命中要打开源码核对；确认误报后写豁免留痕，别直接忽略。
