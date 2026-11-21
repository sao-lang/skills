#!/usr/bin/env python3
"""兼容 shim：实际实现见 ../../conductor-review/scripts/review_gate.py。

保留 conductor/scripts 入口，实现唯一真相源在器官目录。
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[2] / "conductor-review" / "scripts" / "review_gate.py"
if __name__ == "__main__":
    sys.path.insert(0, str(_TARGET.parent))
    runpy.run_path(str(_TARGET), run_name="__main__")
