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
        "conductor-plan 场景判定": ("conductor-plan/references/router/planning-core.md", ["语义三问", "结构算子", "置信度"]),
        "plan 意图推断与切分": ("conductor-plan/references/router/planning-core.md", ["原子任务切分", "意图推断", "去类型化", "并列"]),
        "plan 反例库": ("conductor-plan/references/cases.md", ["被合并成单节点", "正确解析", "serves_task"]),
        "plan 端到端测试方案": ("conductor-plan/references/test-plan.md", ["黑盒", "判分表", "测试结果"]),
        "plan 调研归属": ("conductor-plan/references/planning-method.md", ["调研/分析节点归属", "serves_task"]),
        "subagent 独立性判据": ("conductor-subagent/SKILL.md", ["≥2 个相互独立", "任务独立性与工作量"]),
        "conductor-plan 图 DSL": ("conductor-plan/references/execution-graph-schema.md", ["节点", "边", "空转防护", "serves_task"]),
        "conductor-plan 规划方法": ("conductor-plan/references/planning-method.md", ["意图分析", "澄清循环", "步骤展开", "习惯"]),
        "conductor 场景适配层": ("conductor/references/01-routing/execution-graph-adapter.md", ["场景", "门禁", "ref"]),
        "review 设计→代码对称": ("conductor-review/references/independent-review.md", ["改设计", "代码是否失配", "Blocker"]),
        "cost-tiers 反向验证": ("conductor/references/01-routing/cost-tiers.md", ["反向验证", "判对了省钱", "判错了被拦"]),
        "overview 省掉证据": ("conductor-memory/references/overview.md", ["省掉", "可核对信号", "反向验证"]),
        "conductor-brainstorm": ("conductor-brainstorm/references/grill-design-SKILL.md", ["设计树", "前沿", "结论"]),
        "conductor-brainstorm 规格方法": ("conductor-brainstorm/references/spec-method.md", ["抽取", "merge", "验收注入"]),
        "conductor-memory 沉淀方法": ("conductor-memory/references/learning-method.md", ["抽什么", "去重", "回写"]),
        "conductor-memory 记录方法": ("conductor-memory/references/overview.md", ["L0", "details", "脱敏"]),
        "conductor-debug": ("conductor-debug/references/engineering-debugging.md", ["根因", "复现", "纵深防御"]),
        "conductor-git": ("conductor-git/references/git-commit.md", ["提交", "精确", "hooks"]),
        "conductor-subagent": ("conductor-subagent/references/dispatch.md", ["brief", "全新", "评审"]),
        "conductor-sync": ("conductor-sync/references/install-verify.md", ["复制", "全局", "测试"]),
        "conductor-review 残留核对": ("conductor-review/references/removal-check.md", ["删除", "残留", "退出码"]),
        "router 条件加载判据": ("conductor/references/01-routing/cost-tiers.md", ["删除推导", "removal_check", "文档同步核对", "双轨扫描", "机器可判"]),
        "tdd 两种最小化区分": ("conductor-tdd/references/coding-rules-common.md", ["变更面最小", "diff 行数最小", "hotfix", "退出条件"]),
    }
    for organ, (rel, keywords) in static.items():
        p = SKILLS / rel
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
        miss = [k for k in keywords if k not in text]
        check(f"{organ} 方法步骤齐备", not miss, f"缺={miss or '无'}")


