#!/usr/bin/env python3
"""脚本单一真相源测试：conductor 的重复入口必须是薄 shim，实现只在器官目录。

检查：
  1. 6 个已知重复脚本都是薄 shim（含 runpy.run_path，且不含完整实现标记）
  2. shim 指向的器官实现存在且语法可编译
  3. 每个 shim 能转发 --help 并返回 0

退出码：0 = 全部通过；1 = 有 shim 漂移或转发失败。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILLS = SCRIPTS.parents[1]          # .../skills（本测试已随测试套件迁至 conductor-sync/scripts）
SHIM_DIR = SKILLS / "conductor" / "scripts"   # 6 个薄 shim 仍留在 conductor 本体

SHIMS = {
    "verify.py": "conductor-tdd/scripts/verify.py",
    "review_gate.py": "conductor-review/scripts/review_gate.py",
    "overview_path.py": "conductor-memory/scripts/overview_path.py",
    "commitment_ledger.py": "conductor-ledger/scripts/commitment_ledger.py",
    "migration_ledger.py": "conductor-ledger/scripts/migration_ledger.py",
    "impact_analysis.py": "conductor-impact/scripts/impact_analysis.py",
}
FULL_IMPL_MARKERS = ("def main(", "argparse.ArgumentParser(")

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def check_shims() -> None:
    for name, rel in SHIMS.items():
        shim = SHIM_DIR / name
        target = SKILLS / rel
        if not shim.is_file():
            check(f"{name} shim 存在", False, f"缺 {shim}")
            continue
        text = shim.read_text(encoding="utf-8")
        is_thin = ("runpy.run_path" in text and "_TARGET" in text
                   and 'if __name__ == "__main__"' in text
                   and rel.replace("/", "/") in text
                   and len(text) < 1200
                   and not any(marker in text for marker in FULL_IMPL_MARKERS))
        check(f"{name} 是薄 shim", is_thin, f"{len(text)} 字符")

        if not target.is_file():
            check(f"{name} 目标存在", False, f"缺 {target}")
            continue
        try:
            compile(target.read_text(encoding="utf-8"), str(target), "exec")
            ok = True
            detail = ""
        except SyntaxError as e:
            ok = False
            detail = str(e)
        check(f"{name} 目标语法可编译", ok, detail)


def check_forwarding() -> None:
    with tempfile.TemporaryDirectory() as d:
        for name in SHIMS:
            proc = subprocess.run(
                [sys.executable, "-B", str(SHIM_DIR / name), "--help"],
                cwd=d, capture_output=True, text=True, timeout=30,
            )
            check(f"{name} 转发 --help", proc.returncode == 0,
                  (proc.stderr or proc.stdout).strip().splitlines()[-1]
                  if (proc.stderr or proc.stdout).strip() else "")


def main() -> int:
    print("# 脚本单一真相源测试\n")
    check_shims()
    check_forwarding()
    failed = results.count(False)
    print(f"\n> {len(results) - failed}/{len(results)} 通过；"
          "本测试只验证 shim 接线与转发，不替代脚本本身的效果测试。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
