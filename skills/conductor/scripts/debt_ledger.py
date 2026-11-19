#!/usr/bin/env python3
"""技术债台账：扫描源码债标记，聚合成可量化的债清单草稿（S4/S5 收尾与排期用）。

债标记与权重（见 WEIGHTS）：FIXME/SAFETY=3、HACK/XXX=2、TODO/DEBT=1。
按类型和文件分组，算「债指数」（权重和）与热点文件，给优先级建议。
目的：把散落的 TODO/FIXME 与 overview 未完成项收敛成台账，避免以"技术债"名义静默放行。

定位：启发式草稿，需人工核对影响面；不改代码、不判定能否放行。
输出 md（默认）或 json（--format）；退出码恒 0，--fail-over <N> 超阈值返回 1（CI 卡口）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_EXTS = ".py,.ts,.tsx,.js,.jsx,.vue,.go,.rs,.dart"
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build",
             "tmp", ".agents", "output", "overviews"}
WEIGHTS = {"TODO": 1, "DEBT": 1, "FIXME": 3, "SAFETY": 3, "HACK": 2, "XXX": 2}


@dataclass(frozen=True)
class DebtItem:
    kind: str
    file: str
    line: int
    text: str
    weight: int


def marker_regex(kinds: list[str]) -> re.Pattern[str]:
    return re.compile(r"\b(" + "|".join(map(re.escape, kinds)) + r")\b\s*[:：]?\s*(.*)")


def iter_source(root: Path, exts: set[str]) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in exts:
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in p.parts):
            continue
        out.append(p)
    return out


def scan(root: Path, exts: set[str], kinds: list[str]) -> list[DebtItem]:
    rx = marker_regex(kinds)
    items: list[DebtItem] = []
    for f in iter_source(root, exts):
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(f.relative_to(root))
        for i, line in enumerate(lines, start=1):
            m = rx.search(line)
            if not m:
                continue
            kind = m.group(1).upper()
            note = m.group(2).strip()[:100] or "(无说明)"
            items.append(DebtItem(kind, rel, i, note, WEIGHTS.get(kind, 1)))
    return items


def render_md(items: list[DebtItem], root: Path) -> str:
    index = sum(i.weight for i in items)
    by_kind = Counter(i.kind for i in items)
    by_file = Counter(i.file for i in items)
    lines = [f"# 技术债台账草稿（{root}）", ""]
    lines.append(f"债指数：**{index}**（条目 {len(items)}）")
    lines.append("类型分布：" + "、".join(f"{k} {v}" for k, v in by_kind.most_common()) + "")
    lines.append("")
    lines.append("## 热点文件（债最多）")
    if by_file:
        for f, n in by_file.most_common(10):
            lines.append(f"- {f} — {n} 条")
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 债条目（逐条核对影响面与优先级）")
    if not items:
        lines.append("- 未发现债标记（仍可能有未标记的技术债，需人工核对）")
    else:
        for kind in sorted(items, key=lambda x: (-x.weight, x.file, x.line)):
            lines.append(f"- `{kind.file}:{kind.line}` — **{kind.kind}**（权重{kind.weight}） {kind.text}")
    lines.append("")
    lines.append("> 草稿仅供核对：标记≠已登记。影响面/优先级/是否放行需人工判定并写入 overview「未完成项」。")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 技术债台账（草稿）")
    ap.add_argument("--path", default=".", help="源码根路径")
    ap.add_argument("--exts", default=DEFAULT_EXTS, help="扫描扩展名，逗号分隔")
    ap.add_argument("--kinds", default=",".join(WEIGHTS), help="债标记，逗号分隔")
    ap.add_argument("--format", choices=("md", "json"), default="md", help="输出格式")
    ap.add_argument("--fail-over", type=int, default=-1,
                    help="债指数超过该值返回 1（CI 卡口）；默认 -1 不卡")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    exts = {e.strip() for e in args.exts.split(",") if e.strip()}
    kinds = [k.strip().upper() for k in args.kinds.split(",") if k.strip()]
    items = scan(root, exts, kinds)
    index = sum(i.weight for i in items)

    if args.format == "json":
        print(json.dumps({
            "root": str(root),
            "index": index,
            "count": len(items),
            "by_kind": dict(Counter(i.kind for i in items)),
            "items": [asdict(i) for i in items],
        }, ensure_ascii=False, indent=2))
    else:
        print(render_md(items, root))

    if args.fail_over >= 0 and index > args.fail_over:
        print(f"\n[债指数 {index} > 阈值 {args.fail_over}]", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
