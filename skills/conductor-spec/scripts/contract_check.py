#!/usr/bin/env python3
"""校验 change-contract 六段齐全且 Acceptance 非空。

用法：
    python contract_check.py --contract change-contract.md
    python contract_check.py --contract change-contract.md --acceptance-only

退出码：0 = 契约有效；1 = 缺段或 Acceptance 为空。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED = ("Why", "Delta", "Invariants", "Affected", "Acceptance", "Open")
ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)(.+?)\s*$")


def split_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", text, re.M))
    result: dict[str, str] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        result[m.group(1).strip()] = text[m.end():end]
    return result


def collect_items(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        m = ITEM_RE.match(line)
        if m and m.group(1).strip():
            items.append(m.group(1).strip())
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="change-contract 契约检查")
    ap.add_argument("--contract", required=True, help="契约文件路径")
    ap.add_argument("--acceptance-only", action="store_true",
                    help="只输出 Acceptance 条目，便于管道灌入台账")
    args = ap.parse_args()

    path = Path(args.contract)
    if not path.is_file():
        print(f"[contract] FAIL 文件不存在：{path}")
        return 1

    sections = split_sections(path.read_text(encoding="utf-8"))
    missing = [s for s in REQUIRED if s not in sections]
    acceptance = collect_items(sections.get("Acceptance", ""))

    if args.acceptance_only:
        if missing or not acceptance:
            print(f"[contract] FAIL 契约不完整或缺 Acceptance：缺段={missing or '无'}", file=sys.stderr)
            return 1
        for item in acceptance:
            print(item)
        return 0

    problems: list[str] = []
    if missing:
        problems.append(f"缺段={missing}")
    if not acceptance:
        problems.append("Acceptance 无条目")
    if problems:
        print("[contract] FAIL " + "; ".join(problems))
        return 1

    print(f"[contract] PASS 六段齐全，Acceptance={len(acceptance)} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
