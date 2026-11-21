#!/usr/bin/env python3
"""源码纯净门禁：数据驱动规则库 + 存量基线，把 coding-rules 软约束变成机器判定。

起因：AI 反复两类错——① 无真实环境时在 src/ 写 InMemoryStore/内存版冒充生产 adapter；
② 不具体类型（Any/object/interface{}/dynamic/裸容器…）散落签名。
规则文本早有（coding-rules-common §1 等）但拦不住：verify.py 只跑 linter，多数项目不报错；
scan_gaps 只认固定前缀。本脚本用可扩展规则库扫模式，退出码即证据。

三条核心能力：
  1. **数据驱动规则库**——内置规则表覆盖各语言多种"不具体类型"形状 + fake 信号；
     --rules 可追加项目自定义规则（JSON）。不再硬编码单一正则。
  2. **存量基线（baseline）**——重构场景：老代码本就有这些类型，不能要求一次清零（违反禁扩大 diff）。
     `baseline` 把当前命中快照为 .purity-baseline.json；`check --strict` 默认只卡**新增**命中（不在基线里的），
     存量单列 TODO 台账。`--scope` 可只看本次改动文件，配合 `git diff --name-only`。
  3. **留痕豁免**——purity-exempt 三粒度（行内/块级/文件级），理由 ≥4 字符，空理由不算。

用法：
  python scripts/source_purity.py scan --path src [--lang python] [--format json] [--strict]
  python scripts/source_purity.py baseline --path src [--out .purity-baseline.json]
  python scripts/source_purity.py check --path src [--baseline .purity-baseline.json] \
      [--scope changed.txt] [--strict] [--format json]
  python scripts/source_purity.py rules --lang python          # 列出当前规则
  python scripts/source_purity.py --path src --strict           # 兼容旧调用（等价于 scan --strict）

退出码：scan/check 默认 0（草稿）；--strict 下有"新增且未豁免"命中则 1（S4 门禁）。
哲学同 scan_gaps/verify：机器出草稿+判定，人工核实与豁免判断归人/AI。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_EXTS = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "typescript", ".jsx": "typescript", ".vue": "typescript",
    ".go": "go", ".rs": "rust", ".dart": "dart", ".java": "java",
    ".kt": "kotlin", ".swift": "swift", ".cs": "csharp", ".rb": "ruby", ".php": "php",
}
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "overviews", "output", "__tests__"}
TEST_MARKERS = ("tests", "test", "spec", "fixture", "__tests__")
DEFAULT_BASELINE = ".purity-baseline.json"

EXEMPT_INLINE = re.compile(r"purity-exempt:\s*(\S.{3,})", re.I)
EXEMPT_BEGIN = re.compile(r"purity-exempt-begin:\s*(\S.{3,})", re.I)
EXEMPT_END = re.compile(r"purity-exempt-end", re.I)
EXEMPT_FILE = re.compile(r"purity-exempt-file:\s*(\S.{3,})", re.I)


# ---------- 数据驱动规则库 ----------

@dataclass(frozen=True)
class Rule:
    id: str
    category: str        # fake_impl | dynamic_type
    lang: str            # python | typescript | ... | "*" 通用
    pattern: str         # 正则字符串
    desc: str
    severity: str = "error"   # error | warn（warn 只提示不卡门禁）


# 每条规则独立、可单独开关（--disable-rule）、可追加（--rules）。
# 覆盖"不具体类型"的多种形状：裸动态类型、容器包装、泛型兜底、类型别名、缺类型等。
BUILTIN_RULES: list[Rule] = [
    # ===== fake / 内存实现冒充生产 =====
    Rule("fake.class", "fake_impl", "*",
         r"\b(?:class|struct|interface|type)\s+(\w*(?:InMemory|InMem|Memory|Fake|Stub|Mock|Dummy|"
         r"Ephemeral|InProcess|LocalOnly|TestOnly)\w*)", "fake/内存类名（生产源码禁止）"),
    Rule("fake.decl", "fake_impl", "*",
         r"\b(?:const|let|var|val)\s+(\w*(?:InMemory|InMem|Fake|Stub|Mock|Dummy|Ephemeral)\w*)\s*[=:]",
         "fake 变量声明"),
    Rule("fake.intent", "fake_impl", "*",
         r"内存(版|存储|实现|模拟|替身|缓存)|(模拟|假|临时|测试|开发)(版|实现|存储|替身|数据)"
         r"|in[- ]?memory|for testing only|test[- ]?only|placeholder"
         r"|TODO[^\n]{0,60}(real|真实|replace|替换|换成|production|生产)"
         r"|not (yet )?implemented|mock (db|storage|repo|backend)", "内存/测试替身意图注释"),
    Rule("fake.filename", "fake_impl", "*",
         r"(^|[-_.])(inmemory|in_memory|inmem|memory|fake|stub|mock|dummy|ephemeral|localstore|testonly)([-_.]|$)",
         "文件名含测试替身信号", "warn"),  # 文件名走单独通道，这里保留供 rules 展示

    # ===== Python 不具体类型（多种形状）=====
    Rule("py.any-annotation", "dynamic_type", "python",
         r"(?::|->)\s*(?:Any|typing\.Any)\b|\b(?:Any|typing\.Any)\s*(?=[,)\]])", "注解用 Any"),
    Rule("py.object-annotation", "dynamic_type", "python",
         r"(?::|->)\s*object\b|\bobject\s*(?=[,)\]])", "注解用 object"),
    Rule("py.dyn-container", "dynamic_type", "python",
         r"\b(?:dict|list|set|tuple|Dict|List|Set|Tuple|Mapping|MutableMapping|Sequence|Iterable|"
         r"Collection|Callable|Type|Optional|Union)\s*\[[^\]\n]*\b(?:Any|object)\b[^\]\n]*\]",
         "容器/泛型参数含 Any/object"),
    Rule("py.bare-container", "dynamic_type", "python",
         r"(?::|->)\s*(?:dict|list|set|tuple|Dict|List|Set|Tuple)\b(?!\s*\[)", "裸容器类型（缺元素类型）", "warn"),
    Rule("py.any-import", "dynamic_type", "python",
         r"from\s+typing\s+import[^\n]*\bAny\b|\bimport\s+typing[^\n]*", "typing.Any 导入", "warn"),
    Rule("py.callable-ellipsis", "dynamic_type", "python",
         r"Callable\s*\[\s*\.\.\.", "Callable[..., ...] 省略参数类型", "warn"),

    # ===== TypeScript / JavaScript =====
    Rule("ts.any", "dynamic_type", "typescript",
         r":\s*any\b|\bas\s+any\b|\bany\[\]|<\s*any\s*>|Array\s*<\s*any\s*>|Promise\s*<\s*any\s*>",
         "TS any"),
    Rule("ts.unknown", "dynamic_type", "typescript",
         r":\s*unknown\b|as\s+unknown\b", "TS unknown（未收窄）", "warn"),
    Rule("ts.object", "dynamic_type", "typescript",
         r":\s*object\b|:\s*\{\s*\}\b|Record\s*<\s*string\s*,\s*(?:any|object|unknown)\s*>|"
         r"\bFunction\b(?=\s*[>),;=]|\s+\w)", "TS object/{}/Function 不具体类型"),
    Rule("ts.bare-array", "dynamic_type", "typescript",
         r":\s*(?:Array|array)\b(?!\s*<)|:\s*\[\s*\]\b", "裸数组类型（缺元素类型）", "warn"),

    # ===== Go =====
    Rule("go.empty-iface", "dynamic_type", "go",
         r"\binterface\s*\{\s*\}|\bany\b", "Go interface{}/any"),
    Rule("go.dyn-container", "dynamic_type", "go",
         r"(?:map\s*\[[^\]]+\]|\[\]|chan\s+|<-chan\s+)\s*(?:any|interface\s*\{\s*\})", "Go 容器元素为 any"),
    Rule("go.func-any", "dynamic_type", "go",
         r"func\s*\([^)]*\b(?:any|interface\s*\{\s*\})\b[^)]*\)", "Go 函数参数含 any", "warn"),

    # ===== Rust =====
    Rule("rs.dyn-any", "dynamic_type", "rust",
         r"\bBox\s*<\s*dyn\s+Any\s*>|\bdyn\s+Any\b|&\s*dyn\s+Any\b", "Rust dyn Any"),
    Rule("rs.unit-placeholder", "dynamic_type", "rust",
         r"->\s*\(\s*\)\s*\{|:\s*\(&\s*\)", "Rust 空元组占位返回", "warn"),

    # ===== Dart =====
    Rule("dart.dynamic", "dynamic_type", "dart",
         r"\bdynamic\b", "Dart dynamic"),
    Rule("dart.object", "dynamic_type", "dart",
         r"\bObject\s*\??\b(?!\s*\{)", "Dart Object（JSON 边界外）", "warn"),

    # ===== Java / Kotlin / C# =====
    Rule("java.object", "dynamic_type", "java",
         r"\bObject\b(?!\s*\[\])|\bMap\s*<\s*String\s*,\s*Object\s*>|\bList\s*<\s*Object\s*>", "Java Object"),
    Rule("java.raw-type", "dynamic_type", "java",
         r"\b(?:List|Map|Set|Collection|HashMap|ArrayList)\s+(?!<)\w+\s+[=;)]", "Java 裸泛型类型", "warn"),
    Rule("kt.any", "dynamic_type", "kotlin",
         r":\s*Any\s*\??\b|\bAny\s*\??\s*(?=[,)\]])", "Kotlin Any"),
    Rule("cs.object", "dynamic_type", "csharp",
         r"\bobject\b(?!\s*\[\])|\bdynamic\b", "C# object/dynamic"),

    # ===== Ruby / PHP 兜底（动态语言：靠注释/签名缺失信号）=====
    Rule("rb.untyped", "dynamic_type", "ruby",
         r"#\s*@param\s+\w+\s*$|#\s*@return\s*$", "Ruby YARD 注释缺类型", "warn"),
    Rule("php.mixed", "dynamic_type", "php",
         r":\s*mixed\b|\bmixed\s+\$", "PHP mixed 类型"),

    # ===== 双轨/兼容层（最小完整变更，coding-rules-common §8）=====
    # 合法兼容层必须已在 change-contract Open 段登记并用 purity-exempt 留痕豁免；
    # 存量走 baseline 只卡新增/改到的文件。
    Rule("dual.legacy-suffix", "dual_track", "*",
         r"\b(?:class|struct|def|func|fn|function)\s+\w*?(?:Legacy|Compat|Deprecated)\w*",
         "Legacy/Compat 命名的旁路实现（双轨信号；已登记豁免的除外）"),
    Rule("dual.legacy-branch", "dual_track", "*",
         r"if\s+\(?\s*(?:legacy|use[_ ]?old|old[_ ]?(?:version|impl|path|api)|compat(?:ibility)?[_ ]?mode|backward[_ ]?compat)\w*",
         "legacy/compat 运行时兼容分支"),
    Rule("dual.compat-comment", "dual_track", "*",
         r"(?:兼容层|向后兼容|旧版兼容|过渡方案|过渡期|兼容旧)[^\n]{0,60}"
         r"|(?:#|//)\s*(?:backward[- ]?compat(?:ibility)?|legacy (?:support|path|code)|kept for compat)[^\n]{0,60}",
         "兼容/过渡意图注释（双轨信号）", "warn"),
]

VALID_CATEGORIES = {"fake_impl", "dynamic_type", "dual_track"}
VALID_LANGS = set(DEFAULT_EXTS.values()) | {"*"}


def compile_rules(rules: list[Rule]) -> list[tuple[Rule, re.Pattern]]:
    out: list[tuple[Rule, re.Pattern]] = []
    for r in rules:
        try:
            out.append((r, re.compile(r.pattern, re.I)))
        except re.error as e:
            print(f"[rules] 跳过非法规则 {r.id}: {e}", file=sys.stderr)
    return out


def load_extra_rules(path: str) -> list[Rule]:
    if not path:
        return []
    p = Path(path).resolve()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[rules] 读取自定义规则失败：{p}（{e}）", file=sys.stderr)
        return []
    seq = data.get("rules", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    extra: list[Rule] = []
    for obj in seq:
        if not isinstance(obj, dict) or not all(k in obj for k in ("id", "pattern", "desc")):
            continue
        extra.append(Rule(
            id=str(obj["id"]), category=str(obj.get("category", "dynamic_type")),
            lang=str(obj.get("lang", "*")), pattern=str(obj["pattern"]),
            desc=str(obj["desc"]), severity=str(obj.get("severity", "error")),
        ))
    return extra


@dataclass(frozen=True)
class Hit:
    category: str
    file: str
    line: int
    text: str
    rule: str          # 规则描述
    rule_id: str       # 规则 id（基线指纹用）
    severity: str
    exempt: str = ""   # 非空=已豁免（附理由）

    @property
    def fingerprint(self) -> str:
        raw = f"{self.file}:{self.line}:{self.rule_id}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


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


def scan_file(path: Path, root: Path, lang: str, compiled: list[tuple[Rule, re.Pattern]],
              allow: list[re.Pattern], fname_re: re.Pattern) -> list[Hit]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    f_exempt = file_level_exempt(lines)
    rel = path.relative_to(root).as_posix()
    hits: list[Hit] = []
    block_exempt = ""
    fname_hit = bool(fname_re.search(path.name))

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if EXEMPT_END.search(line):
            block_exempt = ""
        begin = EXEMPT_BEGIN.search(line)
        if begin:
            block_exempt = begin.group(1).strip()
        exempt = f_exempt or block_exempt or (EXEMPT_INLINE.search(line).group(1).strip()
                                              if EXEMPT_INLINE.search(line) else "")

        if any(p.search(line) for p in allow):
            continue

        if fname_hit and i == 1:
            hits.append(Hit("fake_impl", rel, 1, f"文件名信号：{path.name}",
                            "fake.filename", "fake.filename", "warn", exempt))

        for rule, pattern in compiled:
            if rule.id == "fake.filename":
                continue  # 文件名单独处理
            if rule.lang not in ("*", lang):
                continue
            if pattern.search(line):
                hits.append(Hit(rule.category, rel, i, stripped[:120],
                                rule.desc, rule.id, rule.severity, exempt))
    return hits


def scan(root: Path, exts: set[str], lang_filter: str,
         compiled: list[tuple[Rule, re.Pattern]], allow_patterns: list[str],
         fname_re: re.Pattern) -> list[Hit]:
    allow = [re.compile(p) for p in allow_patterns]
    hits: list[Hit] = []
    for f in iter_source(root, exts):
        lang = DEFAULT_EXTS.get(f.suffix, "")
        if lang_filter and lang != lang_filter:
            continue
        hits.extend(scan_file(f, root, lang, compiled, allow, fname_re))
    return hits


def merge_intent_gaps(hits: list[Hit], root: Path, lang_filter: str) -> list[Hit]:
    """合并函数级语义扫描（未解释占位/未使用参数）。intent_gaps 不可用则静默跳过，不阻断主门禁。"""
    try:
        import intent_gaps
    except ImportError:
        print("[intent] intent_gaps.py 不在同目录，跳过函数级语义扫描。", file=sys.stderr)
        return hits
    try:
        ihits = intent_gaps.scan(root, lang_filter)
    except Exception as e:  # 语义分析失败不应打断行级门禁
        print(f"[intent] 语义扫描跳过（{e}）。", file=sys.stderr)
        return hits
    for ih in ihits:
        hits.append(Hit(
            category=ih.category, file=ih.file, line=ih.line, text=ih.text,
            rule=ih.rule, rule_id=ih.rule_id, severity=ih.severity, exempt=ih.exempt,
        ))
    return hits


# ---------- 基线 ----------

def load_baseline(path: str) -> dict[str, dict]:
    p = Path(path).resolve()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        items = data.get("entries", {}) if isinstance(data, dict) else {}
        return items if isinstance(items, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_baseline(path: str, hits: list[Hit], root: Path) -> None:
    entries = {h.fingerprint: {"file": h.file, "line": h.line, "rule_id": h.rule_id,
                               "rule": h.rule, "text": h.text} for h in hits}
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"version": 1, "project": str(root), "entries": entries},
                            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_scope(path: str) -> set[str]:
    """--scope 文件：每行一个相对路径（配合 git diff --name-only），或逗号分隔的参数本身。"""
    if not path:
        return set()
    p = Path(path)
    if p.is_file():
        raw = p.read_text(encoding="utf-8", errors="replace")
        return {ln.strip().lstrip("+-").strip() for ln in raw.splitlines() if ln.strip()}
    return {x.strip() for x in path.split(",") if x.strip()}


def split_hits(hits: list[Hit], baseline: dict[str, dict], scope: set[str]):
    """分为：新增未豁免（卡门禁）、存量（基线内）、已豁免、warn。
    重构语义：存量里被 --scope 标记的改动文件 = 需负责（升级为卡门禁的新增）。"""
    fresh_blocking: list[Hit] = []
    legacy: list[Hit] = []
    exempted: list[Hit] = []
    warns: list[Hit] = []
    for h in hits:
        if h.exempt:
            exempted.append(h)
        elif h.severity == "warn":
            warns.append(h)
        elif h.fingerprint in baseline:
            if scope and h.file in scope:
                fresh_blocking.append(h)   # 改到的文件里的存量 = 本次需负责
            else:
                legacy.append(h)
        else:
            fresh_blocking.append(h)       # 真新增
    return fresh_blocking, legacy, exempted, warns


# ---------- 输出 ----------

def build_rules(rules_json: str, disable: list[str]) -> list[Rule]:
    rules = [r for r in BUILTIN_RULES if r.id not in disable]
    if rules_json:
        rules += [r for r in load_extra_rules(rules_json) if r.id not in disable]
    return rules


def print_report(root: Path, fresh: list[Hit], legacy: list[Hit], exempted: list[Hit],
                 warns: list[Hit], baseline_on: bool, scope_on: bool) -> None:
    print(f"# 源码纯净扫描（{root}）\n")
    print(f"- 新增/本次需处理（卡门禁）：{len(fresh)}")
    if baseline_on:
        print(f"- 存量（基线内，暂不卡；改到的文件才需负责）：{len(legacy)}")
    print(f"- 已豁免：{len(exempted)} · warn 提示：{len(warns)}")

    def section(title: str, items: list[Hit], show_reason: bool = False) -> None:
        if not items:
            return
        print(f"\n## {title}（{len(items)}）")
        for h in items[:60]:
            extra = f" — 理由：{h.exempt}" if show_reason and h.exempt else ""
            print(f"- [{h.rule_id}] `{h.file}:{h.line}` — {h.text}{extra}")
        if len(items) > 60:
            print(f"- ... 另 {len(items) - 60} 条")

    section("新增污染（必须处理）", fresh)
    if baseline_on:
        section("存量 TODO（基线内，未改到的文件可暂缓）", legacy)
    section("warn 提示（核对后决定是否豁免）", warns)
    section("已豁免（需在 overview 登记理由）", exempted, show_reason=True)

    if not (fresh or legacy or exempted or warns):
        print("\n未检出污染信号。仍需人工核对：真实 adapter 是否连真基础设施、跨进程契约与副作用。")
    print("\n> 处理：fake 实现移到 tests/、src/ 只留生产级真实 adapter；"
          "动态类型改具名别名/具体类型；占位写清依赖谁/谁补/何时接入；"
          "未用参数写清给谁用/是否预留；确需保留的按 purity-exempt 写理由（≥4 字符）。")
    print("> 存量代码：先 `baseline` 快照，重构改到哪个文件才处理哪个文件的存量（禁扩大 diff）。")
    print("> 退出码 0 = 草稿/核对；`--strict` 下有新增/本次需处理命中则 1 = 禁止进 review / 标完成。")


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 源码纯净门禁（数据驱动规则库 + 存量基线）")
    sub = ap.add_subparsers(dest="cmd")

    def add_common(sp):
        sp.add_argument("--path", default="src", help="生产源码根路径")
        sp.add_argument("--lang", default="", choices=sorted(VALID_LANGS - {"*"}), help="只扫某语言")
        sp.add_argument("--exts", default="", help="覆盖扩展名，逗号分隔")
        sp.add_argument("--rules", default="", help="自定义规则 JSON（追加到内置规则库）")
        sp.add_argument("--disable-rule", action="append", default=[], help="禁用某规则 id（可重复）")
        sp.add_argument("--allow-pattern", action="append", default=[], help="行内正则命中即放行（可重复）")
        sp.add_argument("--no-intent", action="store_true", help="跳过函数级语义扫描（未解释占位/未使用参数）")

    p_scan = sub.add_parser("scan", help="扫描当前源码污染")
    add_common(p_scan)
    p_scan.add_argument("--format", default="text", choices=("text", "json"))
    p_scan.add_argument("--strict", action="store_true", help="有未豁免命中即退出 1（不区分存量）")

    p_base = sub.add_parser("baseline", help="把当前命中快照为存量基线")
    add_common(p_base)
    p_base.add_argument("--out", default=DEFAULT_BASELINE, help="基线文件路径")

    p_check = sub.add_parser("check", help="门禁：只卡新增（相对基线），存量出 TODO")
    add_common(p_check)
    p_check.add_argument("--baseline", default=DEFAULT_BASELINE, help="基线文件（不存在则全部算新增）")
    p_check.add_argument("--scope", default="", help="改动文件列表（文件或逗号分隔）；其中的存量升级为需处理")
    p_check.add_argument("--format", default="text", choices=("text", "json"))
    p_check.add_argument("--strict", action="store_true", help="有新增/本次需处理命中则退出 1")

    p_rules = sub.add_parser("rules", help="列出当前生效规则")
    p_rules.add_argument("--lang", default="")
    p_rules.add_argument("--rules", default="")
    p_rules.add_argument("--disable-rule", action="append", default=[])

    # 兼容旧调用：无子命令时按 scan 处理
    if len(sys.argv) > 1 and sys.argv[1] not in ("scan", "baseline", "check", "rules", "-h", "--help"):
        sys.argv.insert(1, "scan")
    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0

    rules = build_rules(getattr(args, "rules", ""), getattr(args, "disable_rule", []))
    compiled = compile_rules(rules)
    fname_re = next((re.compile(r.pattern, re.I) for r in rules if r.id == "fake.filename"),
                    re.compile(r"(?!x)x"))

    if args.cmd == "rules":
        print(f"# 生效规则（{len(rules)} 条）\n")
        for r in rules:
            if args.lang and r.lang not in ("*", args.lang):
                continue
            print(f"- `{r.id}` [{r.category}/{r.lang}/{r.severity}] {r.desc}")
        return 0

    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"FAIL — 源码目录不存在：{root}")
        return 1
    exts = ({e.strip() for e in args.exts.split(",") if e.strip()} if args.exts
            else set(DEFAULT_EXTS))
    hits = scan(root, exts, args.lang, compiled, getattr(args, "allow_pattern", []), fname_re)
    if not getattr(args, "no_intent", False):
        hits = merge_intent_gaps(hits, root, args.lang)

    if args.cmd == "baseline":
        save_baseline(args.out, hits, root)
        print(f"# 存量基线已写入\n- 文件：`{Path(args.out).resolve()}`")
        print(f"- 记录命中：{len(hits)}（其中已豁免 {sum(1 for h in hits if h.exempt)}）")
        print("> 之后 `check --strict` 只卡新增；重构改到某文件时用 --scope 让其存量进入负责范围。")
        return 0

    if args.cmd == "scan":
        unexempt = [h for h in hits if not h.exempt]
        blocking = [h for h in unexempt if h.severity == "error"]
        warns = [h for h in hits if h.severity == "warn" and not h.exempt]
        exempted = [h for h in hits if h.exempt]
        if args.format == "json":
            print(json.dumps({"hits": [asdict(h) for h in hits],
                              "blocking_count": len(blocking), "unexempt_count": len(unexempt),
                              "exempted_count": len(exempted)}, ensure_ascii=False, indent=2))
            return 1 if (args.strict and blocking) else 0
        print_report(root, blocking, [], exempted, warns, baseline_on=False, scope_on=False)
        return 1 if (args.strict and blocking) else 0

    # check：相对基线
    baseline = load_baseline(args.baseline)
    scope = load_scope(args.scope)
    fresh, legacy, exempted, warns = split_hits(hits, baseline, scope)
    blocking = [h for h in fresh if h.severity == "error"]
    if args.format == "json":
        print(json.dumps({"new_blocking": [asdict(h) for h in blocking],
                          "new_blocking_count": len(blocking),
                          "legacy_count": len(legacy), "exempted_count": len(exempted),
                          "warn_count": len(warns)}, ensure_ascii=False, indent=2))
        return 1 if (args.strict and blocking) else 0
    print_report(root, blocking, legacy, exempted, warns, baseline_on=True, scope_on=bool(scope))
    return 1 if (args.strict and blocking) else 0


if __name__ == "__main__":
    sys.exit(main())
