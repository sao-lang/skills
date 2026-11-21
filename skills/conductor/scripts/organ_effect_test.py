#!/usr/bin/env python3
"""器官效果测试：对可执行的器官跑真实输入→输出冒烟；对方法型器官校验关键步骤齐备。

与 organ_contract_test.py 的区别：
- contract：文件/接线/自包含
- effect：给定输入后是否产出约定的输出（真实脚本执行 + 方法步骤断言）

退出码：0 = 全部通过；1 = 有缺口。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
results: list[bool] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def run(script: Path, *args: str, cwd: Path, stdin: str = "") -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-B", str(script), *args], cwd=cwd,
                       input=stdin, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def method_organs() -> None:
    static = {
        "conductor-router": ("conductor-router/references/routing.md", ["语义三问", "结构算子", "置信度"]),
        "conductor-brainstorm": ("conductor-brainstorm/references/grill-design-SKILL.md", ["设计树", "前沿", "结论"]),
        "conductor-spec": ("conductor-spec/references/spec-method.md", ["抽取", "merge", "验收注入"]),
        "conductor-learn": ("conductor-learn/references/learning-method.md", ["抽什么", "去重", "回写"]),
        "conductor-debug": ("conductor-debug/references/engineering-debugging.md", ["根因", "复现", "纵深防御"]),
        "conductor-git": ("conductor-git/references/finish.md", ["验测试", "菜单", "清理"]),
    }
    for organ, (rel, keywords) in static.items():
        p = SKILLS / rel
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
        miss = [k for k in keywords if k not in text]
        check(f"{organ} 方法步骤齐备", not miss, f"缺={miss or '无'}")


def executable_organs() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        # overview：create → append
        ov_script = SKILLS / "conductor-overview/scripts/overview_path.py"
        rc, out = run(ov_script, "--project-root", ".", "--topic", "效果测试", cwd=root)
        first = json.loads(out)["sid"] if rc == 0 else ""
        rc2, out2 = run(ov_script, "--project-root", ".", "--topic", "续写", cwd=root)
        second = json.loads(out2) if rc2 == 0 else {}
        check("conductor-overview 续接同一会话", bool(first) and second.get("sid") == first,
              f"{first} → {second.get('sid')}")

        # ledger：采集 → 门禁 → 全览
        led_script = SKILLS / "conductor-ledger/scripts/commitment_ledger.py"
        (root / "spec.md").write_text("- 需求一：能登录\n- 需求二：有回归测试\n", encoding="utf-8")
        rc, out = run(led_script, "init", "--ledger", ".commitment-ledger.json",
                      "--from-list", "spec.md", cwd=root)
        rc2, show = run(led_script, "show", cwd=root)
        check("conductor-ledger 采集并全览", rc == 0 and rc2 == 0 and "需求一" in show)

        # review：lite 复核门禁
        rv_script = SKILLS / "conductor-review/scripts/review_gate.py"
        (root / "ov.md").write_text(
            "## 轻量复核（lite）\n- 档位: lite\n- Blocker = 0\n"
            "- 意图一致 — src/a.py:12\n- 边界 — 无新增风险\n- 证据 — 退出码 0\n",
            encoding="utf-8")
        rc, out = run(rv_script, "--overview", "ov.md", "--lite", cwd=root)
        check("conductor-review lite 门禁放行", rc == 0, out.splitlines()[-1] if out else "")

        # impact：真实脚本找引用者
        imp_script = SKILLS / "conductor-impact/scripts/impact_analysis.py"
        (root / "a.py").write_text("def target():\n    return 1\n", encoding="utf-8")
        (root / "b.py").write_text("from a import target\n\ndef use():\n    return target()\n",
                                   encoding="utf-8")
        rc, out = run(imp_script, "--path", ".", "--symbols", "target", cwd=root)
        check("conductor-impact 找到引用者", rc == 0 and "b.py" in out, out.splitlines()[0] if out else "")

        # spec：契约检查与 Acceptance 输出
        sp_script = SKILLS / "conductor-spec/scripts/contract_check.py"
        (root / "change-contract.md").write_text(
            "# Change: t1 / 2026-01-01 / confirmed\n"
            "## Why\n验证活规格\n\n"
            "## Delta\n- 新增登录能力\n\n"
            "## Invariants\n- 错误语义不变\n\n"
            "## Affected\n- a.py（需核实）\n\n"
            "## Acceptance\n- 登录回归测试全绿\n\n"
            "## Open\n- 无\n", encoding="utf-8")
        rc, out = run(sp_script, "--contract", "change-contract.md", cwd=root)
        rc2, items = run(sp_script, "--contract", "change-contract.md", "--acceptance-only", cwd=root)
        check("conductor-spec 契约检查与 Acceptance 输出",
              rc == 0 and rc2 == 0 and "登录回归测试全绿" in items,
              out.splitlines()[0] if out else "")

        # learn：dry-run 出草稿，不落盘
        ln_script = SKILLS / "conductor-learn/scripts/learn_capture.py"
        (root / "learn-ov.md").write_text(
            "## 关键决策\n- 遇到 X 现象先查 Y 根因，避免重复踩坑\n", encoding="utf-8")
        rc, out = run(ln_script, "--overview", "learn-ov.md", cwd=root)
        check("conductor-learn dry-run 出草稿",
              rc == 0 and "触发条件" in out and "未写文件" in out,
              out.splitlines()[0] if out else "")

        # tdd：verify 干跑给出验证命令
        td_script = SKILLS / "conductor-tdd/scripts/verify.py"
        rc, out = run(td_script, "--lang", "python", "--dry-run", cwd=root)
        check("conductor-tdd 产出验证命令", rc == 0 and ("ruff" in out or "pytest" in out),
              out.splitlines()[0] if out else "")


def main() -> int:
    print("# conductor 器官效果测试\n")
    method_organs()
    executable_organs()
    failed = results.count(False)
    print(f"\n> {len(results) - failed}/{len(results)} 通过；"
          "方法型器官为步骤断言，脚本型器官为真实输入→输出冒烟。")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
