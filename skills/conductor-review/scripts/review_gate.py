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

lite 档（--lite）：不派独立子代理，改查 overview 的「轻量复核（lite）」章节——
档位标记 + Blocker 清零 + ≥3 条复核项 + ≥2 条带行号/退出码的证据，防"省成本"变成省门禁。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 「独立 review」章节总识别（历史格式含"门禁证据/第2轮/结果"等，统一归为结果章节）
SECTION_PATTERNS = (
    r"独立\s*review",
    r"独立\s*审查",
    r"independent\s*review",
)
# 内嵌报告章节识别（报告正文直接写进 overview，替代外部 .md 文件）——优先于结果章节
REPORT_SECTION_PATTERNS = (
    r"独立\s*review\s*报告",
    r"独立\s*审查\s*报告",
    r"review\s*报告\s*附录",
    r"independent\s*review\s*report",
)
# lite 档轻量复核章节
LITE_SECTION_PATTERNS = (
    r"轻量\s*复核",
    r"轻量\s*review",
    r"lite\s*review",
)
LITE_TIER_PATTERN = r"档位\s*[:：]\s*lite"
LITE_EVIDENCE_PATTERN = re.compile(
    r"(退出码\s*[01]|[:：]\s*\d+|file\s*:\s*line)", re.I
)


def is_report_heading(line: str) -> bool:
    return bool(re.match(r"^##\s", line) and any(re.search(p, line, re.I) for p in REPORT_SECTION_PATTERNS))


