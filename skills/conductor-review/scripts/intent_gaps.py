#!/usr/bin/env python3
"""意图空白扫描：抓两类"代码里有未解释空白、AI 与后人无法判断意图"的问题。

与 source_purity 的分工：source_purity 扫**行级模式**（不具体类型、fake 类名）；
本脚本扫**函数级语义**——需要理解函数体结构才能判定：
  1. unexplained_placeholder —— 跨模块占位（pass / ... / raise NotImplementedError / 空 return）
     但所在函数没有说明"依赖哪个模块 / 谁来补 / 何时接入"的注释，AI 误读为"功能没做"。
  2. unused_param —— 函数参数声明了但函数体内没用，且没有注释说明"给谁用 / 是否其他模块要传 / 预留"，
     AI 与后人无法判断是接口契约还是死参数。

关键设计：占位和未用参数**本身合法**（跨模块依赖、接口对齐、回调签名都正常），
只抓"没有意图信息"的那种——缺的是注释/契约说明，不是代码本身。
所以判定核心 = 有信号 + 无解释注释 + 无豁免。

合法豁免（不算命中）：
  - 参数名 `_` 前缀 / `self` / `cls` / `_args` / `_kwargs` —— 约定明确表示忽略
  - `@abstractmethod` / `@overload` / Protocol / `@override` —— 接口签名，参数可不用
  - 函数 docstring 或邻近注释提到该参数名，或含"依赖/待接入/由…实现/reserved/其他模块/回调/接口"等意图信号
  - 行内 `purity-exempt: <理由>` / 文件级 `purity-exempt-file:`（与 source_purity 同机制）
  - lambda / 空接口定义体

输出：与 source_purity 兼容的 JSON（hits 数组，字段 file/line/text/rule/rule_id/category/exempt）。
默认恒 0；--strict 有未豁免命中则 1。

用法：
  python scripts/intent_gaps.py --path src
  python scripts/intent_gaps.py --path src --strict --format json
  python scripts/intent_gaps.py --path src --lang python
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "overviews", "output", "__tests__"}
TEST_MARKERS = ("tests", "test", "spec", "fixture", "__tests__")
PY_EXTS = {".py"}

# 意图信号：注释里出现这些说明"这是有意的跨模块占位/预留/接口"
INTENT_SIGNAL = re.compile(
    r"依赖|待接入|待实现|由\s*\w+\s*(?:模块|实现|提供|补)|其他模块|外部模块|下游|上游|"
    r"交由|后续补|第二阶段|下一阶段|预留|保留参数|接口|回调|契约|约定|"
    r"depend|delegate|deferred|upstream|downstream|reserved|placeholder for|"
    r"implemented (?:in|by)|provided by|will be|TODO:|FIXME:|ref:", re.I
)
EXEMPT_INLINE = re.compile(r"purity-exempt:\s*(\S.{3,})", re.I)
EXEMPT_FILE = re.compile(r"purity-exempt-file:\s*(\S.{3,})", re.I)
# 占位信号（Python 函数体内的语句）
PLACEHOLDER_CALL = {"notimplementederror", "notimplemented", "pass", "todo", "unimplemented"}

VALID_CATEGORIES = {"unexplained_placeholder", "unused_param"}
VALID_LANGS = {"python"}   # v1 精准支持 Python；其他语言见文档降级说明


@dataclass(frozen=True)
class Hit:
    category: str
    file: str
    line: int
    text: str
    rule: str
    rule_id: str
    severity: str = "error"
    exempt: str = ""

    @property
    def fingerprint(self) -> str:
        import hashlib
        return hashlib.md5(f"{self.file}:{self.line}:{self.rule_id}".encode()).hexdigest()[:12]


def is_test_path(path: Path) -> bool:
    return any(part in TEST_MARKERS or "test" in part.lower() or "spec" in part.lower()
               for part in path.parts)


def iter_py(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*.py"):
        parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts):
            continue
        if is_test_path(p):
            continue
        out.append(p)
    return sorted(out)


def file_exempt(lines: list[str]) -> str:
    for ln in lines[:5]:
        m = EXEMPT_FILE.search(ln)
        if m:
            return m.group(1).strip()
    return ""


def decorators_of(fn: ast.AST) -> set[str]:
    names: set[str] = set()
    for d in getattr(fn, "decorator_list", []):
        if isinstance(d, ast.Name):
            names.add(d.id.lower())
        elif isinstance(d, ast.Attribute):
            names.add(d.attr.lower())
        elif isinstance(d, ast.Call):
            f = d.func
            if isinstance(f, ast.Name):
                names.add(f.id.lower())
            elif isinstance(f, ast.Attribute):
                names.add(f.attr.lower())
    return names


def func_comment_text(lines: list[str], fn: ast.AST, end_line: int) -> str:
    """仅取本函数的意图注释：紧邻上方的连续注释块 + docstring + 函数体内注释。
    不取上方固定 N 行——那会串味到上一个函数（典型误报源）。"""
    chunks: list[str] = []
    start = fn.lineno  # 1-based，def 所在行（含装饰器时 ast.lineno 指向 def）
    # 紧邻上方的连续注释块（从 def 上一行往上，遇到非注释行即停）
    j = start - 2  # 0-based，def 上一行
    while j >= 0 and re.match(r"\s*#", lines[j]):
        chunks.append(lines[j])
        j -= 1
    doc = ast.get_docstring(fn) or ""
    chunks.append(doc)
    # 函数体内所有注释（整个函数，不只前 8 行）
    for ln in lines[start - 1:min(end_line, len(lines))]:
        if re.match(r"\s*#", ln):
            chunks.append(ln)
    return "\n".join(chunks)


def param_names(fn: ast.AST) -> list[str]:
    a = fn.args
    names = [x.arg for x in (a.posonlyargs + a.args + a.kwonlyargs)]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return names


def used_names(fn: ast.AST) -> set[str]:
    used: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used.add(node.value.id)
    return used


def is_placeholder_stmt(stmt: ast.AST) -> bool:
    if isinstance(stmt, ast.Pass):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
        return True
    if isinstance(stmt, ast.Raise):
        exc = stmt.exc
        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            return exc.func.id.lower() in PLACEHOLDER_CALL
        if isinstance(exc, ast.Name):
            return exc.id.lower() in PLACEHOLDER_CALL
    if isinstance(stmt, ast.Return) and stmt.value is None:
        return True
    return False


def analyze_file(path: Path, root: Path, f_exempt: str) -> list[Hit]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []
    rel = path.relative_to(root).as_posix()
    hits: list[Hit] = []

    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        decos = decorators_of(fn)
        is_interface = bool(decos & {"abstractmethod", "overload", "override", "abc"})
        # 函数体最后一条语句行号（含嵌套除外，仅看本层 body）
        body = fn.body
        if not body:
            continue
        end_line = max(getattr(s, "end_lineno", s.lineno) for s in body)
        comment = func_comment_text(lines, fn, end_line)
        has_intent = bool(INTENT_SIGNAL.search(comment))
        used = used_names(fn)
        params = param_names(fn)

        # 1) 未解释占位：占位语句 + 无意图注释
        placeholders = [s for s in body if is_placeholder_stmt(s)]
        if placeholders and not is_interface and not has_intent:
            for s in placeholders:
                line_no = s.lineno
                raw = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
                inline = EXEMPT_INLINE.search(raw)
                exempt = f_exempt or (inline.group(1).strip() if inline else "")
                if exempt:
                    continue
                hits.append(Hit(
                    "unexplained_placeholder", rel, line_no, raw[:120] or "<pass>",
                    "占位/空实现缺意图注释（依赖谁/谁补/何时接入）",
                    "intent.placeholder", "error", exempt,
                ))

        # 2) 未使用参数：声明了但函数体没引用，且无意图说明。
        #    占位函数若已有意图注释（has_intent）→ 参数天然不用，不报。
        if not is_interface and not has_intent:
            for p in params:
                if p in {"self", "cls"} or p.startswith("_"):
                    continue
                if p in used:
                    continue
                # 定位参数所在行（函数签名行或续行）
                decl_line = fn.lineno
                for i in range(fn.lineno - 1, min(end_line, fn.lineno + 3)):
                    if re.search(rf"\b{re.escape(p)}\b", lines[i]):
                        decl_line = i + 1
                        break
                raw = lines[decl_line - 1].strip() if decl_line - 1 < len(lines) else ""
                inline = EXEMPT_INLINE.search(raw)
                exempt = f_exempt or (inline.group(1).strip() if inline else "")
                if exempt:
                    continue
                hits.append(Hit(
                    "unused_param", rel, decl_line, raw[:120],
                    f"参数 `{p}` 声明但未使用且无说明（给谁用/其他模块是否要传/预留？）",
                    "intent.unused_param", "error", exempt,
                ))
    return hits


def scan(root: Path, lang_filter: str) -> list[Hit]:
    hits: list[Hit] = []
    files = iter_py(root) if (not lang_filter or lang_filter == "python") else []
    for f in files:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        hits.extend(analyze_file(f, root, file_exempt(lines)))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 意图空白扫描（无注释占位 / 未使用参数）")
    ap.add_argument("--path", default="src", help="生产源码根路径")
    ap.add_argument("--lang", default="", choices=sorted(VALID_LANGS), help="语言（v1 支持 python）")
    ap.add_argument("--format", default="text", choices=("text", "json"))
    ap.add_argument("--strict", action="store_true", help="有未豁免命中即退出 1")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"FAIL — 源码目录不存在：{root}")
        return 1
    hits = scan(root, args.lang)
    unexempt = [h for h in hits if not h.exempt]

    if args.format == "json":
        print(json.dumps({"hits": [asdict(h) for h in hits],
                          "unexempt_count": len(unexempt)}, ensure_ascii=False, indent=2))
        return 1 if (args.strict and unexempt) else 0

    print(f"# 意图空白扫描（{root}）\n")
    print(f"- 未豁免命中：{len(unexempt)} · 已豁免：{len(hits) - len(unexempt)}")
    if not hits:
        print("\n未检出意图空白。仍需人工核对跨模块契约与装配（见 architecture-contracts）。")
        return 0
    for h in hits:
        mark = "豁免" if h.exempt else "FAIL"
        extra = f" — 理由：{h.exempt}" if h.exempt else ""
        print(f"- [{mark}/{h.rule_id}] `{h.file}:{h.line}` — {h.rule}{extra}")
        print(f"    {h.text}")
    print("\n> 处理：占位写清依赖哪个模块/谁补/何时接入；未用参数写清给谁用/是否预留，"
          "或加 `purity-exempt: <理由>`（≥4字符）。")
    print("> 退出码 0 = 草稿；`--strict` 有未豁免命中则 1 = 禁止进 review / 标完成。")
    return 1 if (args.strict and unexempt) else 0


if __name__ == "__main__":
    sys.exit(main())