def executable_organs() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)

        # memory：create → append
        ov_script = SKILLS / "conductor-memory/scripts/overview_path.py"
        rc, out = run(ov_script, "--project-root", ".", "--topic", "效果测试", cwd=root)
        first = json.loads(out)["sid"] if rc == 0 else ""
        rc2, out2 = run(ov_script, "--project-root", ".", "--topic", "续写", cwd=root)
        second = json.loads(out2) if rc2 == 0 else {}
        check("conductor-memory 续接同一会话", bool(first) and second.get("sid") == first,
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

        # review_gate 反向验证：省掉声明 vs 客观信号（跳过判断的机器兜底）
        rg_script = SKILLS / "conductor-review/scripts/review_gate.py"
        (root / "skip-ov.md").write_text(
            "## 独立 review 结果\nBlocker = 0\n\n## 独立 review 报告\n"
            "- finding: 文件:行号 src/a.py:12\n- blocker: 0\n- 证据: 退出码 0\n\n"
            "## 路由声明\n省掉：TDD/verify（无代码改动）、文档同步\n",
            encoding="utf-8")
        rc, out = run(rg_script, "--overview", "skip-ov.md", "--diff", "src/a.py", cwd=root)
        check("反向验证：省掉TDD但diff有代码 → FAIL", rc == 1 and "冲突" in out,
              out.splitlines()[0] if out else "")
        rc, out = run(rg_script, "--overview", "skip-ov.md", "--diff", "docs/x.md", cwd=root)
        check("反向验证：省掉TDD且diff仅文档 → PASS", rc == 0 and "跳过成立" in out,
              out.splitlines()[0] if out else "")
        (root / "skip-contract.md").write_text(
            "# Change t\n## Delta\n- 替换公共接口 parse_config 的签名\n## Acceptance\n- 无\n",
            encoding="utf-8")
        rc, out = run(rg_script, "--overview", "skip-ov.md", "--contract", "skip-contract.md", cwd=root)
        check("反向验证：省掉文档同步但契约有公共接口 → FAIL", rc == 1 and "文档同步" in out and "FAIL" in out,
              out.splitlines()[0] if out else "")

        # impact：真实脚本找引用者
        imp_script = SKILLS / "conductor-impact/scripts/impact_analysis.py"
        (root / "a.py").write_text("def target():\n    return 1\n", encoding="utf-8")
        (root / "b.py").write_text("from a import target\n\ndef use():\n    return target()\n",
                                   encoding="utf-8")
        rc, out = run(imp_script, "--path", ".", "--symbols", "target", cwd=root)
        check("conductor-impact 找到引用者", rc == 0 and "b.py" in out, out.splitlines()[0] if out else "")

        # brainstorm（spec 并入）：契约检查与 Acceptance 输出
        sp_script = SKILLS / "conductor-brainstorm/scripts/contract_check.py"
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
        check("conductor-brainstorm 契约检查与 Acceptance 输出",
              rc == 0 and rc2 == 0 and "登录回归测试全绿" in items,
              out.splitlines()[0] if out else "")

        # memory（learn 并入）：dry-run 出草稿，不落盘
        ln_script = SKILLS / "conductor-memory/scripts/learn_capture.py"
        (root / "learn-ov.md").write_text(
            "## 关键决策\n- 遇到 X 现象先查 Y 根因，避免重复踩坑\n", encoding="utf-8")
        rc, out = run(ln_script, "--overview", "learn-ov.md", cwd=root)
        check("conductor-memory dry-run 出草稿",
              rc == 0 and "触发条件" in out and "未写文件" in out,
              out.splitlines()[0] if out else "")

        # tdd：verify 干跑给出验证命令
        td_script = SKILLS / "conductor-tdd/scripts/verify.py"
        rc, out = run(td_script, "--lang", "python", "--dry-run", cwd=root)
        check("conductor-tdd 产出验证命令", rc == 0 and ("ruff" in out or "pytest" in out),
              out.splitlines()[0] if out else "")

        # review（removal_check）：待删项残留 → FAIL；清除后 → PASS
        rc_script = SKILLS / "conductor-review/scripts/removal_check.py"
        (root / "contract.md").write_text(
            "# Change: t1\n## Why\nx\n## Delta\n- 删除 `obsolete_fn` 函数\n"
            "## Invariants\n- 无\n## Affected\n- a.py\n## Acceptance\n- 无\n## Open\n- 无\n",
            encoding="utf-8")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "m.py").write_text("def obsolete_fn():\n    return 1\n", encoding="utf-8")
        rc, out = run(rc_script, "--contract", "contract.md", "--path", "src", cwd=root)
        check("conductor-review 待删项残留被拦", rc == 1 and "残留：obsolete_fn" in out,
              out.splitlines()[0] if out else "")
        (root / "src" / "m.py").write_text("def fresh_fn():\n    return 2\n", encoding="utf-8")
        rc, out = run(rc_script, "--contract", "contract.md", "--path", "src", cwd=root)
        check("conductor-review 清除后放行", rc == 0 and "已清除：obsolete_fn" in out,
              out.splitlines()[0] if out else "")

        # plan：执行图校验 + mermaid 生成
        pv_script = SKILLS / "conductor-plan/scripts/plan_validate.py"
        good_plan = {
            "version": "1.0", "goal": "效果测试", "mode": "conductor", "confidence": 0.9,
            "nodes": [
                {"id": "n1", "kind": "tool", "label": "跑测试", "action": "pytest", "exit_criteria": "退出码0"},
                {"id": "n2", "kind": "gate", "label": "门禁", "action": "verify", "exit_criteria": "退出码0"},
            ],
            "edges": [{"from": "n1", "to": "n2", "type": "seq"}],
            "budget": {"max_steps": 10, "noop_limit": 2},
        }
        (root / "plan.json").write_text(json.dumps(good_plan, ensure_ascii=False), encoding="utf-8")
        rc, out = run(pv_script, "--plan", "plan.json", "--mermaid", cwd=root)
        check("conductor-plan 合法图 PASS + mermaid", rc == 0 and "flowchart TD" in out,
              out.splitlines()[0] if out else "")
        bad_plan = dict(good_plan, budget={"max_steps": 10}, confidence=0.3)
        (root / "plan-bad.json").write_text(json.dumps(bad_plan, ensure_ascii=False), encoding="utf-8")
        rc, out = run(pv_script, "--plan", "plan-bad.json", cwd=root)
        check("conductor-plan 缺空转预算/低置信度被拦", rc == 1 and "noop_limit" in out and "0.5" in out,
              out.splitlines()[0] if out else "")
        no_serves = dict(good_plan, nodes=[
            {"id": "r1", "kind": "research", "label": "调研范围", "action": "查 widget 意图", "exit_criteria": "出范围清单"},
        ])
        (root / "plan-noserves.json").write_text(json.dumps(no_serves, ensure_ascii=False), encoding="utf-8")
        rc, out = run(pv_script, "--plan", "plan-noserves.json", cwd=root)
        check("conductor-plan 调研节点缺 serves_task 被拦", rc == 1 and "serves_task" in out,
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
