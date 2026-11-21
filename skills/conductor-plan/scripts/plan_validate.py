#!/usr/bin/env python3
"""执行图校验器：校验 conductor-plan 输出的 JSON 执行图，并可生成 mermaid。

校验（对照 execution-graph-schema.md 第七节）：
  1. 顶层必填字段
  2. 节点必填字段 + 叶子 kind 合法 + exit_criteria 非空
  3. 边端点存在 + loop_back/retry 指向对应控制节点且带 budget
  4. loop/retry 有 max_rounds + on_fail；branch 至少 2 条出边
  5. budget.noop_limit 存在
  6. 无孤儿节点（有入边/出边，入口与终点除外）
  7. 生成 mermaid（可选 --mermaid 输出）

退出码：0 = 图合法；1 = 有违规。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEAF_KINDS = {"tool", "skill", "research", "think", "ask", "gate", "action"}
CONTROL_KINDS = {"branch", "loop", "retry", "parallel", "subplan"}
ALL_KINDS = LEAF_KINDS | CONTROL_KINDS
EDGE_TYPES = {"seq", "cond", "loop_back", "retry", "parallel"}
NODE_REQUIRED = ("id", "kind", "label", "action", "exit_criteria")
TOP_REQUIRED = ("version", "goal", "mode", "nodes", "edges", "budget")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def validate(data: dict) -> None:
    for k in TOP_REQUIRED:
        if k not in data:
            err(f"顶层缺字段：{k}")

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    budget = data.get("budget", {})
    if not isinstance(nodes, list) or not nodes:
        err("nodes 必须是非空数组")
        return
    if not isinstance(edges, list):
        err("edges 必须是数组")
        edges = []

    ids: set[str] = set()
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            err(f"节点 #{i} 不是对象")
            continue
        for k in NODE_REQUIRED:
            if not n.get(k):
                err(f"节点 #{i} 缺字段：{k}")
        nid = n.get("id", f"#{i}")
        if nid in ids:
            err(f"节点 id 重复：{nid}")
        ids.add(nid)
        kind = n.get("kind", "")
        if kind not in ALL_KINDS:
            err(f"节点 {nid} kind 非法：{kind}")
        if kind in CONTROL_KINDS:
            b = n.get("budget") or {}
            if kind in ("loop", "retry"):
                if not b.get("max_rounds"):
                    err(f"控制节点 {nid}({kind}) 缺 budget.max_rounds")
                if not n.get("on_fail"):
                    err(f"控制节点 {nid}({kind}) 缺 on_fail")
            if kind == "branch":
                out = [e for e in edges if e.get("from") == nid]
                if len(out) < 2:
                    err(f"分支节点 {nid} 出边 <2（无法分支）")
        if not n.get("exit_criteria"):
            err(f"节点 {nid} 缺 exit_criteria（无法判定完成）")
        if kind in ("research", "think") and not n.get("serves_task"):
            err(f"调研/分析节点 {nid} 缺 serves_task（必须标明服务于哪个任务）")

    task_ids = {t.get("id") for t in data.get("tasks", []) if isinstance(t, dict)}
    if task_ids:
        for n in nodes:
            if isinstance(n, dict) and n.get("serves_task") and n["serves_task"] not in task_ids:
                err(f"节点 {n.get('id')} 的 serves_task={n['serves_task']} 指向不存在的任务")

    if "noop_limit" not in budget:
        err("顶层 budget 缺 noop_limit（空转防护）")
    if not budget.get("max_steps") and budget.get("max_steps") != 0:
        warn("顶层 budget 未设 max_steps（建议设总步数上限）")

    incoming: dict[str, int] = {i: 0 for i in ids}
    outgoing: dict[str, int] = {i: 0 for i in ids}
    for j, e in enumerate(edges):
        if not isinstance(e, dict):
            err(f"边 #{j} 不是对象")
            continue
        src, dst, typ = e.get("from"), e.get("to"), e.get("type")
        if src not in ids:
            err(f"边 #{j} from 指向不存在的节点：{src}")
        if dst not in ids:
            err(f"边 #{j} to 指向不存在的节点：{dst}")
        if typ not in EDGE_TYPES:
            err(f"边 #{j} type 非法：{typ}")
        if src in incoming:
            outgoing[src] += 1
        if dst in incoming:
            incoming[dst] += 1
        if typ in ("loop_back", "retry"):
            target = next((n for n in nodes if n.get("id") == dst), None)
            want = "loop" if typ == "loop_back" else "retry"
            if target and target.get("kind") != want:
                err(f"边 #{j} 是 {typ}，但目标 {dst} 的 kind 是 {target.get('kind')}（应为 {want}）")

    if len(ids) > 1:
        for nid in ids:
            if incoming[nid] == 0:
                warn(f"节点 {nid} 无入边（确认是否为入口）")
            if outgoing[nid] == 0:
                warn(f"节点 {nid} 无出边（确认是否为终点）")

    if data.get("confidence", 1.0) < 0.5:
        err("confidence < 0.5：信息不足应先澄清，禁止出图")


def to_mermaid(data: dict) -> str:
    lines = ["flowchart TD"]
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    labels = {n.get("id", ""): n.get("label", "") for n in nodes if isinstance(n, dict)}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id", "")
        label = str(n.get("label", "")).replace('"', "'").replace("[", "(").replace("]", ")")
        kind = n.get("kind", "action")
        shape = '{"' + label + '"}' if kind in CONTROL_KINDS else '["' + label + '"]'
        lines.append(f'  {nid}{shape}')
    for e in edges:
        if not isinstance(e, dict):
            continue
        src, dst = e.get("from", ""), e.get("to", "")
        typ = e.get("type", "seq")
        label = str(e.get("label", "")).replace('"', "'")
        arrow = "-->" if typ != "cond" else f"-->|{label or 'cond'}|"
        if typ == "loop_back":
            arrow = f"-.->|{label or 'loop'}|"
        elif typ == "retry":
            arrow = f"-->|{label or 'retry'}|"
        lines.append(f"  {src} {arrow} {dst}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="执行图校验器 + mermaid 生成")
    ap.add_argument("--plan", required=True, help="执行图 JSON 文件")
    ap.add_argument("--mermaid", action="store_true", help="同时输出 mermaid 图")
    ap.add_argument("--mermaid-out", help="mermaid 输出到文件")
    args = ap.parse_args()

    p = Path(args.plan)
    if not p.is_file():
        print(f"[plan] FAIL 文件不存在：{p}")
        return 1
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"[plan] FAIL JSON 解析失败：{e}")
        return 1

    validate(data)
    for w in warnings:
        print(f"[WARN] {w}")
    for e in errors:
        print(f"[FAIL] {e}")

    mermaid = to_mermaid(data)
    if args.mermaid_out:
        Path(args.mermaid_out).write_text(mermaid + "\n", encoding="utf-8")
        print(f"[plan] mermaid 已写入 {args.mermaid_out}")
    elif args.mermaid:
        print("\n```mermaid\n" + mermaid + "\n```")

    if errors:
        print(f"\n> FAIL：{len(errors)} 项错误，执行图不可交付。")
        return 1
    print(f"\n> PASS：图合法（{len(data.get('nodes', []))} 节点 / {len(data.get('edges', []))} 边）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
