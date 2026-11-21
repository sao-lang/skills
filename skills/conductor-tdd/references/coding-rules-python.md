# 编码规则 · Python

> 语言特定规则，与 `coding-rules-common.md` 一起遵守。目标版本：Python 3.12+。

## 注释方案（Google Style docstring，中文）

- 模块 / 类 / 函数 / 方法全部写 docstring；首行一句摘要，空行后 `Args:` / `Returns:` / `Raises:` / `Yields:` / `Note:`。
- 公开 API 必须有 docstring；私有函数至少首行摘要。
- **实例属性（`self.xxx`）也必须注释**——见下节"实例属性注释"，这是最常漏的一项。
- 复杂控制流按 common §4 模板逐分支 / 逐循环注释。

```
def reserve(self, estimated_cost: float) -> Reservation | None:
    """调用前原子预留预算额度。

    Args:
        estimated_cost: 预估成本，负数按 0 处理。

    Returns:
        预留凭证；预算不足返回 None。

    Raises:
        无——预算不足是正常路径，折叠为 None。
    """
```

## 实例属性注释（最常漏，必做）

Python 的 `self.xxx` 属性没有独立 docstring 位置，光靠"函数写 docstring"会整类漏掉属性说明，
读者只能从用法反推每个字段是什么。**每一个实例属性都要有中文注释**，二选一：

1. **类级注释**（推荐，属性多或含义复杂时）——在 class docstring 后用 `Attributes:` 块集中说明：
   ```python
   class MemoryStore:
       """记忆默认实现。

       Attributes:
           _kv: (namespace, key) → 值，键值记忆本体。
           _items: item_id → MemoryItem，分层管理的记忆项。
           _tiers: item_id → 所在层（hot/warm/cold）。
           _item_times: item_id → 写入时刻，供 TTL 过期判定。
           _next_item_id: 下一个自增 item_id。
       """
   ```
2. **行内注释**（属性少、含义自明时）——在 `__init__` 每个赋值后加 `# 中文说明`。
   - **容器必须写清 key 和 value 分别是什么**：`self._kv: dict[tuple[str,str], DynamicValue] = {}  # (namespace,key)→值`。
   - 注入依赖写清"是什么 + None 时降级成什么"。
   - 计数/ID 写清"自增还是复用、从几开始"。

判定口径：**"删掉注释，别人能否一眼看懂这个属性的 key/value/生命周期？"** 不能 → 必须注释。
不要把 `self._kv = {}` 这种裸赋值留在 `__init__` 里——这是"实现了但没写明白"，S4 应打回。

## 类型

- 全部签名标注类型；用 `X | Y` 联合、`list[T]`、`dict[K, V]`，`from __future__ import annotations` 顶置。
- 禁裸 `Any`；JSON 边界用 `type JsonValue = ...` 具名别名（见 common §1）。
- 动态形态用 pydantic `BaseModel` 建模，`model_config = ConfigDict(extra="forbid")`。

## 禁魔法字符串

- 用 `class Status(StrEnum)`（3.11+ `enum.StrEnum`）定义状态 / 类型 / 事件名 / 错误码。
- 常量用模块级 `UPPER_SNAKE`；配置键集中在 `class Keys:` 或 `Final` 常量。
- 比较用 `is`（枚举成员），不用 `==` 裸字符串。

## 格式与长度

- 行宽 88（Black 默认）；docstring 72。
- 单函数 ≤ 50 行，单文件 ≤ 500 行，圈复杂度 ≤ 10。
- 工具：Black（格式）、Ruff（lint + 复杂度）、mypy --strict（类型）、pydocstyle（docstring）。

## 推荐语法

`match/case`、`type` 语句、`dataclass(slots=True, frozen=True)`、`StrEnum`、f-string 嵌套、
`typing.override`、结构模式匹配、异常组（ExceptionGroup）。

## 验证命令（S4 必跑，退出码为证据）

```bash
ruff check .                       # lint + 复杂度 + 魔法值线索
ruff format --check .              # 格式（或 black --check .）
mypy --strict src                  # 类型
pydocstyle src                     # docstring 完整性
pytest -q --cov=src --cov-fail-under=80   # 测试 + 覆盖率
```
