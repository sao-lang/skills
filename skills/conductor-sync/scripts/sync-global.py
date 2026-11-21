#!/usr/bin/env python3
"""把 conductor 家族 skill 统一安装/更新到 WorkBuddy 全局 skills 目录（conductor-sync 器官）。

背景：Windows 无符号链接权限，全局安装采用复制，两份独立。
项目 skills/ 是唯一真相源；改完跑本脚本同步到 ~/.workbuddy/skills/。

用法：
    python scripts/sync-global.py                # 同步 conductor 家族（conductor + conductor-*，默认）
    python scripts/sync-global.py --all          # 同步全部 skill（含非 conductor 家族的协作 skill）
    python scripts/sync-global.py --dry-run      # 只列差异，不复制
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

SKILLS_BASE = Path(__file__).resolve().parents[2]         # .../skills
GLOBAL_BASE = Path.home() / ".workbuddy" / "skills"


def rel_files(root: Path) -> list[Path]:
    return sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file())


def sync_tree(src_root: Path, dst_root: Path, dry_run: bool) -> tuple[int, int]:
    """同步一棵 skill 树，返回 (同步文件数, 全局多余文件数)。"""
    to_copy: list[Path] = []
    for rel in rel_files(src_root):
        src, dst = src_root / rel, dst_root / rel
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            to_copy.append(rel)

    stale: list[Path] = []
    if dst_root.is_dir():
        for rel in rel_files(dst_root):
            if not (src_root / rel).exists():
                stale.append(rel)

    print(f"[sync] {src_root.name} → {dst_root}")
    for rel in to_copy:
        print(f"  同步：{rel}")
    for rel in stale:
        print(f"  全局多余（源已删，需手动确认）：{rel}")

    if not dry_run:
        for rel in to_copy:
            src, dst = src_root / rel, dst_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return len(to_copy), len(stale)


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 家族 skill 统一安装/更新到全局目录")
    ap.add_argument("--dry-run", action="store_true", help="只列差异，不复制")
    ap.add_argument("--all", action="store_true",
                    help="同步全部 skill（默认只同步 conductor 家族：conductor + conductor-*）")
    args = ap.parse_args()

    if not SKILLS_BASE.is_dir():
        print(f"[sync] 源目录不存在：{SKILLS_BASE}", file=sys.stderr)
        return 1

    if args.all:
        targets = [(p, GLOBAL_BASE / p.name) for p in sorted(SKILLS_BASE.iterdir())
                   if p.is_dir() and not p.name.startswith(".")]
    else:
        targets = [(p, GLOBAL_BASE / p.name) for p in sorted(SKILLS_BASE.glob("conductor*"))
                   if p.is_dir()]

    total = stale_total = 0
    for src, dst in targets:
        copied, stale = sync_tree(src, dst, args.dry_run)
        total += copied
        stale_total += stale

    if args.dry_run:
        print(f"[sync] dry-run：将同步 {total} 个文件；未实际复制。")
    else:
        print(f"[sync] 完成，同步 {total} 个文件。")
    if stale_total:
        print(f"[sync] 注意：全局有 {stale_total} 个源已删除的文件，需手动确认后删除。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
