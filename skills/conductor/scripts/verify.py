#!/usr/bin/env python3
"""规则验证：按语言执行 coding-rules-<lang>.md 中的验证命令，汇总退出码。

用途：conductor 的 S4 自省阶段。把"AI 声称遵守规则"变成"工具退出码为证据"。
输出可直接贴进 overview 的"验证结果"一节。

覆盖率门禁：命令集里必须存在带覆盖率的测试命令（pytest --cov / vitest --coverage /
go test -coverprofile 等），只跑裸测试不算 S4 证据——拦截"测试全绿冒充覆盖率达标"。
阈值可由命令参数或项目配置提供，配置式阈值需在 test-strategy.md 的人工台账里核对。

退出码：0 = 全部命令通过且覆盖率门禁通过；1 = 有失败 / 命令缺失 / 未跑覆盖率。
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REFS = Path(__file__).resolve().parents[1] / "references" / "03-coding-rules"
LANGS = ("python", "typescript", "react", "vue", "go", "rust", "dart")

# 覆盖率门禁：每门语言必须有一条"测试 + 覆盖率"命令，且带阈值参数。
# 只跑裸测试（pytest -q / go test / vitest run 无覆盖率）不算 S4 验证证据。
COVERAGE_SIGNALS = ("--cov", "--coverage", "-cover", "llvm-cov", "coverage=coverage")
THRESHOLD_SIGNALS = ("--cov-fail-under", "fail-under", "threshold", "min=", "coverage-min")


@dataclass(frozen=True)
class Result:
    cmd: str
    code: int
    ok: bool
    note: str = ""


def coverage_gate(cmds: list[str]) -> tuple[bool, str]:
    """覆盖率门禁：验证命令集里必须存在'测试 + 覆盖率'命令。

    拦截 S4 最常见的偷懒：只跑裸 pytest -q / vitest run / go test，
    拿'测试全绿'冒充覆盖率达标。阈值可由命令参数（--cov-fail-under /
    --fail-under）或项目配置（vitest.config 的 thresholds 等）提供——
    本检查只强制"跑了覆盖率"，阈值来源的核对交给 test-strategy.md 的人工台账。
    """
    coverage_cmds = [c for c in cmds if any(s in c.lower() for s in COVERAGE_SIGNALS)]
    if not coverage_cmds:
        return False, (
            "未发现任何覆盖率命令。裸跑测试不算 S4 验证证据——"
            "必须用带覆盖率的命令（如 pytest --cov / vitest --coverage / "
            "go test -coverprofile）并重跑，或显式登记豁免理由。"
        )
    with_threshold = [c for c in coverage_cmds if any(s in c.lower() for s in THRESHOLD_SIGNALS)]
    detail = f"检出 {len(coverage_cmds)} 条覆盖率命令"
    if with_threshold:
        detail += f"，其中 {len(with_threshold)} 条命令行自带阈值参数"
    else:
        detail += "；均未带命令行阈值，须确认阈值已在项目配置中固化（见 test-strategy.md）"
    return True, detail


def extract_commands(md: Path) -> list[str]:
    """从规则文件的 ```bash 代码块提取命令（忽略注释与空行）。"""
    if not md.is_file():
        return []
    text = md.read_text(encoding="utf-8")
    blocks = re.findall(r"```bash\s*\n(.*?)```", text, re.S)
    cmds: list[str] = []
    for block in blocks:
        for line in block.splitlines():
            line = line.split("#", 1)[0].strip()  # 去行尾注释
            if line:
                cmds.append(line)
    return cmds


def run_one(cmd: str, cwd: Path, timeout: int) -> Result:
    first = shlex.split(cmd)[0] if cmd else ""
    if not shutil.which(first):
        return Result(cmd, -1, False, "命令不存在（工具未安装）")
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        note = ""
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout).strip().splitlines()
            note = tail[-1][:120] if tail else ""
        return Result(cmd, proc.returncode, proc.returncode == 0, note)
    except subprocess.TimeoutExpired:
        return Result(cmd, -2, False, f"超时（>{timeout}s）")


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 规则验证汇总")
    ap.add_argument("--lang", required=True, choices=LANGS, help="要验证的语言")
    ap.add_argument("--cwd", default=".", help="命令执行目录（项目根）")
    ap.add_argument("--timeout", type=int, default=300, help="单命令超时秒数")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要执行的命令")
    args = ap.parse_args()

    md = REFS / f"coding-rules-{args.lang}.md"
    cmds = extract_commands(md)
    if not cmds:
        print(f"[verify] 未从 {md.name} 提取到验证命令。", file=sys.stderr)
        return 1

    if args.dry_run:
        print("\n".join(cmds))
        return 0

    cwd = Path(args.cwd).resolve()
    print(f"# 验证结果 · {args.lang}（{cwd}）\n")

    gate_ok, gate_note = coverage_gate(cmds)
    print(f"- [{'PASS' if gate_ok else 'FAIL'}] coverage-gate — {gate_note}")

    results = [run_one(c, cwd, args.timeout) for c in cmds]
    for r in results:
        mark = "PASS" if r.ok else "FAIL"
        print(f"- [{mark}] exit={r.code} `{r.cmd}`" + (f" — {r.note}" if r.note else ""))
    passed = sum(1 for r in results if r.ok)
    print(f"\n小结：{passed}/{len(results)} 通过。")
    print("> 退出码为客观证据；非 0 项禁止进 review、禁止标完成。")
    return 0 if gate_ok and all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