def is_result_heading(line: str) -> bool:
    return bool(
        re.match(r"^##\s", line)
        and any(re.search(p, line, re.I) for p in SECTION_PATTERNS)
        and not is_report_heading(line)
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


def _section_body(text: str, heading_pred) -> str | None:
    """按标题判定函数提取某类 ## 章节正文（到下一个同级 ## 标题）。"""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if heading_pred(line):
            start = i + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if re.match(r"^##\s", line):
            break
        body.append(line)
    return "\n".join(body)


def find_section_body(text: str) -> str | None:
    """提取「独立 review 结果」章节（排除内嵌报告章节）。

    多轮 review 的历史文档可能有多个结果章节（第1轮 Blocker>0、第2轮清零）。
    优先取标题含"最终/final/清零"的章节，避免误判中间状态为未通过。
    """
    final_pred = lambda line: is_result_heading(line) and bool(
        re.search(r"最终|final|清零后|结论", line, re.I)
    )
    return _section_body(text, final_pred) or _section_body(text, is_result_heading)


def find_embedded_report(text: str) -> str | None:
    """提取内嵌的「独立 review 报告」——从标题抓到文件末尾。

    报告正文自带 `## 一、结论` 等小节标题，若按常规 `##` 截断会只抓到开头、
    丢失分级/finding 证据。报告通常是主文件最后一章，故一直读到末尾。
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if is_report_heading(line):
            return "\n".join(lines[i + 1:])
    return None


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

    # 检查 3 + 4：报告证据存在（内嵌章节 或 外部报告文件，二选一）
    embedded = find_embedded_report(text)
    if embedded and len(embedded.strip()) >= 80 and re.search(
        r"blocker|should|nit|finding|文件:行号|证据|file:line", embedded, re.I
    ):
        notes.append(f"PASS — 发现内嵌「独立 review 报告」章节（{len(embedded)} 字符，含分级/证据）")
    else:
        # 回退：外部 .md 报告路径引用 + 文件真实存在（兼容历史文档）
        refs = re.findall(REPORT_PATH_PATTERN, body)
        report_refs = [r for r in refs if r.lower().endswith(".md")]
        if not report_refs:
            ok = False
            notes.append(
                "FAIL — 未发现 review 证据：既无内嵌「独立 review 报告」章节，"
                "也无外部报告路径引用（须内嵌报告正文或在章节内写 `xxx.review.md`）"
            )
        else:
            notes.append(f"PASS — 发现报告路径引用：{report_refs[0]}")
            all_exist = True
            for ref in report_refs:
                rp = (overview.parent / ref).resolve()
                if not rp.is_file():
                    ok = False
                    all_exist = False
                    notes.append(f"FAIL — 报告文件不存在：{rp}（写了路径但没生成 = 假证据）")
            if all_exist:
                notes.append(f"PASS — {len(report_refs)} 个报告文件均存在")

    return ok, notes


def find_lite_section(text: str) -> str | None:
    """提取 lite 档「轻量复核」章节正文（到下一个同级 ## 标题）。"""
    def is_lite_heading(line: str) -> bool:
        return bool(
            re.match(r"^##\s", line)
            and any(re.search(p, line, re.I) for p in LITE_SECTION_PATTERNS)
        )
    return _section_body(text, is_lite_heading)


def check_lite(overview: Path) -> tuple[bool, list[str]]:
    """lite 档门禁：轻量复核章节 + 档位 + Blocker 清零 + 三项复核 + 证据。"""
    notes: list[str] = []
    if not overview.is_file():
        return False, [f"FAIL — overview 文件不存在：{overview}"]
    text = read_text(overview)
    if not text:
        return False, [f"FAIL — overview 读取失败或为空：{overview}"]

    body = find_lite_section(text)
    if body is None:
        return False, [
            "FAIL — 未发现「轻量复核（lite）」章节。lite 档不派独立子代理，"
            "但必须写三问复核（意图一致/边界与错误/证据）到该章节；"
            "若已超 lite 条件请升档走独立 review。"
        ]

    ok = True
    notes.append("PASS — 发现「轻量复核（lite）」章节")

    if re.search(LITE_TIER_PATTERN, body, re.I):
        notes.append("PASS — 发现档位标记：lite")
    else:
        ok = False
        notes.append("FAIL — 章节内缺少 `档位: lite` 标记，无法确认适用 lite 门禁")

    if any(re.search(p, body, re.I) for p in BLOCKED_PATTERNS):
        ok = False
        notes.append("FAIL — 轻量复核发现未清零 Blocker，必须升 standard 派独立子代理")
    elif any(re.search(p, body, re.I) for p in CLEAR_PATTERNS):
        notes.append("PASS — 发现 Blocker 清零结论")
    else:
        ok = False
        notes.append("FAIL — 章节内无明确的 Blocker = 0 / 无阻塞项结论")

    bullets = re.findall(r"^\s*[-*+]\s+(.+)$", body, re.M)
    if len(bullets) >= 3:
        notes.append(f"PASS — 复核项 {len(bullets)} 条（要求 ≥3）")
    else:
        ok = False
        notes.append(f"FAIL — 复核项仅 {len(bullets)} 条（要求 ≥3：意图一致/边界与错误/证据）")

    evidenced = [b for b in bullets if LITE_EVIDENCE_PATTERN.search(b)]
    if len(evidenced) >= 2:
        notes.append(f"PASS — {len(evidenced)} 条复核项带行号或退出码证据（要求 ≥2）")
    else:
        ok = False
        notes.append("FAIL — 带 `文件:行号` 或 `退出码 N` 的复核项不足 2 条，禁止 finish")

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
    ap.add_argument(
        "--lite",
        action="store_true",
        help="lite 档：校验 overview 的「轻量复核（lite）」章节，替代独立子代理 review",
    )
    args = ap.parse_args()

    if args.lite and args.waived:
        print("# review 门禁\n\n- FAIL — --lite 与 --waived 不能同时使用（lite 档也必须留复核证据）")
        return 1

    overview = Path(args.overview).resolve()
    if args.lite:
        ok, notes = check_lite(overview)
        title = "# 轻量复核门禁（lite 档）"
    else:
        ok, notes = check(overview, args.waived, args.waiver_reason)
        title = "# 独立 review 门禁"

    print(f"{title}\n")
    for n in notes:
        print(f"- {n}")
    print()
    print("> 退出码 0 = 门禁通过；1 = 证据不足或有未清零 Blocker，禁止 finish / 标完成。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
