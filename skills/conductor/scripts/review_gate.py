#!/usr/bin/env python3
"""独立 review 门禁：检查 overview 里是否有"交付前独立 code-quality-review"的客观证据。

用途：conductor 的 S5 阶段（改码场景 finish 前）。把"AI 声称做过独立 review"
变成"overview 里拿得出章节 + 结论 + 报告路径 + 报告文件"的可核对证据。

起因：coding 收尾时执行者自查（运动员当裁判）常漏 L3 功能遗漏/断点；
独立 review 门禁虽已写入 SKILL.md，但仍是"纪律门禁"靠自觉——本脚本把它升级为机器检查。

检查项：
  1. overview 存在「独立 review 结果」章节（或缺省时的豁免声明）
  2. 有 Blocker 清零结论（Blocker = 0 / 已清零 / 无阻塞项）
  3. 有 review 报告路径引用（.review.md 或任意 .md 路径）
  4. 引用的报告文件真实存在（防"写了路径但没生成"的假证据）

退出码：0 = 门禁通过（证据齐全 或 显式豁免）；1 = 证据缺失 / 有未清零 Blocker。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 章节标题识别（大小写不敏感，允许"独立 review 结果 / 独立审查 / independent review"）
SECTION_PATTERNS = (
    r"独立\s*review",
    r"独立\s*审查",
    r"independent\s*review",
)
# Blocker 清零结论识别
CLEAR_PATTERNS = (
    r"blocker\s*[=:]\s*0",
    r"blocker\s*已清零",
    r"无\s*blocker",
    r"无阻塞项",
    r"blocker\s*[:：]\s*无",
    r"0\s*个\s*blocker",
    r"阻塞项\s*[:：]?\s*0",
)
# 未清零信号（命中则 FAIL，即便有清零措辞也以更严格的为准）
BLOCKED_PATTERNS = (
    r"blocker\s*[=:]\s*[1-9]",
    r"blocker\s*未清",
    r"有\s*blocker",
    r"未关闭.*阻塞",
)
# 报告路径引用（匹配 `xxx.review.md` 或反引号里的 .md 路径）
REPORT_PATH_PATTERN = r"[`\s]([\w/\-\.]+\.md)"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def find_section_body(text: str) -> str | None:
    """提取「独立 review 结果」章节正文（从标题到下一个同级 ## 标题）。"""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if any(re.search(p, line, re.I) for p in SECTION_PATTERNS) and (
            line.lstrip().startswith("#") or "独立" in line
        ):
            start = i + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if re.match(r"^##\s", line) and not any(re.search(p, line, re.I) for p in SECTION_PATTERNS):
            break
        body.append(line)
    return "\n".join(body)


def check(overview: Path, waived: bool, waiver_reason: str) -> tuple[bool, list[str]]:
    """返回 (是否通过, 检查明细)。"""
    notes: list[str] = []
    if waived:
        reason = waiver_reason or "调用方声明本场景无代码改动或已豁免"
        return True, [f"WAIVED — 显式豁免：{reason}"]

    if not overview.is_file():
        return False, [f"FAIL — overview 文件不存在：{overview}"]

    text = read_text(overview)
    if not text:
        return False, [f"FAIL — overview 读取失败或为空：{overview}"]

    body = find_section_body(text)
    if body is None:
        return False, [
            "FAIL — overview 中未发现「独立 review 结果」章节。改码场景交付前必须由"
            "全新上下文子代理跑 code-quality-review 并把结论写入该章节；"
            "非改码场景请用 --waived 显式声明豁免。"
        ]

    ok = True
    # 检查 1：章节存在
    notes.append("PASS — 发现「独立 review 结果」章节")

    # 检查 2：Blocker 清零结论 + 未清零信号（后者优先）
    if any(re.search(p, body, re.I) for p in BLOCKED_PATTERNS):
        ok = False
        notes.append("FAIL — 章节内有未清零的 Blocker / 阻塞项信号，禁止 finish")
    elif any(re.search(p, body, re.I) for p in CLEAR_PATTERNS):
        notes.append("PASS — 发现 Blocker 清零结论")
    else:
        ok = False
        notes.append("FAIL — 章节内无明确的 Blocker 清零结论（须写明 Blocker = 0 / 无阻塞项）")

    # 检查 3 + 4：报告路径引用 + 文件真实存在
    refs = re.findall(REPORT_PATH_PATTERN, body)
    report_refs = [r for r in refs if r.lower().endswith(".md")]
    if not report_refs:
        ok = False
        notes.append("FAIL — 未发现 review 报告路径引用（须在章节内写 `xxx.review.md`）")
    else:
        notes.append(f"PASS — 发现报告路径引用：{report_refs[0]}")
        # 报告相对 overview 所在目录解析
        report_path = (overview.parent / report_refs[0]).resolve()
        if report_path.is_file():
            notes.append(f"PASS — 报告文件存在：{report_path.name}")
        else:
            ok = False
            notes.append(
                f"FAIL — 报告文件不存在：{report_path}（写了路径但没生成 = 假证据）"
            )

    return ok, notes


def main() -> int:
    ap = argparse.ArgumentParser(description="conductor 独立 review 门禁")
    ap.add_argument("--overview", required=True, help="本轮 overview 文件路径")
    ap.add_argument(
        "--waived",
        action="store_true",
        help="显式声明豁免（只读/纯文档场景，或确有理由不做独立 review）",
    )
    ap.add_argument("--waiver-reason", default="", help="豁免理由（写入输出与 overview 证据）")
    args = ap.parse_args()

    overview = Path(args.overview).resolve()
    ok, notes = check(overview, args.waived, args.waiver_reason)

    print("# 独立 review 门禁\n")
    for n in notes:
        print(f"- {n}")
    print()
    print("> 退出码 0 = 门禁通过；1 = 证据不足或有未清零 Blocker，禁止 finish / 标完成。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
