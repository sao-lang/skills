#!/usr/bin/env python3
"""overview 路径定位：用「会话指针文件」锁定唯一 overview，解决同一会话多轮对话写到同一文件。

设计原则：**零外部依赖、所有 agent 通用**。不读任何环境变量（各家不统一），
只读写项目里的一个指针文件 `.conductor-session.json`——任何 agent 都能读写文件。

机制：
  - 指针文件存当前会话的 session_id（UUID）；同一会话的所有轮次共享它。
  - S0 默认读取指针 → 用 session_id 短 hash 定位 overview → append。
  - 说"新任务/新会话"时带 --new-session → 生成新 UUID 覆盖指针 → 下一个新文件。
  - 指针不存在（首次）→ 自动创建 → create。

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
        return data if isinstance(data, dict) and data.get("session_id") else None
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None


def save_pointer(root: Path, session_id: str, topic: str, *, ended: bool = False) -> None:
    p = root / POINTER_NAME
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    data = {
        "session_id": session_id,
        "created": now,
        "topic": topic,
        "status": "ended" if ended else "active",
    }
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def find_existing(root: Path, shorthash: str) -> Path | None:
    ov = root / "overviews"
    if not ov.is_dir():
        return None
    DETAIL_SUFFIX = (".review.md", ".review2.md", ".review3.md",
                     ".questions.md", ".debts.md", ".changes.md")
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

    if args.detect_only:
        print(json.dumps({
            "pointer": str(root / POINTER_NAME).replace("\\", "/"),
            "session_id": ptr.get("session_id") if ptr else None,
            "status": ptr.get("status") if ptr else "no-pointer",
            "topic": ptr.get("topic") if ptr else None,
        }, ensure_ascii=False, indent=2))
        return 0

    # 结束会话：删指针，不建 overview
    if args.end_session:
        if ptr:
            save_pointer(root, ptr["session_id"], ptr.get("topic", ""), ended=True)
        print(json.dumps({
            "action": "ended",
            "session_id": ptr.get("session_id") if ptr else None,
        }, ensure_ascii=False, indent=2))
        return 0

    # 决定会话 ID
    need_new = args.new_session or ptr is None or ptr.get("status") == "ended"
    if need_new:
        session_id = str(uuid.uuid4())
        save_pointer(root, session_id, args.topic)
        src = "new-session" if args.new_session else ("first-use" if ptr is None else "after-end")
    else:
        session_id = ptr["session_id"]
        src = "pointer"

    shorthash = session_id[:8]
    existing = find_existing(root, shorthash)
    if existing:
        result = {
            "session_id": session_id, "source": src, "shorthash": shorthash,
            "path": str(existing.relative_to(root)).replace("\\", "/"),
            "action": "append", "existed": True,
            "pointer": POINTER_NAME,
        }
    else:
        date = datetime.now().strftime("%Y-%m-%d")
        result = {
            "session_id": session_id, "source": src, "shorthash": shorthash,
            "path": f"overviews/{date}/{shorthash}-{slug}.md",
            "action": "create", "existed": False,
            "pointer": POINTER_NAME,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
