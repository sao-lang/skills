#!/usr/bin/env python3
"""变更影响分析：给定改动的符号/文件，静态找出「谁引用它」「该跑哪些测试」（S1/S2 影响面）。

输出必改文件/必跑测试的草稿，喂给计划与 TDD。启发式需人工核实，
**不替代 graphify 精确调用图**（有则优先用）。退出码恒 0，--fail-on-refs 有外部引用即 1。

输入（三选一，可叠加）：
  --symbols  Foo,bar        直接给符号名（函数/类/方法）
  --files    src/a.py,...   给改动文件，自动提取其中定义的顶层符号
  --diff                    从 stdin 读 `git diff --name-only` 的输出，当作改动文件

扫描目标：
  1. 定义位置：def/class（py）、function/class/export const（ts/js/tsx/vue）
  2. 外部引用：符号名在全仓的出现（排除定义行与注释行），带 file:line
  3. 建议测试：按命名约定（test_<mod>/<mod>_test/<mod>.spec）匹配 + 直接引用该符号的测试文件
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_EXTS = ".py,.ts,.tsx,.js,.jsx,.vue,.go,.rs,.dart"
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "overviews", "output"}
TEST_HINTS = ("test", "spec", "__tests__")

# 各语言顶层符号定义
DEF_PATTERNS = (
    re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.M),              # py
    re.compile(r"^\s*class\s+(\w+)\b", re.M),                             # py/ts/js
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(", re.M),
    re.compile(r"^\s*export\s+(?:const|let|var)\s+(\w+)\s*[=:]", re.M),    # ts/js
    re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)\s*\(", re.M),                  # rust
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(\w+)\s*\(", re.M),         # go
)


@dataclass(frozen=True)
class Definition:
    symbol: str
    file: str
    line: int


@dataclass(frozen=True)
class Reference:
    symbol: str
    file: str
    line: int
    text: str


def iter_source(root: Path, exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in p.parts):
            continue
        files.append(p)
    return files


def is_test_file(path: Path) -> bool:
    low = str(path).lower()
    return any(h in low for h in TEST_HINTS)


def extract_defs(files: list[Path], root: Path) -> list[Definition]:
    defs: list[Definition] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(f.relative_to(root))
        for pat in DEF_PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                defs.append(Definition(m.group(1), rel, line))
    return defs


def find_references(symbols: set[str], all_texts: dict[Path, str],
                    root: Path, definitions: list[Definition]) -> list[Reference]:
    def_pts = {(d.file, d.line) for d in definitions}
    refs: list[Reference] = []
    for f, text in all_texts.items():
        rel = str(f.relative_to(root))
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith(("#", "//", "/*", "*")):
                continue
            # 跳过定义行本身（def/class/fn/function 声明），避免自引用噪声
            for sym in symbols:
                if not re.search(rf"\b{re.escape(sym)}\b", line):
                    continue
                if (rel, i) in def_pts:
                    continue
                if re.match(rf"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:pub\s+)?"
                            rf"(?:def|class|fn|func|function)\s+{re.escape(sym)}\b", line):
                    continue
                refs.append(Reference(sym, rel, i, stripped[:90]))
    return refs


def suggest_tests(symbols: set[str], defs: list[Definition],
                  all_texts: dict[Path, str], root: Path) -> list[str]:
    tests: set[str] = set()
    # 1. 直接引用符号的测试文件
    for f, text in all_texts.items():
        if not is_test_file(f):
            continue
        if any(re.search(rf"\b{re.escape(sym)}\b", text) for sym in symbols):
            tests.add(str(f.relative_to(root)))
    # 2. 按模块名匹配
    for d in defs:
        stem = Path(d.file).stem
        base = stem[5:] if stem.startswith("test_") else stem
        for f, _ in all_texts.items():
            if is_test_file(f) and base.lower() in f.stem.lower():
                tests.add(str(f.relative_to(root)))
    return sorted(tests)


def parse_diff_files() -> list[str]:
    return [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 变更影响分析（草稿）")
    ap.add_argument("--path", default=".", help="源码根路径")
    ap.add_argument("--symbols", default="", help="符号名，逗号分隔")
    ap.add_argument("--files", default="", help="改动文件路径，逗号分隔（自动提取符号）")
    ap.add_argument("--diff", action="store_true", help="从 stdin 读 git diff --name-only")
    ap.add_argument("--exts", default=DEFAULT_EXTS, help="扫描扩展名，逗号分隔")
    ap.add_argument("--fail-on-refs", action="store_true", help="有外部引用即返回 1")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    exts = {e.strip() for e in args.exts.split(",") if e.strip()}
    files = iter_source(root, exts)
    all_texts: dict[Path, str] = {}
    for f in files:
        try:
            all_texts[f] = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

    symbols: set[str] = {s.strip() for s in args.symbols.split(",") if s.strip()}
    changed: list[str] = [x.strip() for x in args.files.split(",") if x.strip()]
    if args.diff:
        changed += parse_diff_files()

    definitions: list[Definition] = []
    if changed:
        changed_paths = [root / c for c in changed if (root / c).is_file()]
        definitions = extract_defs(changed_paths, root)
        symbols |= {d.symbol for d in definitions}

    if not symbols:
        print("# 变更影响分析\n")
        print("未指定符号。用 --symbols Foo,bar / --files src/a.py / --diff 提供输入。")
        return 0

    refs = find_references(symbols, all_texts, root, definitions)
    tests = suggest_tests(symbols, definitions, all_texts, root)

    print(f"# 变更影响分析（{root}）\n")
    print(f"分析符号（{len(symbols)}）：{', '.join(sorted(symbols))}\n")

    print("## 必看定义位置")
    if definitions:
        for d in definitions:
            print(f"- `{d.file}:{d.line}` — {d.symbol}")
    else:
        print("- （未提供改动文件，跳过；用 --files 可列出定义位置）")
    print()

    print(f"## 外部引用（{len(refs)} 处，逐条核实是否需同步改）")
    by_sym: dict[str, list[Reference]] = {}
    for r in refs:
        by_sym.setdefault(r.symbol, []).append(r)
    if not refs:
        print("- 未发现符号引用（注意：动态调用/字符串反射查不到，需人工核对）")
    for sym, items in sorted(by_sym.items()):
        print(f"### {sym}（{len(items)}）")
        for r in items:
            print(f"- `{r.file}:{r.line}` — {r.text}")
        print()

    print("## 建议跑的测试")
    if tests:
        for t in tests:
            print(f"- {t}")
    else:
        print("- 未匹配到测试文件——若该行为重要，按 TDD 补 characterization test（见 test-strategy.md）")
    print()
    print("> 草稿仅供核对：静态匹配含同名误报，动态调用查不到；graphify 可用时以其精确调用图为准。")
    return 1 if (args.fail_on_refs and refs) else 0


if __name__ == "__main__":
    sys.exit(main())
