# 源码纯净守卫 · 测试兼容代码与动态类型的硬门禁

> 用途：拦住两类反复污染生产源码的错误——① 无真实环境时用内存/假实现冒充生产 adapter；
> ② `Any`/`object`/`dict[str, object]`/`interface{}` 等不具体类型散落签名。
> 定位：S3 写码时按需加载（写码前先读，当作生成约束）；S4 自省跑 `source_purity.py --strict` 机器判定。
> 与 `architecture-contracts.md` §4.5（无环境不砍功能）、`test-strategy.md` §2/§5.5（mock 边界/真实环境）、
> `coding-rules-common.md` §1（禁动态类型）同源——那些是规则正文，本文件是把它们变成退出码的门禁。

## 一、为什么规则写了还拦不住

三段规则文本其实都很完备，但都是**软约束**：
- `coding-rules-common.md` §1 明令禁止 `Any`/`object`，但其 §6 自承"锁 1/2 靠 prompt 自律（可能打折）"；
- `verify.py` 只跑 formatter/linter/type-checker——**多数项目没配严格 mypy/pyright/eslint 规则**，
  `Any` 和 `InMemoryStore` 编译器不报错，于是逃逸；
- `scan_gaps.py` 只认 `class Fake*/Stub*/Mock*` 前缀，AI 换个名字（`InMemoryUserRepo`、
  `LocalCache`、`内存版存储`）或干脆用 dict 兜底就绕过。

结论：需要**专门的源码模式扫描**，不依赖项目 linter 配置，直接把这两类信号变成机器判定。

## 二、门禁命令

```bash
# S3 写码后即时自查（草稿，恒 0）
python scripts/source_purity.py --path src
# S4 收尾门禁（有未豁免命中即退出 1，禁止进 review / 标完成）
python scripts/source_purity.py --path src --strict
# 只要 JSON 输出（喂台账 / CI）
python scripts/source_purity.py --path src --format json
# 只扫某语言 / 项目级例外
python scripts/source_purity.py --path src --lang python --allow-pattern 'class FakeClock' --strict
```
- 只扫生产源码（`--path src`），**自动排除 tests/test/spec/fixture 目录**——测试替身在测试区合法。
- 命中输出带 `文件:行号` + 规则名；未豁免命中与已豁免分开列。

## 三、检测的两类污染

### A. 测试兼容代码污染（fake_impl）—— 严重
扫生产源码里的：
- **fake 类名**：`class/struct/interface/type` 名含 `InMemory/InMem/Memory/Fake/Stub/Mock/Dummy/Ephemeral/InProcess/LocalOnly/TestOnly`
- **fake 变量声明**：`const/let/var/val` 声明名含 fake 信号
- **意图注释**：`内存版/内存存储/模拟实现/临时实现/测试用/开发用/in-memory/for testing only/
  placeholder/TODO 换成真实实现/not implemented/mock db`
- **文件名**：含 `inmemory/in_mem/memory/fake/stub/mock/dummy/ephemeral/localstore/testonly`

**红线**：生产路径的核心逻辑必须是真实实现。没有真实环境时的正确处理见 §四。

### B. 不具体类型（dynamic_type）
按语言扫函数签名 / 字段 / 公开 API：
| 语言 | 命中模式 |
|---|---|
| Python | `: Any`、`-> Any`、`dict[str, object]`、`list[Any]`、`typing.Any` 导入 |
| TS/JS | `: any`、`as any`、`any[]`、`<any>`、`Record<string, any>`、`: object`、`: {}` |
| Go | `interface{}`、`any`、`map[string]any`、`map[string]interface{}` |
| Rust | `Box<dyn Any>`、`dyn Any` |
| Dart | `dynamic` |
| Java | `Object`、`Map<String, Object>` |

## 四、正确做法（不是"绕过扫描"，是"真的写对"）

### 情形 1：功能依赖真实环境，但开发时连不上（用户说的 pgsql 场景）
**错误做法**（被门禁拦）：在 `src/` 写 `InMemoryUserRepo` 冒充 adapter，测试全绿。
**正确做法**：
1. `src/` 里照真实基础设施写**生产级 adapter**——真 SQL / 真协议 / 真错误语义
   （即使当场连不上库，代码语义必须是真的，见 architecture-contracts §4.5）；
2. 可注入的 fake **只放 `tests/`**（本脚本自动排除测试区）；
3. 真实环境才能验证的部分，在 overview 登记「待真实环境验证」未完成项：
   `<功能> — 生产 adapter 已落地于 <路径:行号>，待真实环境验证（需 pgsql/Docker）`；
4. 用户后续说"开真实环境测"→ 跑真实入口（`tests/integration/`），不是复用 fake 测试。

**判定**：功能已实现 + 未验证 = 对；只写 fake 标完成 = 功能缺失断点，S4 必须登记。

### 情形 2：确实无法静态描述的类型（任意 JSON、vendor payload、反射边界）
按 `coding-rules-common.md` §1 用**具名别名集中定义一处**，别散落裸 `Any`：
- Python: `type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]`
  （别名定义文件用文件级豁免，见 §五）
- TS: `type JsonValue = string | number | boolean | null | JsonValue[] | { [k: string]: JsonValue }`
- Go: `json.RawMessage` 或边界 `type Payload map[string]any`
- 关键：动态类型只出现在**边界别名定义处**，业务逻辑里必须是具体类型。

## 五、豁免（必须留痕，禁止刷空理由）

确需保留的命中，用行内注释声明，**理由 ≥4 字符**（空理由不算，机器会当成未豁免）：
```python
class InMemoryCache:  # purity-exempt: 这是 L1 进程内缓存，非 DB 替身，生产确需
def parse(raw: dict[str, object]) -> ...:  # purity-exempt: 外部 JSON 边界，已按 JsonValue 收窄
```
三种粒度：
- **行内**：`purity-exempt: <理由>` —— 单行豁免
- **块级**：`purity-exempt-begin: <理由>` … `purity-exempt-end` —— 一段代码豁免
- **文件级**：文件首 5 行 `purity-exempt-file: <理由>` —— 整个文件豁免（用于 vendor/JSON 别名集中定义处）

**纪律**：每条豁免的理由必须写进 overview「验证结果」或「未完成项」供审计；
禁止为了让门禁变绿刷 `purity-exempt: xxx` 敷衍——理由须说明"为何这里合法"。
项目级固定例外可用 `--allow-pattern '<行内正则>'`，但要在 reference 或 overview 登记依据。

## 六、完成判定
- S3 写码后跑 `source_purity.py --path src` 自查，fake/动态类型当场处理，别攒到 S4；
- S4 `source_purity.py --path src --strict` 退出 0（无未豁免命中）；
- 每条豁免理由进 overview 可追溯；
- 与 `verify.py`（格式化/类型检查/覆盖率）、`commitment_ledger.py check --strict`（零未勾销）、
  `review_gate.py`（独立 review）叠加，互不替代；
- 任一不满足 → 不得标完成、不得进 review。

> 提醒：脚本是模式扫描（草稿+信号），会有误报（如 `LocalConfig` 被当 fake）。
> 每条命中打开源码核对；但**"核对后确认是误报"要写豁免留痕**，不能直接忽略。
