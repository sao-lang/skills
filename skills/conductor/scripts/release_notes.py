#!/usr/bin/env python3
"""发布说明草稿：从 conventional commits 生成 CHANGELOG 段落 + 版本号建议。

用途：conductor 发布编排（../references/04-guards/release-checklist.md）——
把 `git log` 的 conventional commits 按类型分组，生成 CHANGELOG 草稿，并据提交类型
给出语义化版本号建议。草稿需人工润色为"用户可理解的变化"，不直接当最终版发布。

分组（Conventional Commits）：
  feat→新增 / fix→修复 / perf→性能 / refactor→重构 / docs→文档 / chore→杂项 / 其他→其他
  BREAKING CHANGE 或 `feat!:`/`fix!:` → 破坏性变更（单独列出，版本建议 MAJOR）

版本建议：有破坏性→MAJOR；仅有 feat→MINOR；只有 fix/perf/refactor→PATCH；无约定提交→?

用法：
  python scripts/release_notes.py --since v1.2.0
  python scripts/release_notes.py --since v1.2.0 --repo /path/to/repo --format json
退出码：恒为 0（草稿）；--repo 非 git 仓库时报错返回 1。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path

TYPE_LABELS = OrderedDict([
    ("feat", "新增"), ("fix", "修复"), ("perf", "性能"), ("refactor", "重构"),
    ("docs", "文档"), ("chore", "杂项"),
])
COMMIT_RE = re.compile(r"^(\w+)(!)?(?:\([^)]*\))?\s*:\s*(.+)$")


def git_log(repo: Path, since: str | None) -> list[str]:
    rng = f"{since}..HEAD" if since else "-20"
    cmd = ["git", "-C", str(repo), "log", "--pretty=format:%s", "--no-merges"]
    cmd.append(rng if since else "-n")
    if not since:
        cmd.append("20")
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[release_notes] git log 失败：{e}", file=sys.stderr)
        return []


def parse(subjects: list[str]) -> tuple[dict[str, list[str]], bool, set[str]]:
    groups: dict[str, list[str]] = {label: [] for label in TYPE_LABELS.values()}
    groups["其他"] = []
    breaking: list[str] = []
    has_breaking = False
    types_seen: set[str] = set()
    for s in subjects:
        m = COMMIT_RE.match(s)
        if not m:
            groups["其他"].append(s)
            continue
        typ, bang, desc = m.group(1).lower(), m.group(2), m.group(3)
        types_seen.add(typ)
        label = TYPE_LABELS.get(typ)
        entry = f"- {desc}"
        if bang or "BREAKING CHANGE" in desc.upper():
            has_breaking = True
            breaking.append(entry)
        if label:
            groups[label].append(entry)
        else:
            groups["其他"].append(f"- `{typ}` {desc}")
    if breaking:
        groups["破坏性变更"] = breaking
    return groups, has_breaking, types_seen


def suggest_version(has_breaking: bool, types: set[str]) -> str:
    if has_breaking:
        return "MAJOR (x.0.0)"
    if "feat" in types:
        return "MINOR (x.Y.0)"
    if types & {"fix", "perf", "refactor"}:
        return "PATCH (x.y.Z)"
    return "? (未发现约定提交，需人工判定)"


def render_md(groups: dict[str, list[str]], version: str, since: str | None) -> str:
    scope = f"（自 {since}）" if since else "（最近 20 条）"
    lines = [f"# CHANGELOG 草稿 {scope}", "", f"版本建议：**{version}**", ""]
    order = ["破坏性变更"] + list(TYPE_LABELS.values()) + ["其他"]
    any_content = False
    for label in order:
        items = groups.get(label, [])
        if not items:
            continue
        any_content = True
        lines.append(f"## {label}（{len(items)}）")
        lines.extend(items)
        lines.append("")
    if not any_content:
        lines.append("无提交记录。")
    lines.append("> 草稿仅供润色：改为用户可理解的表述，删内部术语；破坏性变更需醒目提示。")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 发布说明草稿（conventional commits）")
    ap.add_argument("--since", default="", help="起始 tag/ref（如 v1.2.0）；缺省取最近 20 条提交")
    ap.add_argument("--repo", default=".", help="git 仓库路径")
    ap.add_argument("--format", choices=("md", "json"), default="md", help="输出格式")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / ".git").exists():
        print(f"[release_notes] 非 git 仓库：{repo}", file=sys.stderr)
        return 1
    since = args.since.strip() or None
    subjects = git_log(repo, since)
    groups, has_breaking, types = parse(subjects)
    version = suggest_version(has_breaking, types)

    if args.format == "json":
        print(json.dumps({
            "repo": str(repo), "since": since, "commits": len(subjects),
            "version_suggestion": version, "groups": groups,
        }, ensure_ascii=False, indent=2))
    else:
        print(render_md(groups, version, since))
    return 0


if __name__ == "__main__":
    sys.exit(main())
