#!/usr/bin/env python3
"""从 overview 抽取可回写经验草稿；默认 dry-run，不落盘。

用法：
    python learn_capture.py --overview overviews/2026-01-01/abc-demo.md
    python learn_capture.py --overview <path> --out docs/conventions.md --apply

退出码：0 = 草稿生成成功；1 = overview 不存在。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_HINTS = (
    "关键决策", "独立 review 报告", "轻量复核", "未完成项",
    "环境阻断", "问题与状态", "未完成项与下一步",
)
ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")


def extract_items(text: str) -> list[str]:
    items: list[str] = []
    active = False
    for line in text.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            active = any(hint in title for hint in SOURCE_HINTS)
            continue
        m = ITEM_RE.match(line)
        if active and m:
            item = m.group(1).strip()
            if len(item) >= 6 and "待补" not in item:
                items.append(item)
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique[:5]


def build_draft(items: list[str]) -> str:
    if not items:
        return "## 本次 learn 回写\n\n- 本次无新增经验（overview 未抽取到可复用条目）。\n"
    lines = ["## 本次 learn 回写（草稿，需人工确认）", ""]
    for item in items:
        lines.append(f"- [触发条件] {item} → [处理动作] 待补（来源：overview）")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="从 overview 抽经验草稿")
    ap.add_argument("--overview", required=True, help="overview 主文件路径")
    ap.add_argument("--out", help="--apply 时的写入目标文件")
    ap.add_argument("--apply", action="store_true", help="实际写入；默认只打印草稿")
    args = ap.parse_args()

    overview = Path(args.overview)
    if not overview.is_file():
        print(f"[learn] FAIL overview 不存在：{overview}")
        return 1

    draft = build_draft(extract_items(overview.read_text(encoding="utf-8")))

    if args.apply:
        if not args.out:
            print("[learn] FAIL --apply 必须同时给 --out", file=sys.stderr)
            return 1
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as f:
            f.write("\n" + draft)
        print(f"[learn] 已写入 {out}")
        return 0

    print(draft)
    print("[learn] dry-run：未写文件；确认草稿后加 --apply --out <path>。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
