#!/usr/bin/env python3
"""投递追踪：用一个 JSON 文件记录投了哪些岗位，并渲染成求职看板。

为什么存在这个脚本：求职过程里"投了哪些、用了哪个简历版本、进行到哪一轮、下一步做
什么"很容易乱。让模型每次手维护一张 Markdown 表格，既容易格式跑偏、又会重复/丢条目。
这里用一个结构化 JSON 做单一数据源，增删改查和看板渲染都走脚本，保证一致、可去重。

数据文件默认 resources/applications.json（相对脚本定位），可用 --store 覆盖。

用法:
    add     新增投递
        python track_application.py add --company 字节跳动 --role "AI产品经理" \
            --status 已投 --resume resume_bytedance.docx --next "等笔试" --jd-link http://...
    update  更新某条（按 id 或 公司+岗位 模糊匹配）
        python track_application.py update --id 2 --status 一面 --next "周四下午面"
        python track_application.py update --match 字节 --status 已挂
    list    列出全部（--json 输出原始数据）
    board   渲染 Markdown 看板（按状态分组）

退出码: 0 成功; 2 入参/匹配错误。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date

# Windows 控制台默认 GBK，会让中文输出乱码甚至抛 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

DEFAULT_STORE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "resources", "applications.json"
)

# 求职管线状态顺序，用于看板分列；不在表里的状态归到"其他"。
PIPELINE = ["想投", "已投", "笔试", "一面", "二面", "三面", "终面", "Offer", "已拒", "已挂"]


def _load(store: str) -> list[dict]:
    if not os.path.exists(store):
        return []
    with open(store, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, list) else data.get("applications", [])


def _save(store: str, items: list[dict]):
    os.makedirs(os.path.dirname(store), exist_ok=True)
    with open(store, "w", encoding="utf-8") as fh:
        json.dump(items, fh, ensure_ascii=False, indent=2)


def _next_id(items: list[dict]) -> int:
    return max((it.get("id", 0) for it in items), default=0) + 1


def cmd_add(args, items):
    # 去重：同公司同岗位已存在则提示用 update
    for it in items:
        if it["company"] == args.company and it["role"] == args.role:
            print(f"[track] 已存在 #{it['id']} {args.company}/{args.role}，"
                  f"请用 update 修改。", file=sys.stderr)
            return 2
    entry = {
        "id": _next_id(items),
        "company": args.company,
        "role": args.role,
        "status": args.status or "想投",
        "resume_version": args.resume or "",
        "jd_link": args.jd_link or "",
        "next_step": args.next or "",
        "notes": args.notes or "",
        "date_applied": args.date or date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    items.append(entry)
    print(f"[track] 已新增 #{entry['id']} {entry['company']} / {entry['role']} "
          f"（状态：{entry['status']}）")
    return 0


def _find(items, args):
    if args.id is not None:
        hits = [it for it in items if it["id"] == args.id]
    else:
        key = args.match or ""
        hits = [it for it in items if key in it["company"] or key in it["role"]]
    return hits


def cmd_update(args, items):
    hits = _find(items, args)
    if not hits:
        print("[track] 没找到匹配的投递记录。", file=sys.stderr)
        return 2
    if len(hits) > 1:
        ids = ", ".join(f"#{h['id']} {h['company']}/{h['role']}" for h in hits)
        print(f"[track] 匹配到多条，请用 --id 指定：{ids}", file=sys.stderr)
        return 2
    it = hits[0]
    for field, val in (
        ("status", args.status), ("resume_version", args.resume),
        ("jd_link", args.jd_link), ("next_step", args.next), ("notes", args.notes),
    ):
        if val is not None:
            it[field] = val
    it["updated"] = date.today().isoformat()
    print(f"[track] 已更新 #{it['id']} {it['company']}/{it['role']} → 状态 {it['status']}")
    return 0


def cmd_list(args, items):
    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    if not items:
        print("（暂无投递记录）")
        return 0
    for it in sorted(items, key=lambda x: x["id"]):
        print(f"#{it['id']:<2} {it['company']} / {it['role']:<16} "
              f"[{it['status']}]  下一步: {it['next_step'] or '—'}  "
              f"简历: {it['resume_version'] or '—'}  ({it['date_applied']})")
    return 0


def cmd_board(args, items):
    if not items:
        print("# 求职看板\n\n_暂无投递记录。用 `add` 新增第一条。_")
        return 0
    groups: dict[str, list[dict]] = {}
    for it in items:
        groups.setdefault(it["status"], []).append(it)

    order = PIPELINE + [s for s in groups if s not in PIPELINE]
    lines = ["# 求职看板", "", f"_共 {len(items)} 条投递_", ""]
    active = total_offer = 0
    for status in order:
        if status not in groups:
            continue
        lines.append(f"## {status}（{len(groups[status])}）")
        for it in sorted(groups[status], key=lambda x: x["updated"], reverse=True):
            nxt = f" → **下一步**: {it['next_step']}" if it["next_step"] else ""
            resume = f" ｜简历: {it['resume_version']}" if it["resume_version"] else ""
            lines.append(f"- **{it['company']}** · {it['role']}{resume}{nxt}  "
                         f"`更新 {it['updated']}`")
        lines.append("")
        if status not in ("已拒", "已挂", "Offer"):
            active += len(groups[status])
        if status == "Offer":
            total_offer += len(groups[status])
    lines.append(f"---\n\n**进行中** {active} 个 ｜ **Offer** {total_offer} 个")
    print("\n".join(lines))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="投递追踪 + 求职看板")
    ap.add_argument("--store", default=DEFAULT_STORE, help="数据文件路径")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="新增投递")
    a.add_argument("--company", required=True)
    a.add_argument("--role", required=True)
    a.add_argument("--status")
    a.add_argument("--resume", help="使用的简历版本/文件名")
    a.add_argument("--jd-link", dest="jd_link")
    a.add_argument("--next", help="下一步动作")
    a.add_argument("--notes")
    a.add_argument("--date", help="投递日期 YYYY-MM-DD，默认今天")

    u = sub.add_parser("update", help="更新投递")
    grp = u.add_mutually_exclusive_group(required=True)
    grp.add_argument("--id", type=int)
    grp.add_argument("--match", help="按公司或岗位关键词模糊匹配")
    u.add_argument("--status")
    u.add_argument("--resume")
    u.add_argument("--jd-link", dest="jd_link")
    u.add_argument("--next")
    u.add_argument("--notes")

    li = sub.add_parser("list", help="列出投递")
    li.add_argument("--json", action="store_true")

    sub.add_parser("board", help="渲染 Markdown 看板")

    args = ap.parse_args()
    items = _load(args.store)

    handlers = {"add": cmd_add, "update": cmd_update, "list": cmd_list, "board": cmd_board}
    rc = handlers[args.cmd](args, items)
    if args.cmd in ("add", "update") and rc == 0:
        _save(args.store, items)
    return rc


if __name__ == "__main__":
    sys.exit(main())
