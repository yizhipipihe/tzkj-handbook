#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在题库里检索题目，供 AI 在回答问题前取证。

用法示例：
    python scripts/search.py 转专业
    python scripts/search.py 奖学金 比例 --topic 04 -n 5
    python scripts/search.py --id TF-022
    python scripts/search.py 请假 --type 填空题
    python scripts/search.py --list-topics
    python scripts/search.py 处分 --json

输出默认是便于阅读的文本；加 --json 输出机器可读结果。
"""

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "questions.jsonl")


def load():
    if not os.path.exists(DATA):
        sys.exit(f"找不到题库数据：{DATA}")
    with open(DATA, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def haystack(rec):
    parts = [rec["stem"], rec["answer"]]
    for o in rec["options"]:
        parts.append(o["key"] + o["text"])
    return "\n".join(parts)


def score(rec, terms):
    text = haystack(rec)
    total = 0
    for t in terms:
        n = text.count(t)
        if n:
            total += n * (3 if t in rec["stem"] else 1)
    return total


def render(rec, show_options=True):
    head = f"[{rec['id']}] {rec['type']} · {rec.get('topic_name', rec['topic'])}"
    lines = [head, f"Q: {rec['stem']}"]
    if show_options and rec["options"]:
        for o in rec["options"]:
            lines.append(f"   {o['key']}. {o['text']}")
    lines.append(f"A: {rec['answer']}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="检索学生手册题库")
    ap.add_argument("terms", nargs="*", help="关键词，可多个（空格分隔）")
    ap.add_argument("--id", help="按题号取题，如 TF-001")
    ap.add_argument("--topic", help="按主题前缀过滤，如 06 或 公寓")
    ap.add_argument("--type", help="按题型过滤：填空题/判断题/单选题/多选题")
    ap.add_argument("-n", type=int, default=8, help="返回条数上限，默认 8")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--list-topics", action="store_true", help="列出主题及题量")
    ap.add_argument("--no-options", action="store_true", help="不显示选项")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    recs = load()

    if args.list_topics:
        seen = {}
        for r in recs:
            name = r.get("topic_name", r["topic"])
            seen[name] = seen.get(name, 0) + 1
        for topic, n in sorted(seen.items()):
            print(f"{topic}: {n} 题")
        print(f"合计: {len(recs)} 题")
        return

    if args.id:
        for r in recs:
            if r["id"].lower() == args.id.lower():
                print(render(r, not args.no_options))
                return
        sys.exit(f"没有找到题号 {args.id}")

    hits = recs
    if args.topic:
        hits = [r for r in hits
                if r["topic"].startswith(args.topic) or args.topic in r.get("topic_name", "")]
    if args.type:
        hits = [r for r in hits if r["type"] == args.type]

    if args.terms:
        scored = [(score(r, args.terms), r) for r in hits]
        scored = [(s, r) for s, r in scored if s > 0]
        scored.sort(key=lambda x: (-x[0], x[1]["id"]))
        hits = [r for _, r in scored][: args.n]
    else:
        hits = hits[: args.n]

    if not hits:
        print("没有匹配的题目。可换关键词，或用 --topic / --type 放宽条件。")
        return

    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
    else:
        print(f"命中 {len(hits)} 题（共 {len(recs)} 题）\n")
        for r in hits:
            print(render(r, not args.no_options))
            print()


if __name__ == "__main__":
    main()
