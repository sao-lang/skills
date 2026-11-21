#!/usr/bin/env python3
"""承诺台账（通用防漏引擎）：把任意场景里"隐含的待办承诺"外置成机器可校验的台账。

核心认知：不管什么场景，"漏东西"的本质相同——输入里隐含的承诺没有被逐条勾销。
开发的承诺=规格每条需求；重构=每个模块等价；解 bug=每个症状+回归；文档同步=每处差异；
审查=每个 finding。本脚本是统一引擎，migration_ledger.py 是它在重构场景的兼容 shim。

防膨胀纪律（重要）：
  1. 机器能扫的绝不让人填——模块来自源码扫描，条目来自已有文档/脚本输出。
  2. 门禁只卡三个公共出口（S0 采集 / S4 核证据 / S5 放行），不插到每一步。
  3. 允许显式豁免但留痕——skipped 必须填 reason，禁止伪装成 verified。

四个子命令：
  init   采集：从一个/多个来源把承诺 harvest 进台账（增量合并，保留已填状态与证据）。
  next   断点：输出下一批待办（in_progress 优先，模块按依赖层序）。
  check  闸门：校验收口——pending/in_progress/verified 无证据/skipped 无理由/drift。
  show   概览：打印台账全部条目与状态（人工核对用）。

采集来源（可叠加，均幂等；来源名写入每条 source 字段，便于分源 drift 核对）：
  --from-modules PATH   扫源码文件→模块承诺（kind=entry/route/module/config，deps 弱信号）
  --from-list FILE      解析 md/txt 的列表项（- / * / 1. / - [ ] / - [x]）→条目承诺
  --from-json FILE      JSON 数组或 {items:[...]} →承诺（id 必填）
  --stdin               从管道读 JSON 或每行一条（供 impact_analysis.py / scan_gaps.py / review 输出灌入）
  --manual "a,b,c"      直接给若干条（逗号分隔）

退出码：init/next/show 恒 0；check 默认 0（草稿核对），check --strict 有缺口则 1（收尾门禁）。
哲学同 scan_gaps/review_gate：脚本给草稿+机器判定，人工核实与语义判断归人/AI。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from overview_path import ensure_ignore

DEFAULT_LEDGER = ".commitment-ledger.json"
VERSION = 1

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "tests", "test",
             "tmp", ".agents", "overviews", "dist", "build", ".mypy_cache", ".pytest_cache"}
DEFAULT_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".go", ".rs",
                ".java", ".dart", ".rb", ".php", ".c", ".cpp", ".h")

ENTRY_FILENAMES = re.compile(r"^(main|index|app|server|cli|__main__|bootstrap|entry)\.\w+$", re.I)
ENTRY_CONTENT = re.compile(
    r'if\s+__name__\s*==\s*["\']__main__["\']'
    r'|func\s+main\s*\(|fn\s+main\s*\('
    r'|export\s+default\b|\bnew\s+Vue\s*\(|\bcreateApp\s*\('
)
ROUTE_CONTENT = re.compile(
    r'@(?:app|router|bp|blueprint)\.(?:get|post|put|delete|patch|route)\b'
    r'|\b(?:app|router)\.(?:get|post|put|delete|patch)\s*\('
    r'@(?:Get|Post|Put|Delete|Patch)Mapping\b|routes?\s*[:=]\s*\['
)
IMPORT_PATTERNS = (
    re.compile(r'^\s*(?:from)\s+([\w.]+)\s+import\b', re.M),
    re.compile(r'^\s*(?:import)\s+([\w.]+)', re.M),
    re.compile(r'^\s*import\s+["\']([\w./\-@]+)["\']', re.M),
    re.compile(r'^\s*const\s+\w+\s*=\s*require\(["\']([\w./\-@]+)["\']\)', re.M),
)
STDLIB_PREFIX = {"os", "sys", "re", "json", "typing", "pathlib", "time", "datetime",
                 "collections", "itertools", "functools", "dataclasses", "argparse",
                 "logging", "math", "random", "string", "io", "abc", "enum", "uuid", "hashlib"}

VALID_STATUS = {"pending", "in_progress", "verified", "skipped"}
SOURCE_MODULE = "module"


# ---------- 通用工具 ----------

def iter_source(root: Path, exts: set[str]) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or (p.suffix and p.suffix not in exts):
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS or part.startswith(".") for part in rel_parts):
            continue
        files.append(p)
    return sorted(files)


def parse_exts(s: str) -> set[str]:
    return {e.strip() for e in s.split(",") if e.strip()}


def load_ledger(path: Path) -> dict | None:
    """读取台账；兼容旧完整格式与新紧凑格式，读时补齐默认字段。"""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        return None
    items: dict[str, dict] = {}
    for cid, raw in data["items"].items():
        if not isinstance(raw, dict):
            continue
        full = new_item(cid, raw.get("source", ""), raw.get("kind", "task"),
                        list(raw.get("deps", [])))
        full.update(raw)
        full["id"] = cid
        items[cid] = full
    return {
        "version": data.get("v", data.get("version", VERSION)),
        "project": data.get("project", ""),
        "items": items,
    }


def save_ledger(path: Path, items: dict[str, dict], project: str) -> None:
    """最小持久化：紧凑 JSON，省略空字段/重复 id/pending 默认状态。"""
    compact: dict[str, dict] = {}
    for cid, it in items.items():
        d = {k: v for k, v in it.items()
             if k != "id" and v not in ("", [], None)}
        if d.get("status") == "pending":
            d.pop("status", None)
        compact[cid] = d
    data: dict = {"v": VERSION, "items": compact}
    if project:
        data["project"] = project
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
                    encoding="utf-8")
    ensure_ignore(path.parent)


def new_item(cid: str, source: str, kind: str = "task", deps: list[str] | None = None) -> dict:
    return {"id": cid, "source": source, "kind": kind, "status": "pending",
            "deps": deps or [], "checkpoint": "", "evidence": "", "reason": "", "note": ""}


# ---------- 采集器（机器能扫的自动扫） ----------

def scan_modules(root: Path, exts: set[str], max_deps: int) -> dict[str, dict]:
    """扫源码→模块承诺（重构/迁移场景）。这是 migration_ledger 复用的核心。"""
    items: dict[str, dict] = {}
    for f in iter_source(root, exts):
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rid = f.relative_to(root).as_posix()
        if ENTRY_FILENAMES.match(f.name) or ENTRY_CONTENT.search(text):
            kind = "entry"
        elif ROUTE_CONTENT.search(text):
            kind = "route"
        elif f.suffix in {".yaml", ".yml", ".json", ".toml", ".ini", ".env"} or "config" in f.name.lower():
            kind = "config"
        else:
            kind = "module"
        deps: set[str] = set()
        for pat in IMPORT_PATTERNS:
            for m in pat.finditer(text):
                dep = m.group(1)
                if dep and dep.split(".")[0] not in STDLIB_PREFIX:
                    deps.add(dep)
        items[rid] = new_item(rid, SOURCE_MODULE, kind, sorted(deps)[:max_deps])
    return items


LIST_ITEM_RE = re.compile(r'^\s*(?:[-*+]\s+(?:\[[ xX]\]\s*)?|\d+[.)]\s+)(.+?)\s*$')


def parse_list_file(path: Path, source: str, kind: str, id_prefix: str = "") -> dict[str, dict]:
    """解析 md/txt 列表项→承诺。规格条目、finding、缺口、TODO 清单都适用。"""
    items: dict[str, dict] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return items
    for ln in lines:
        m = LIST_ITEM_RE.match(ln)
        if not m:
            continue
        text = m.group(1).strip()
        # 过滤结构噪声：过短、纯符号、明显的分隔/标题残留
        if len(text) < 4 or set(text) <= set("-#*:| "):
            continue
        text = re.sub(r'[`*_]{1,3}', '', text).strip()
        fingerprint = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        cid = f"{id_prefix}{fingerprint}:{text[:48]}"
        items[cid] = new_item(cid, source, kind)
    return items


def normalize_json_items(data, source: str, kind: str) -> dict[str, dict]:
    """接受 JSON 数组或 {items:[...]}；每条须有 id（字符串化），可选 source/kind/deps。"""
    items: dict[str, dict] = {}
    if isinstance(data, dict):
        seq = data.get("items", [])
    elif isinstance(data, list):
        seq = data
    else:
        return items
    if not isinstance(seq, list):
        return items
    for obj in seq:
        if not isinstance(obj, dict) or "id" not in obj:
            continue
        cid = str(obj["id"])
        it = new_item(cid, str(obj.get("source", source)), str(obj.get("kind", kind)),
                      list(obj.get("deps", [])) if isinstance(obj.get("deps", []), list) else [])
        for f in ("status", "checkpoint", "evidence", "reason", "note"):
            if f in obj:
                it[f] = str(obj[f])
        if it["status"] not in VALID_STATUS:
            it["status"] = "pending"
        items[cid] = it
    return items


def harvest(args, ledger_path: Path) -> tuple[dict[str, dict], list[str]]:
    """从所有指定来源采集，返回 (新条目集合, 本次采集的来源列表)。"""
    gathered: dict[str, dict] = {}
    sources: list[str] = []
    exts = parse_exts(args.exts)

    if args.from_modules:
        root = Path(args.from_modules).resolve()
        gathered.update(scan_modules(root, exts, args.max_deps))
        sources.append(f"modules:{root}")

    if args.from_list:
        for spec in args.from_list.split(","):
            spec = spec.strip()
            if not spec:
                continue
            # 允许 file::kind 指定语义类型
            fp, _, k = spec.partition("::")
            kind = k or args.list_kind
            p = Path(fp).resolve()
            gathered.update(parse_list_file(p, args.list_source, kind, args.id_prefix))
            sources.append(f"list:{p}")

    if args.from_json:
        for fp in args.from_json.split(","):
            fp = fp.strip()
            if not fp:
                continue
            p = Path(fp).resolve()
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            gathered.update(normalize_json_items(data, args.json_source, args.json_kind))
            sources.append(f"json:{p}")

    if args.stdin:
        raw = sys.stdin.read().strip()
        if raw:
            parsed = None
            if raw.startswith(("[", "{")):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
            if parsed is not None:
                gathered.update(normalize_json_items(parsed, args.stdin_source, args.stdin_kind))
            else:
                for ln in raw.splitlines():
                    t = ln.strip().lstrip("-* ").strip()
                    if not t:
                        continue
                    it = new_item(t, args.stdin_source, args.stdin_kind)
                    gathered[t] = it
            sources.append("stdin")

    if args.manual:
        for t in [x.strip() for x in args.manual.split(",") if x.strip()]:
            it = new_item(t, "manual", args.manual_kind)
            gathered[t] = it
        sources.append("manual")

    return gathered, sources


def merge_items(ledger: dict | None, gathered: dict[str, dict], sources: list[str]) -> tuple[dict[str, dict], list[str], int, list[str]]:
    """增量合并：已存在的 id 保留人工/AI 填写的状态与证据；新增 id 进台账。
    对本次涉及的每个来源做分源 drift：该来源旧条目本次未采集到→标 STALE。"""
    old: dict[str, dict] = ledger.get("items", {}) if ledger else {}
    merged: dict[str, dict] = {}
    added: list[str] = []
    kept = 0

    for cid, fresh in gathered.items():
        if cid in old:
            prev = dict(old[cid])
            for f in ("status", "checkpoint", "evidence", "reason", "note"):
                fresh[f] = prev.get(f, fresh[f])
            fresh["note"] = re.sub(r"\s*\[STALE:[^\]]*\]", "", fresh.get("note", "")).strip()
            kept += 1
        else:
            added.append(cid)
        merged[cid] = fresh

    # 分源 drift：仅对本次采集的来源标记其"消失"的旧条目
    src_names = {s.split(":")[0] for s in sources}
    for cid, prev in old.items():
        src = prev.get("source", "")
        src_key = src.split(":")[0]
        if cid not in gathered:
            if src == SOURCE_MODULE and "modules" in src_names:
                p = dict(prev)
                p["note"] = (re.sub(r"\s*\[STALE:[^\]]*\]", "", p.get("note", "")).strip()
                             + " [STALE: 本次未扫描到，核实是否已删除/改名]").strip()
                merged[cid] = p
            elif src_key in src_names and src_names & {"list", "json", "stdin", "manual"}:
                # 非模块来源的消失条目同样保留并标记（来源名精确匹配时）
                if any(s.startswith(src_key + ":") or s == src_key for s in sources) or src_key in src_names:
                    p = dict(prev)
                    p["note"] = (re.sub(r"\s*\[STALE:[^\]]*\]", "", p.get("note", "")).strip()
                                 + " [STALE: 本次来源未再列出，核实是否已完成/删除]").strip()
                    merged[cid] = p
            else:
                merged[cid] = dict(prev)

    return merged, added, kept, sources


# ---------- 证据校验 / 门禁 ----------

def evidence_ok(evidence: str, ledger_dir: Path) -> tuple[bool, str]:
    if not evidence or not evidence.strip():
        return False, "evidence 为空"
    e = evidence.strip()
    if e.startswith("report:"):
        rp = Path(e[len("report:"):].strip())
        target = rp if rp.is_absolute() else (ledger_dir / rp)
        if not target.is_file():
            return False, f"报告文件不存在：{target}"
        return True, "报告文件存在"
    if re.search(r"exit\s*0|退出码\s*0|passed|PASS|通过\s*\d|\:\d+", e, re.I):
        return True, "含可核对线索"
    return False, "证据无可核对线索（需含 exit 0 / 通过数 / 文件:行号，或 report: 路径）"


def check_items(items: dict[str, dict], ledger_dir: Path, modules_path: str = "",
                exts: str = "", max_deps: int = 20) -> dict:
    """返回门禁结论的结构化结果（migration shim 与 check 命令共用）。"""
    counts = {s: 0 for s in VALID_STATUS}
    bad_status: list[str] = []
    for cid, it in items.items():
        st = it.get("status", "pending")
        if st in counts:
            counts[st] += 1
        else:
            bad_status.append(f"{cid}: 非法状态 {st}")

    fails: list[str] = list(bad_status)
    pending = sorted(c for c, it in items.items() if it.get("status") == "pending")
    inprog = sorted(c for c, it in items.items() if it.get("status") == "in_progress")
    if pending:
        fails.append(f"仍有 {len(pending)} 项 pending（未勾销承诺）")
    if inprog:
        fails.append(f"仍有 {len(inprog)} 项 in_progress（中断未收口）")

    for cid, it in items.items():
        if it.get("status") == "verified":
            ok, why = evidence_ok(it.get("evidence", ""), ledger_dir)
            if not ok:
                fails.append(f"verified 无有效证据：{cid}（{why}）")
        if it.get("status") == "skipped" and not str(it.get("reason", "")).strip():
            fails.append(f"skipped 无理由：{cid}")

    drift: list[str] = []
    if modules_path:
        root = Path(modules_path).resolve()
        if root.is_dir():
            scanned = set(scan_modules(root, parse_exts(exts), max_deps))
            tracked = {c for c, it in items.items() if it.get("source") == SOURCE_MODULE}
            drift = sorted(scanned - tracked)
            if drift:
                fails.append(f"发现 {len(drift)} 个模块未进台账（drift，重跑 init --from-modules --merge）")

    total = len(items)
    done = counts["verified"] + counts["skipped"]
    pct = (100 * done / total) if total else 100
    return {"ok": not fails, "fails": fails, "counts": counts, "pending": pending,
            "in_progress": inprog, "drift": drift, "total": total, "done": done, "pct": pct}


def print_check_report(ledger: Path, r: dict) -> None:
    c = r["counts"]
    print("# 承诺台账门禁\n")
    print(f"- 台账：`{ledger}`")
    print(f"- 进度：{r['done']}/{r['total']} 收口（{r['pct']:.0f}%）— "
          + "，".join(f"{s} {c[s]}" for s in ("verified", "skipped", "in_progress", "pending")))
    if r["pending"]:
        print("\n## 待勾销（pending）")
        for cid in r["pending"][:40]:
            print(f"- {cid}")
        if len(r["pending"]) > 40:
            print(f"- ... 另 {len(r['pending']) - 40} 条")
    if r["in_progress"]:
        print("\n## 中断待续（in_progress）")
        for cid in r["in_progress"]:
            print(f"- {cid}")
    if r["fails"]:
        print("\n## 门禁缺口")
        for f in r["fails"][:50]:
            print(f"- FAIL — {f}")
        if len(r["fails"]) > 50:
            print(f"- ... 另 {len(r['fails']) - 50} 条")
    else:
        print("\nPASS — 台账全部收口，每项有证据或理由，无漏登记。")
    print("\n> 退出码 0 = 草稿/核对；`--strict` 下有缺口则 1 = 禁止 finish / 标完成。")


# ---------- 排序（断点续接） ----------

def topo_order(items: dict[str, dict]) -> list[tuple[str, dict]]:
    def local_dep(dep: str, path: str) -> str | None:
        stem = Path(path).stem
        if dep.endswith("." + stem) or dep == stem:
            return None
        dotted = dep.replace(".", "/")
        candidates = [dotted + e for e in DEFAULT_EXTS] + [dep + e for e in DEFAULT_EXTS]
        for cand in candidates:
            if cand in items:
                return cand
        for cand in candidates:
            hits = [p for p in items if p == cand or p.endswith("/" + cand)]
            if len(hits) == 1:
                return hits[0]
        return None

    indeg = {r: 0 for r in items}
    adj: dict[str, list[str]] = {r: [] for r in items}
    for r, it in items.items():
        if it.get("source") != SOURCE_MODULE:
            continue
        for d in it.get("deps", []):
            target = local_dep(d, r)
            if target and target in items:
                adj[target].append(r)
                indeg[r] += 1
    remaining = dict(indeg)
    queue = sorted(r for r, n in remaining.items() if n == 0)
    ordered: list[str] = []
    while queue:
        cur = queue.pop(0)
        ordered.append(cur)
        for nxt in adj.get(cur, []):
            remaining[nxt] -= 1
            if remaining[nxt] == 0:
                queue.append(nxt)
        queue.sort()
    for r in items:
        if r not in ordered:
            ordered.append(r)
    # in_progress 优先（断点续接），其余保持层序
    ordered.sort(key=lambda r: 0 if items[r].get("status") == "in_progress" else 1)
    return [(r, items[r]) for r in ordered]


# ---------- 命令 ----------

def cmd_init(args) -> int:
    ledger = Path(args.ledger)
    old = load_ledger(ledger)
    gathered, sources = harvest(args, ledger)
    if not sources:
        print("FAIL — 未指定任何采集来源。用 --from-modules / --from-list / --from-json / --stdin / --manual。")
        return 1
    merged, added, kept, _ = merge_items(old, gathered, sources)
    save_ledger(ledger, merged, args.project or (old.get("project", "") if old else ""))
    root_hint = Path(args.from_modules).resolve() if args.from_modules else ledger.parent
    print(f"# 承诺台账采集（{root_hint}）\n")
    print(f"- 台账文件：`{ledger}`")
    print(f"- 采集来源：{'；'.join(sources)}")
    print(f"- 条目总数：{len(merged)}（新增 {len(added)}，保留已填状态 {kept}）")
    by_src: dict[str, int] = {}
    for it in merged.values():
        by_src[it.get("source", "?")] = by_src.get(it.get("source", "?"), 0) + 1
    print("- 来源分布：" + "，".join(f"{k} {v}" for k, v in sorted(by_src.items())))
    if added:
        print("\n## 新增条目（默认 pending）")
        for cid in sorted(added)[:60]:
            print(f"- {cid}")
        if len(added) > 60:
            print(f"- ... 另 {len(added) - 60} 条")
    print("\n> 台账是唯一事实源。逐项完成后把 status 改 verified 并填 evidence；"
          "换会话先 `next`/`check` 定位断点，不靠记忆。")
    return 0


def cmd_check(args) -> int:
    ledger = Path(args.ledger)
    data = load_ledger(ledger)
    if data is None:
        print(f"FAIL — 台账不存在或格式错误：{ledger}（先跑 init 采集）")
        return 1
    r = check_items(data.get("items", {}), ledger.parent,
                    args.modules or "", args.exts, args.max_deps)
    print_check_report(ledger, r)
    return 1 if (args.strict and not r["ok"]) else 0


def cmd_next(args) -> int:
    ledger = Path(args.ledger)
    data = load_ledger(ledger)
    if data is None:
        print(f"FAIL — 台账不存在或格式错误：{ledger}（先跑 init 采集）")
        return 1
    items = data.get("items", {})
    todo = [(r, it) for r, it in topo_order(items)
            if it.get("status") in ("pending", "in_progress")]
    if not todo:
        print("全部收口，无待办承诺。")
        return 0
    n = args.limit
    print(f"# 下一批待办承诺（共 {len(todo)} 项，取前 {min(n, len(todo))}）\n")
    print("> 模块依赖层序仅为建议（弱信号需核对）；in_progress 断点项优先显示。\n")
    for cid, it in todo[:n]:
        flag = "[中断续接]" if it.get("status") == "in_progress" else ""
        cp = f" — 断点：{it.get('checkpoint')}" if it.get("checkpoint") else ""
        src = f" — 来源：{it.get('source')}"
        print(f"- {cid}（{it.get('kind', 'task')}）{flag}{cp}{src}")
    return 0


def cmd_show(args) -> int:
    ledger = Path(args.ledger)
    data = load_ledger(ledger)
    if data is None:
        print(f"FAIL — 台账不存在或格式错误：{ledger}")
        return 1
    items = data.get("items", {})
    print(f"# 承诺台账全览（{ledger}）\n")
    for st in ("in_progress", "pending", "verified", "skipped"):
        group = [(c, it) for c, it in items.items() if it.get("status") == st]
        if not group:
            continue
        print(f"## {st}（{len(group)}）")
        for cid, it in group:
            extra = ""
            if it.get("evidence"):
                extra += f" — 证据：{it['evidence'][:60]}"
            if it.get("reason"):
                extra += f" — 理由：{it['reason'][:60]}"
            if it.get("note"):
                extra += f" — {it['note'][:60]}"
            print(f"- {cid}（{it.get('source')}/{it.get('kind')}）{extra}")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="conductor 承诺台账（通用防漏引擎）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="采集：多来源 harvest 进台账（增量合并）")
    p_init.add_argument("--ledger", default=DEFAULT_LEDGER)
    p_init.add_argument("--from-modules", default="", help="扫源码→模块承诺")
    p_init.add_argument("--from-list", default="", help="md/txt 列表项→承诺，逗号分隔；可 file::kind")
    p_init.add_argument("--list-source", default="spec", help="--from-list 的 source 名")
    p_init.add_argument("--list-kind", default="spec", help="--from-list 默认 kind")
    p_init.add_argument("--from-json", default="", help="JSON 数组/{items}→承诺，逗号分隔")
    p_init.add_argument("--json-source", default="json")
    p_init.add_argument("--json-kind", default="task")
    p_init.add_argument("--stdin", action="store_true", help="从管道读 JSON 或每行一条")
    p_init.add_argument("--stdin-source", default="impact")
    p_init.add_argument("--stdin-kind", default="impact")
    p_init.add_argument("--manual", default="", help="直接给若干条，逗号分隔")
    p_init.add_argument("--manual-kind", default="task")
    p_init.add_argument("--id-prefix", default="")
    p_init.add_argument("--exts", default=",".join(DEFAULT_EXTS))
    p_init.add_argument("--max-deps", type=int, default=20)
    p_init.add_argument("--project", default="")

    p_check = sub.add_parser("check", help="闸门：校验承诺收口情况")
    p_check.add_argument("--ledger", default=DEFAULT_LEDGER)
    p_check.add_argument("--modules", default="", help="源码根路径（给了才查模块 drift）")
    p_check.add_argument("--exts", default=",".join(DEFAULT_EXTS))
    p_check.add_argument("--max-deps", type=int, default=20)
    p_check.add_argument("--strict", action="store_true", help="有缺口即退出 1（收尾门禁）")

    p_next = sub.add_parser("next", help="断点：输出下一批待办承诺")
    p_next.add_argument("--ledger", default=DEFAULT_LEDGER)
    p_next.add_argument("--limit", type=int, default=5)

    p_show = sub.add_parser("show", help="概览：打印全部承诺与状态")
    p_show.add_argument("--ledger", default=DEFAULT_LEDGER)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return {"init": cmd_init, "check": cmd_check, "next": cmd_next, "show": cmd_show}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
