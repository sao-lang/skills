#!/usr/bin/env python3
"""迁移台账（场景7 兼容 shim）：底层已收敛到 commitment_ledger.py 通用引擎。

保留原有 init/next/check 三个子命令和 `.migration-ledger.json` 默认文件名，
确保场景7文档与既有调用不破。差异：本 shim 固定 source=module，check 恒查模块 drift。
新场景（开发/迭代/解bug/文档同步）请直接用 `commitment_ledger.py` 的多来源采集。

三个子命令：
  init   盘点：扫源码生成/合并模块台账（--merge 保留已迁状态，只补新增项）
  check  闸门：校验收口（pending/in_progress/无证据/skipped 无理由/drift）；--strict 有缺口退出 1
  next   断点：按依赖层序输出下一批模块（中断项优先）

完整方法论见 ../references/migration-integrity.md；
通用防漏框架见 ../references/commitment-ledger.md。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from commitment_ledger import (
    DEFAULT_EXTS, load_ledger, scan_modules, merge_items,
    save_ledger, check_items, print_check_report, topo_order,
)


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    out = Path(args.out) if args.out else root / ".migration-ledger.json"
    exts = {e.strip() for e in args.exts.split(",") if e.strip()}
    scanned = scan_modules(root, exts, args.max_deps)
    old = load_ledger(out)

    if args.merge:
        merged, added, kept, _ = merge_items(old, scanned, ["modules:" + str(root)])
    else:
        merged, added, kept = scanned, list(scanned), 0
    save_ledger(out, merged, args.project or str(root))

    print(f"# 迁移台账盘点（{root}）\n")
    print(f"- 台账文件：`{out}`")
    print(f"- 条目总数：{len(merged)}（新增 {len(added)}，保留状态 {kept}）")
    by_kind: dict[str, int] = {}
    for it in scanned.values():
        by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
    print("- 类型分布：" + "，".join(f"{k} {v}" for k, v in sorted(by_kind.items())))
    print("\n> 台账是唯一事实源。逐块迁移时在台账里把 status 改为 verified 并填写 evidence；"
          "新会话先跑 `next` 或 `check` 定位断点，不靠记忆。")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    data = load_ledger(ledger)
    if data is None:
        print(f"FAIL — 台账不存在或格式错误：{ledger}（先跑 init 盘点）")
        return 1
    r = check_items(data.get("items", {}), ledger.parent,
                    args.path, args.exts, args.max_deps)
    print_check_report(ledger, r)
    return 1 if (args.strict and not r["ok"]) else 0


def cmd_next(args: argparse.Namespace) -> int:
    ledger = Path(args.ledger)
    data = load_ledger(ledger)
    if data is None:
        print(f"FAIL — 台账不存在或格式错误：{ledger}（先跑 init 盘点）")
        return 1
    items = data.get("items", {})
    todo = [(r, it) for r, it in topo_order(items)
            if it.get("status") in ("pending", "in_progress")]
    if not todo:
        print("全部收口，无待迁模块。")
        return 0
    n = args.limit
    print(f"# 下一批待迁模块（共 {len(todo)} 项，取前 {min(n, len(todo))}）\n")
    print("> 依赖层序仅为建议（弱信号需核对）；每次只迁一个，迁完在台账写 verified+evidence。\n")
    for cid, it in todo[:n]:
        flag = "[中断续接]" if it.get("status") == "in_progress" else ""
        cp = f" — 断点：{it.get('checkpoint')}" if it.get("checkpoint") else ""
        deps = f" — 依赖：{', '.join(it.get('deps', []))}" if it.get("deps") else ""
        print(f"- {cid}（{it.get('kind', 'module')}）{flag}{cp}{deps}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 迁移台账（场景7 shim，底层=承诺台账）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="盘点：扫源码生成/合并模块台账")
    p_init.add_argument("--path", default=".")
    p_init.add_argument("--out", default="")
    p_init.add_argument("--exts", default=",".join(DEFAULT_EXTS))
    p_init.add_argument("--max-deps", type=int, default=20)
    p_init.add_argument("--project", default="")
    p_init.add_argument("--merge", action="store_true")

    p_check = sub.add_parser("check", help="闸门：校验迁移收口")
    p_check.add_argument("--ledger", default=".migration-ledger.json")
    p_check.add_argument("--path", default="")
    p_check.add_argument("--exts", default=",".join(DEFAULT_EXTS))
    p_check.add_argument("--max-deps", type=int, default=20)
    p_check.add_argument("--strict", action="store_true")

    p_next = sub.add_parser("next", help="断点：下一批待迁模块")
    p_next.add_argument("--ledger", default=".migration-ledger.json")
    p_next.add_argument("--limit", type=int, default=5)

    args = ap.parse_args()
    return {"init": cmd_init, "check": cmd_check, "next": cmd_next}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
