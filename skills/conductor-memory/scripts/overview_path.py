#!/usr/bin/env python3
"""overview 路径定位：用「会话指针文件」锁定唯一 overview，解决同一会话多轮对话写到同一文件。

设计原则：**零外部依赖、所有 agent 通用**。不读任何环境变量（各家不统一），
只读写项目里的一个指针文件 `.conductor-session.json`——任何 agent 都能读写文件。

机制（最小状态）：
  - 指针文件只存 `{"sid":"8位短hash"}`——不写 topic/created/status，减少噪声与敏感信息。
  - 兼容旧 `session_id` 字段：读取时截前 8 位；不再回写完整 UUID。
  - S0 默认读取指针 → 用 sid 定位 overview → append；换任务带 --new-session → 新 sid。
  - 首次生成状态时自动把本地状态文件追加进项目 `.gitignore`。

用法：
  python scripts/overview_path.py --project-root . --topic "M04审查落地"
      → JSON: {session_id, shorthash, path, action: create|append, existed, pointer}

  python scripts/overview_path.py --project-root . --topic "xxx" --new-session
      → 强制开新会话（用户明确换任务时）

  python scripts/overview_path.py --project-root . --topic "xxx" --end-session
      → 结束当前会话（删除指针），下次自动开新的

  python scripts/overview_path.py --project-root . --detect-only
      → 只看当前指针状态，不改文件

文件命名：overviews/YYYY-MM-DD/<shorthash>-<slug>.md
  shorthash = session_id 前 8 位 → 同会话文件名前缀相同，天然归组。
  查找按 shorthash 在整棵 overviews 树递归（同一会话可跨天），找到即 append。

退出码：恒 0（定位脚本不判失败）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

POINTER_NAME = ".conductor-session.json"
STATE_IGNORES = (
    ".conductor-session.json",
    ".commitment-ledger.json",
    ".migration-ledger.json",
    ".purity-baseline.json",
)
DETAIL_SUFFIX = (".review.md", ".review2.md", ".review3.md",
                 ".questions.md", ".debts.md", ".changes.md", ".details.md")


def ensure_ignore(root: Path) -> bool:
    """把 conductor 本地状态文件加入项目 .gitignore；返回是否发生修改。"""
    gi = root / ".gitignore"
    existing = []
    if gi.is_file():
        try:
            existing = gi.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            existing = []
    known = {ln.strip() for ln in existing}
    missing = [name for name in STATE_IGNORES if name not in known]
    if not missing:
        return False
    lines = list(existing)
    if lines and lines[-1].strip():
        lines.append("")
    lines.append("# conductor 本地状态（运行痕迹，不进版本库）")
    lines.extend(missing)
    gi.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def slugify(topic: str) -> str:
    s = re.sub(r'[\\/:*?"<>|]+', "-", topic.strip())
    s = re.sub(r"\s+", "-", s)
    return s[:40] or "session"


def load_pointer(root: Path) -> dict | None:
    p = root / POINTER_NAME
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    sid = data.get("sid") or data.get("session_id")
    return {"sid": str(sid)[:8]} if sid else None


def save_pointer(root: Path, sid: str) -> None:
    p = root / POINTER_NAME
    payload = {"sid": sid[:8]}
    p.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                 encoding="utf-8")
    ensure_ignore(root)


def find_existing(root: Path, shorthash: str) -> Path | None:
    ov = root / "overviews"
    if not ov.is_dir():
        return None
    candidates = [
        p for p in ov.rglob(f"{shorthash}-*.md")
        if not p.name.endswith(DETAIL_SUFFIX)
    ]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor overview 路径定位（会话指针，跨 agent 通用）")
    ap.add_argument("--project-root", default=".", help="项目根路径")
    ap.add_argument("--topic", default="session", help="会话主题（文件名可读部分）")
    ap.add_argument("--new-session", action="store_true", help="强制开新会话（换任务时）")
    ap.add_argument("--end-session", action="store_true", help="结束当前会话（删指针，下次自动开新）")
    ap.add_argument("--detect-only", action="store_true", help="只看指针状态，不改文件")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    slug = slugify(args.topic)
    ptr = load_pointer(root)

    compact = dict(ensure_ascii=False, separators=(",", ":"))

    if args.detect_only:
        print(json.dumps({"sid": ptr["sid"] if ptr else None}, **compact))
        return 0

    # 结束会话：直接删指针，不写 status 字段
    if args.end_session:
        p = root / POINTER_NAME
        if p.is_file():
            p.unlink()
        print(json.dumps({"action": "ended", "sid": ptr["sid"] if ptr else None}, **compact))
        return 0

    # 决定会话短 ID
    need_new = args.new_session or ptr is None
    if need_new:
        sid = str(uuid.uuid4())[:8]
        save_pointer(root, sid)
        src = "new-session" if args.new_session else "first-use"
    else:
        sid = ptr["sid"]
        src = "pointer"

    existing = find_existing(root, sid)
    if existing:
        result = {
            "sid": sid, "source": src,
            "path": str(existing.relative_to(root)).replace("\\", "/"),
            "action": "append",
        }
    else:
        date = datetime.now().strftime("%Y-%m-%d")
        result = {
            "sid": sid, "source": src,
            "path": f"overviews/{date}/{sid}-{slug}.md",
            "action": "create",
        }
    print(json.dumps(result, **compact))
    return 0


if __name__ == "__main__":
    sys.exit(main())
