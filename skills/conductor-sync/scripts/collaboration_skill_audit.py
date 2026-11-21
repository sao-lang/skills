#!/usr/bin/env python3
"""协作 skill 筛选测试：按"是否被工作流调用 / 是否产出门禁证据 / 是否与器官重复 / 体积开销"打分。

输出 KEEP / RENAME_TO_ORGAN / DEPRECATE 建议。这是接线与职责筛查，不替代人工体验判断。
退出码恒 0（报告用）。
"""
from __future__ import annotations

from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]

# 名称 → (被 conductor 主链调用, 产出被门禁消费的证据, 与已有器官重复, 字符数阈值)
DATA = {
    "grill-design": (True, True, False, 4000),
    "code-quality-review": (True, True, False, 6000),
    "handoff": (True, True, False, 4000),
    "graphify": (True, False, False, 6000),
    "ponytail": (True, False, False, 5000),
    "caveman": (False, False, True, 6000),
    "grill-me": (False, False, True, 4000),
    "ponytail-review": (False, False, True, 6000),
    "caveman-compress": (False, False, True, 6000),
    "metago-code-review-deep": (True, False, True, 4000),
}

RENAME = {
    "grill-design": "conductor-brainstorm",
    "code-quality-review": "conductor-review",
    "handoff": "conductor-memory",
    "graphify": "conductor-impact",
    "ponytail": "conductor-tdd",
}


def main() -> int:
    print("# 协作 skill 筛选测试\n")
    print(f"{'skill':<26} {'分数':>4}  结论")
    for name, (called, evidence, duplicate, max_chars) in DATA.items():
        skill = SKILLS / name / "SKILL.md"
        n = len(skill.read_text(encoding="utf-8")) if skill.is_file() else 0
        score = called * 3 + evidence * 3 - duplicate * 2 - (n > max_chars) * 1
        if score >= 4 and name in RENAME:
            verdict = f"MERGED_INTO_ORGAN → {RENAME[name]}（原目录已删）"
        elif score >= 4:
            verdict = "KEEP"
        else:
            verdict = "DEPRECATE"
        print(f"{name:<26} {score:>4}  {verdict}  ({n} chars)")
    print("\n> 判定口径：被调用+3 / 产出门禁证据+3 / 与器官重复-2 / 超体积阈值-1；"
          "≥4 且可映射器官 → 改名并入器官，<4 → 废弃。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
