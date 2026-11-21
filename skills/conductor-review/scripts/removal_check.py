#!/usr/bin/env python3
"""待删项残留核对：从 change-contract 的 Delta 段提取"删除/替换"条目，
扫全仓核对这些符号是否真的消失。定义或引用仍存在即 FAIL（退出码 1）。

用途：反"该删没删"——需求变更后旧字段/函数/逻辑/功能/文档仍留在代码里。
与 impact_analysis（找谁引用）互补：本脚本把"应该消失的东西"变成机器门禁。

输入（可叠加）：
  --contract  change-contract.md   从 Delta 段提取含"删除/移除/替换/废弃/下线"且带反引号符号名的条目
  --symbols   Foo,bar              直接给待删符号
  --list      removals.txt         每行一个待删符号（# 注释行忽略）

扫描：
  --path  <root>       源码根（默认 .）
  --exts  .py,.ts,...  覆盖扩展名
  定义 = def/class/fn/const/字段声明；引用 = 词边界命中（排除定义行与纯注释行）

退出码：0 = 所有待删项已消失（或没有待删项）；1 = 有残留或缺 --contract/--symbols/--list。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_EXTS = ".py,.ts,.tsx,.js,.jsx,.vue,.go,.rs,.dart,.java,.kt,.cs,.rb,.php"
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "overviews", "output", "tests"}
DELETE_VERBS = ("删除", "移除", "替换", "废弃", "下线", "去掉", "delete", "remove", "drop", "replace")
BACKTICK = re.compile(r"`([^`]+)`")
SYMBOL_OK = re.compile(r"^[A-Za-z_][\w$.:/\-]{0,120}$")
DEF_PATTERNS = (
    r"^\s*(?:async\s+)?def\s+{s}\s*\(",                    # python
    r"^\s*class\s+{s}\b",                                   # python/ts/js
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+{s}\s*\(",
    r"^\s*(?:export\s+)?(?:const|let|var|val)\s+{s}\s*[=:]",
    r"^\s*(?:pub\s+)?fn\s+{s}\s*\(",                        # rust
    r"^\s*func\s+(?:\([^)]*\)\s*)?{s}\s*\(",               # go
    r"^\s*(?:public|private|protected)?\s*\w+\s+{s}\s*[=(;]",  # java/cs/ts 字段
    r"^\s*{s}\s*[:=]",                                  # 无类型字段/配置键（py 数据类/JSON 式配置）
)
COMMENT_LINE = re.compile(r"^\s*(?:#|//|/\*|\*|<!--)")


def split_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    out: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1).strip()] = text[m.end():end]
    return out


def from_contract(path: Path) -> tuple[list[str], list[str]]:
    """返回（待删符号, 无符号名无法核对的条目）。"""
    if not path.is_file():
        return [], [f"契约文件不存在：{path}"]
    sections = split_sections(path.read_text(encoding="utf-8"))
    delta = sections.get("Delta", "")
    symbols: list[str] = []
    unverifiable: list[str] = []
    for line in delta.splitlines():
        s = line.strip()
        if not s.startswith(("-", "*", "+")):
            continue
        body = s.lstrip("-*+ ").strip()
        if not any(v in body.lower() for v in DELETE_VERBS):
            continue
        candidates = [c.strip() for c in BACKTICK.findall(body)]
        # 只取像符号名的候选（排除说明性反引号）
        named = [c for c in candidates if SYMBOL_OK.match(c) and not c.startswith("新条目")]
        if named:
            symbols.extend(named)
        else:
            unverifiable.append(body)
    return list(dict.fromkeys(symbols)), unverifiable


def from_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return list(dict.fromkeys(out))


def iter_source(root: Path, exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts):
            continue
        files.append(p)
    return sorted(files)


def check_symbol(symbol: str, files: list[Path], root: Path) -> tuple[list[str], list[str]]:
    """返回（定义处, 引用处）。"""
    defs: list[str] = []
    refs: list[str] = []
    word = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(symbol) + r"(?![A-Za-z0-9_])")
    try:
        def_re = [re.compile(p.format(s=re.escape(symbol))) for p in DEF_PATTERNS]
    except re.error:
        def_re = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = f.relative_to(root).as_posix()
        for i, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if COMMENT_LINE.match(line):
                continue
            if any(p.match(line) for p in def_re):
                defs.append(f"{rel}:{i}: {stripped[:100]}")
            elif word.search(line):
                refs.append(f"{rel}:{i}: {stripped[:100]}")
    return defs, refs


def main() -> int:
    ap = argparse.ArgumentParser(description="待删项残留核对（该删没删 → FAIL）")
    ap.add_argument("--contract", help="change-contract 路径，从 Delta 提取待删项")
    ap.add_argument("--symbols", help="逗号分隔的待删符号")
    ap.add_argument("--list", dest="list_file", help="每行一个待删符号的清单文件")
    ap.add_argument("--path", default=".", help="源码根目录（默认 .）")
    ap.add_argument("--exts", default=DEFAULT_EXTS, help="扫描扩展名，逗号分隔")
    args = ap.parse_args()

    symbols: list[str] = []
    unverifiable: list[str] = []
    if args.contract:
        syms, unver = from_contract(Path(args.contract))
        symbols += syms
        unverifiable += unver
    if args.symbols:
        symbols += [s.strip() for s in args.symbols.split(",") if s.strip()]
    if args.list_file:
        symbols += from_list(Path(args.list_file))
    symbols = list(dict.fromkeys(symbols))

    print("# 待删项残留核对\n")
    if not symbols:
        print("未提取到任何待删符号——契约 Delta 里的删除条目必须用反引号带符号名，"
              "或用 --symbols/--list 显式给出。", file=sys.stderr)
        for u in unverifiable:
            print(f"[无法核对] {u}", file=sys.stderr)
        return 1

    root = Path(args.path).resolve()
    exts = {e.strip() for e in args.exts.split(",") if e.strip()}
    files = iter_source(root, exts)
    print(f"- 待删项 {len(symbols)} 个 · 扫描 {len(files)} 个源文件")

    residual = 0
    for symbol in symbols:
        defs, refs = check_symbol(symbol, files, root)
        if defs or refs:
            residual += 1
            print(f"\n## 残留：{symbol}")
            for d in defs[:8]:
                print(f"  [定义] {d}")
            for r in refs[:8]:
                print(f"  [引用] {r}")
            if len(defs) + len(refs) > 16:
                print(f"  ... 另有 {len(defs) + len(refs) - 16} 处")
        else:
            print(f"\n## 已清除：{symbol}")

    for u in unverifiable:
        print(f"\n[无法核对] {u} —— 请补反引号符号名后重跑")

    if residual:
        print(f"\n> FAIL：{residual}/{len(symbols)} 个待删项仍有残留，禁止进 review / 标完成。")
        return 1
    print(f"\n> PASS：{len(symbols)} 个待删项均已消失（{len(unverifiable)} 条无法核对需人工确认）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
