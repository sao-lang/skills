#!/usr/bin/env python3
"""源码纯净门禁：抓两类高发污染，把 coding-rules 的软约束变成机器可判定的退出码。

起因：AI 写码时反复犯两类错，规则文本写得再全也拦不住（锁1/2靠自律）：
  1. **测试兼容代码污染源码**——无真实环境（DB/Redis/外部API）时，在 src/ 里写 InMemoryStore /
     内存版存储 / LocalRepo 冒充生产 adapter，测试全绿但生产路径是假的。
  2. **不具体类型滥用**——Any / object / dict[str, object] / interface{} / any 散落在函数签名与
     公开字段，类型系统形同虚设。

哲学同 scan_gaps/verify：脚本出草稿 + 机器判定，人工核实与豁免判断归人/AI。
默认恒 0（草稿供核对）；--strict 下有未豁免命中则 1（S4 门禁，禁止进 review / 标完成）。

豁免（必须带理由，空理由不算）：
  行内：在命中行末尾写  purity-exempt: <理由>
  块级：purity-exempt-begin: <理由>  ...  purity-exempt-end
  文件级：文件首 5 行内写  purity-exempt-file: <理由>
理由会出现在报告里供 overview 登记；禁止为过门禁刷空豁免（理由需 ≥4 字符）。

用法：
  python scripts/source_purity.py --path src
  python scripts/source_purity.py --path src --lang python --strict
  python scripts/source_purity.py --path src --format json
  python scripts/source_purity.py --path src --allow-pattern 'class FakeClock' --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_EXTS = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "typescript", ".jsx": "typescript", ".vue": "typescript",
    ".go": "go", ".rs": "rust", ".dart": "dart", ".java": "java",
}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "overviews", "output", "__tests__"}
# 这些目录视为测试区，其中允许 fake / 测试替身（本脚本只扫生产源码）
TEST_MARKERS = ("tests", "test", "spec", "fixture", "__tests__")

EXEMPT_INLINE = re.compile(r"purity-exempt:\s*(\S.{3,})", re.I)
EXEMPT_BEGIN = re.compile(r"purity-exempt-begin:\s*(\S.{3,})", re.I)
EXEMPT_END = re.compile(r"purity-exempt-end", re.I)
EXEMPT_FILE = re.compile(r"purity-exempt-file:\s*(\S.{3,})", re.I)

# ---------- 检测规则 ----------

# 1) fake / 内存实现冒充生产（类名、变量名、文件名、注释信号）
FAKE_CLASS_RE = re.compile(
    r"\b(?:class|struct|interface|type)\s+(\w*(?:InMemory|InMem|Memory|Fake|Stub|Mock|Dummy|"
    r"Ephemeral|InProcess|LocalOnly|TestOnly)\w*)", re.I
)
FAKE_DECL_RE = re.compile(
    r"\b(?:const|let|var|val)\s+(\w*(?:InMemory|InMem|Fake|Stub|Mock|Dummy|Ephemeral)\w*)\s*[=:]",
    re.I
)
# 生产源码里出现"内存存储 / 测试替身 / 待换真实实现"的意图信号
FAKE_COMMENT_RE = re.compile(
    r"内存(版|存储|实现|模拟|替身|缓存)|(模拟|假|临时|测试|开发)(版|实现|存储|替身|数据)"
    r"|in[- ]?memory|for testing only|test[- ]?only|placeholder"
    r"|TODO[^\n]{0,60}(real|真实|replace|替换|换成|production|生产)"
    r"|not (yet )?implemented|mock (db|storage|repo|backend)", re.I
)
FAKE_FILENAME_RE = re.compile(
    r"(^|[-_.])(inmemory|in_memory|inmem|memory|fake|stub|mock|dummy|ephemeral|localstore|testonly)([-_.]|$)",
    re.I
)

# 2) 不具体 / 动态类型（按语言）
# Python：函数签名 / 变量注解里的 Any、object、以及容器套 Any/object
PY_ANY_RE = re.compile(
    r"(?::|->)\s*(?:dict|list|set|tuple|Dict|List|Set|Tuple|Mapping|Sequence)\s*\[[^\]]*\b(?:Any|object)\b[^\]]*\]"
    r"|(?::|->)\s*(?:Any|object)\b"
    r"|\b(?:Any|object)\s*(?=[,)\]])",
)
PY_BARE_ANY_IMPORT = re.compile(r"from\s+typing\s+import[^\n]*\bAny\b")

# TS/JS：: any / any[] / as any / Record<string, any> / : object / <any>
TS_ANY_RE = re.compile(
    r":\s*any\b|\bas\s+any\b|\bany\[\]|<\s*any\s*>"
    r"|Record\s*<\s*string\s*,\s*(?:any|object)\s*>"
    r"|:\s*object\b|:\s*\{\s*\}\b",  # 空对象类型 : {} 也属不具体
)

# Go：interface{} / any / map[string]any / map[string]interface{}
GO_ANY_RE = re.compile(r"\binterface\s*\{\s*\}|\bany\b|map\s*\[\s*string\s*\]\s*(?:any|interface\s*\{\s*\})")

# Rust / Dart / Java 的兜底动态类型
RUST_ANY_RE = re.compile(r"\bBox\s*<\s*dyn\s+Any\s*>|\bdyn\s+Any\b")
DART_ANY_RE = re.compile(r"\bdynamic\b")
JAVA_ANY_RE = re.compile(r"\bObject\b(?!\s*\[\])|\bMap\s*<\s*String\s*,\s*Object\s*>")

TYPE_RULES = {
    "python": (PY_ANY_RE, "Python 动态类型 Any/object"),
    "typescript": (TS_ANY_RE, "TS 动态类型 any/object/{}"),
    "go": (GO_ANY_RE, "Go 动态类型 interface{}/any"),
    "rust": (RUST_ANY_RE, "Rust 动态类型 dyn Any"),
    "dart": (DART_ANY_RE, "Dart 动态类型 dynamic"),
    "java": (JAVA_ANY_RE, "Java 动态类型 Object"),
}

VALID_CATEGORIES = {"fake_impl", "dynamic_type"}


@dataclass(frozen=True)
class Hit:
    category: str      # fake_impl | dynamic_type
    file: str
    line: int
    text: str
    rule: str
    exempt: str = ""   # 非空=已豁免（附理由）


def is_test_path(path: Path) -> bool:
    return any(
        part in TEST_MARKERS or "test" in part.lower() or "spec" in part.lower()
        for part in path.parts
    )


def iter_source(root: Path, exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in parts):
            continue
        if is_test_path(p):
            continue
        files.append(p)
    return sorted(files)


def file_level_exempt(lines: list[str]) -> str:
    for ln in lines[:5]:
        m = EXEMPT_FILE.search(ln)
        if m:
            return m.group(1).strip()
    return ""


def inline_exempt(line: str) -> str:
    m = EXEMPT_INLINE.search(line)
    return m.group(1).strip() if m else ""


def scan_file(path: Path, root: Path, lang: str, allow: list[re.Pattern]) -> list[Hit]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    f_exempt = file_level_exempt(lines)
    rel = path.relative_to(root).as_posix()
    hits: list[Hit] = []
    block_exempt = ""
    fname = path.name
    fname_hit = bool(FAKE_FILENAME_RE.search(fname))

    # 类型规则
    type_re, type_rule = TYPE_RULES.get(lang, (None, ""))

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if EXEMPT_END.search(line):
            block_exempt = ""
        begin = EXEMPT_BEGIN.search(line)
        if begin:
            block_exempt = begin.group(1).strip()
        exempt = f_exempt or block_exempt or inline_exempt(line)

        # 允许模式：命中即整行放行
        if any(p.search(line) for p in allow):
            continue

        # 文件级 fake 文件名信号：只在首行记录一次
        if fname_hit and i == 1:
            hits.append(Hit("fake_impl", rel, 1, f"文件名含测试替身信号：{fname}",
                            "fake-filename", exempt))

        for pattern, rule in (
            (FAKE_CLASS_RE, "fake 类名（生产源码禁止）"),
            (FAKE_DECL_RE, "fake 变量声明（生产源码禁止）"),
            (FAKE_COMMENT_RE, "内存/测试替身意图注释"),
        ):
            if pattern.search(line):
                hits.append(Hit("fake_impl", rel, i, stripped[:120], rule, exempt))

        if type_re is not None:
            m = type_re.search(line)
            if m:
                hits.append(Hit("dynamic_type", rel, i, stripped[:120], type_rule, exempt))
        if lang == "python" and PY_BARE_ANY_IMPORT.search(line):
            hits.append(Hit("dynamic_type", rel, i, stripped[:120],
                            "typing.Any 导入（应改具名别名）", exempt))

    return hits


def scan(root: Path, exts: set[str], lang_filter: str, allow_patterns: list[str]) -> list[Hit]:
    allow = [re.compile(p) for p in allow_patterns]
    hits: list[Hit] = []
    for f in iter_source(root, exts):
        lang = DEFAULT_EXTS.get(f.suffix, "")
        if lang_filter and lang != lang_filter:
            continue
        hits.extend(scan_file(f, root, lang, allow))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 源码纯净门禁（fake 实现 / 动态类型）")
    ap.add_argument("--path", default="src", help="生产源码根路径（默认 src）")
    ap.add_argument("--lang", default="", choices=list(TYPE_RULES), help="只扫某一语言")
    ap.add_argument("--exts", default="", help="覆盖扩展名，逗号分隔（如 .py,.ts）")
    ap.add_argument("--format", default="text", choices=("text", "json"), help="输出格式")
    ap.add_argument("--allow-pattern", action="append", default=[],
                    help="行内正则命中即放行（可重复），用于项目级例外")
    ap.add_argument("--strict", action="store_true", help="有未豁免命中即退出 1（S4 门禁）")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"FAIL — 源码目录不存在：{root}")
        return 1
    exts = ({e.strip() for e in args.exts.split(",") if e.strip()} if args.exts
            else set(DEFAULT_EXTS))
    hits = scan(root, exts, args.lang, args.allow_pattern)
    unexempt = [h for h in hits if not h.exempt]
    fake = [h for h in unexempt if h.category == "fake_impl"]
    dyn = [h for h in unexempt if h.category == "dynamic_type"]
    exempted = [h for h in hits if h.exempt]

    if args.format == "json":
        print(json.dumps({"hits": [asdict(h) for h in hits],
                          "unexempt_count": len(unexempt),
                          "exempted_count": len(exempted)}, ensure_ascii=False, indent=2))
        return 1 if (args.strict and unexempt) else 0

    print(f"# 源码纯净扫描（{root}）\n")
    print(f"- 未豁免命中：{len(unexempt)}（fake 实现 {len(fake)}，动态类型 {len(dyn)}）")
    print(f"- 已豁免：{len(exempted)}（理由见报告）")
    if not hits:
        print("\n未检出污染信号。仍需人工核对：真实 adapter 是否连真基础设施、跨进程契约与副作用。")
        return 0

    if fake:
        print("\n## 测试兼容代码污染（fake_impl）")
        for h in fake:
            print(f"- [{h.rule}] `{h.file}:{h.line}` — {h.text}")
    if dyn:
        print("\n## 不具体类型（dynamic_type）")
        for h in dyn:
            print(f"- [{h.rule}] `{h.file}:{h.line}` — {h.text}")
    if exempted:
        print("\n## 已豁免（需在 overview 登记理由）")
        for h in exempted:
            print(f"- `{h.file}:{h.line}` — {h.rule} — 理由：{h.exempt}")

    print("\n> 处理：fake 实现移到 tests/、src/ 只留生产级真实 adapter；"
          "动态类型改具名别名/具体类型；确需保留的按 purity-exempt 写理由（≥4 字符）。")
    print("> 退出码 0 = 草稿/核对；`--strict` 下有未豁免命中则 1 = 禁止进 review / 标完成。")
    return 1 if (args.strict and unexempt) else 0


if __name__ == "__main__":
    sys.exit(main())
