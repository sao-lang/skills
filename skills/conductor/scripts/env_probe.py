#!/usr/bin/env python3
"""环境依赖探测：发现项目的"真实环境需求"与"当前可用性"，供 S0 记录 overview、S4 核对。

背景：没有 Docker/DB 时，AI 常把依赖真实环境的功能直接砍掉或只写 fake——这是功能缺失。
本脚本把"这个项目是否有环境依赖功能、当前环境是否可用、真实测试入口在哪"变成机器可见的事实，
让 AI 无法以"环境不支持"为借口跳过实现（规则见 architecture-contracts.md §4.5）。

用法：
  python scripts/env_probe.py --project-root .
      → JSON: {docker_available, compose_files, real_test_dirs, env_dependency_signals,
               recommended_real_test_cmd, needs_real_env}

输出字段：
  docker_available       docker daemon 是否可用（bool / null=未安装）
  compose_files          找到的 docker-compose*.yml / compose*.yml
  real_test_dirs         tests/integration、tests/e2e 等真实环境测试目录
  env_dependency_signals 源码里连 DB/Redis/容器/外部 API 的信号（文件:行号）
  needs_real_env         是否存在环境依赖（有 compose 或集成测试目录或依赖信号）
  recommended_real_test_cmd 建议的真实测试命令（供用户要求真实测试时用）

退出码恒 0（探测脚本不判失败）。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

# 本地基础设施依赖信号（DB/Redis/容器）——这些是需要"真实环境"的功能标志。
# 注意：故意不含 httpx/requests——外部 API 适配器（LLM/MCP/WebFetch）通常有合理的
# 默认实现或 mock，不属于"没环境就砍功能"的范畴，纳入只会误报。
DEP_PATTERNS = (
    r"\basyncpg\b", r"\bpsycopg\b", r"\bsqlalchemy\b",
    r"\btestcontainers\b", r"\bcreate_engine\b", r"\bDATABASE_URL\b",
    r"\bREDIS_URL\b", r"\bS3_ENDPOINT\b", r"\bpymongo\b", r"\baiomysql\b",
    r"\bredis\.Redis\b", r"\bfrom redis\b", r"\bimport redis\b",
)
REAL_TEST_DIR_HINTS = ("integration", "e2e", "endtoend", "real")


def docker_status() -> bool | None:
    if shutil.which("docker") is None:
        return None
    try:
        r = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=8,
        )
        return r.returncode == 0 and bool(r.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        return False


def find_compose(root: Path) -> list[str]:
    out: list[str] = []
    for p in list(root.glob("docker-compose*.y*ml")) + list(root.glob("compose*.y*ml")):
        out.append(str(p.relative_to(root)).replace("\\", "/"))
    return sorted(out)


def find_real_test_dirs(root: Path) -> list[str]:
    tests = root / "tests"
    if not tests.is_dir():
        return []
    out: list[str] = []
    for d in tests.rglob("*"):
        if d.is_dir() and any(h in d.name.lower() for h in REAL_TEST_DIR_HINTS):
            out.append(str(d.relative_to(root)).replace("\\", "/"))
    return sorted(out)


def find_env_signals(root: Path) -> list[str]:
    src = root / "src"
    if not src.is_dir():
        return []
    signals: list[str] = []
    pat = re.compile("|".join(DEP_PATTERNS), re.I)
    for p in src.rglob("*.py"):
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            if pat.search(line):
                signals.append(f"{p.relative_to(root).as_posix()}:{i}")
                if len(signals) >= 30:
                    return signals
    return signals


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 环境依赖探测")
    ap.add_argument("--project-root", default=".", help="项目根路径")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    docker = docker_status()
    compose = find_compose(root)
    real_dirs = find_real_test_dirs(root)
    signals = find_env_signals(root)

    needs = bool(compose or real_dirs or signals)

    # 真实测试命令建议：优先 Makefile 集成目标 > pytest integration 目录
    cmd = None
    if real_dirs:
        cmd = f"pytest {' '.join(real_dirs)} -q"
    elif compose:
        cmd = "docker compose --profile core up -d --wait && <跑集成测试>"

    result = {
        "project_root": str(root),
        "docker_available": docker,
        "compose_files": compose,
        "real_test_dirs": real_dirs,
        "env_dependency_signals": signals,
        "signal_count": len(signals),
        "needs_real_env": needs,
        "recommended_real_test_cmd": cmd,
        "hint": (
            "存在环境依赖功能：实现照做(生产adapter)，只能在真实环境验证的部分登记为"
            "「待真实环境验证」未完成项，禁止砍功能或只写fake（architecture-contracts.md §4.5）"
            if needs else "未发现明显环境依赖信号"
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
