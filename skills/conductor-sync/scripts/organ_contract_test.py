#!/usr/bin/env python3
"""器官契约测试：验证 conductor 的器官接线、I/O 契约、降级路径与状态文件瘦身。

注意：本测试验证的是**接线与契约**，不是真实 LLM 会话中器官是否被调用；
后者需要场景冒烟清单人工复核（见 roadmap）。

退出码：0 = 全部通过；1 = 有契约缺口。
"""
from __future__ import annotations

import sys
import tempfile
sys.dont_write_bytecode = True

import json
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPTS.parents[1]          # .../skills
CONDUCTOR = SKILLS_ROOT / "conductor"
ORGANS = (
    "conductor-plan", "conductor-brainstorm",
    "conductor-tdd", "conductor-review",
    "conductor-ledger", "conductor-memory",
    "conductor-impact", "conductor-debug", "conductor-git",
    "conductor-subagent", "conductor-sync",
)
REQUIRED_SECTIONS = ("## 输入", "## 输出", "## 降级")

results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def check_organs() -> None:
    for organ in ORGANS:
        p = SKILLS_ROOT / organ
        skill = p / "SKILL.md"
        if not skill.is_file():
            check(f"{organ} 位于 conductor 同级目录", False, f"缺 {skill}")
            continue
        text = skill.read_text(encoding="utf-8")
        front_ok = f"name: {organ}" in text.split("---", 2)[1] if text.startswith("---") else False
        missing = [s for s in REQUIRED_SECTIONS if s not in text]
        self_contained = ("conductor/references" not in text
                          and "conductor/scripts" not in text
                          and (p / "references").is_dir())
        check(f"{organ} 契约完整", front_ok and not missing,
              f"frontmatter={front_ok}, 缺章节={missing or '无'}")
        check(f"{organ} 自包含（方法文档在本器官）", self_contained)

    merged = {
        "conductor-brainstorm": "grill-design-SKILL.md",
        "conductor-review": "code-quality-review-SKILL.md",
        "conductor-memory": "handoff-SKILL.md",
    }
    for organ, fname in merged.items():
        check(f"{organ} 已并入改名 skill", (SKILLS_ROOT / organ / "references" / fname).is_file())

    merged_specs = {
        "conductor-brainstorm": ("change-contract-template.md", "spec-method.md"),
        "conductor-memory": ("learning-method.md", "lessons-template.md"),
    }
    for organ, fnames in merged_specs.items():
        for fname in fnames:
            check(f"{organ} 已并入方法 {fname}",
                  (SKILLS_ROOT / organ / "references" / fname).is_file())

    for organ, script in (("conductor-brainstorm", "contract_check.py"),
                          ("conductor-memory", "learn_capture.py")):
        check(f"{organ} 执行脚本就位",
              (SKILLS_ROOT / organ / "scripts" / script).is_file())

    registry = (CONDUCTOR / "references/01-routing/organ-registry.md").read_text(encoding="utf-8")
    missing = [o for o in ORGANS if f"`{o}`" not in registry]
    check(f"器官注册表覆盖 {len(ORGANS)} 个器官", not missing, f"缺 {missing or '无'}")

    entry = (CONDUCTOR / "SKILL.md").read_text(encoding="utf-8")
    check("conductor 入口挂载器官总线", "organ-registry.md" in entry)

    matrix = (CONDUCTOR / "references/01-routing/skill-matrix.md").read_text(encoding="utf-8")
    deprecated = ["grill-me", "ponytail-review", "caveman-compress", "graphify", "ponytail", "caveman", "metago-code-review-deep"]
    leftovers = [n for n in deprecated if f"`{n}`" in matrix]
    check("废弃 skill 已从主矩阵移除", not leftovers, f"残留={leftovers or '无'}")


def check_state_files() -> None:
    sys.path.insert(0, str(SKILLS_ROOT / "conductor-ledger" / "scripts"))
    sys.path.insert(0, str(SKILLS_ROOT / "conductor-memory" / "scripts"))
    import overview_path as op
    import commitment_ledger as cl

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        sid = "abcd1234"
        op.save_pointer(root, sid)
        ptr = json.loads((root / op.POINTER_NAME).read_text(encoding="utf-8"))
        gi = (root / ".gitignore").read_text(encoding="utf-8")
        check("会话指针最小字段", set(ptr) == {"sid"} and ptr["sid"] == sid, str(ptr))
        check("状态文件自动忽略",
              all(n in gi for n in (".conductor-session.json", ".commitment-ledger.json")))

        old_style = {f"item-{i:03d}": cl.new_item(f"item-{i:03d}", "spec", "spec") for i in range(40)}
        ledger = root / ".commitment-ledger.json"
        cl.save_ledger(ledger, old_style, "demo")
        raw = ledger.read_text(encoding="utf-8")
        data = json.loads(raw)
        loaded = cl.load_ledger(ledger)
        check("台账紧凑持久化", "\n  " not in raw and set(data) <= {"v", "items", "project"},
              f"{len(raw)} 字符 / 40 条")
        check("台账读回兼容", loaded is not None and len(loaded["items"]) == 40)


def check_overview_template() -> None:
    p = SKILLS_ROOT / "conductor-memory" / "references" / "overview.md"
    text = p.read_text(encoding="utf-8") if p.is_file() else ""
    check("overview 两-tier 模板",
          "L0 索引卡（≤8 行）" in text and ".details.md" in text and len(text) < 5000,
          f"{len(text)} 字符")


def main() -> int:
    print("# conductor 器官契约测试\n")
    check_organs()
    check_state_files()
    check_overview_template()
    failed = results.count(False)
    print(f"\n> {len(results) - failed}/{len(results)} 通过；"
          "本测试不替代真实 LLM 会话调用效果评估。")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
