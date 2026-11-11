#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「学生手册」原始 TXT 题库解析成结构化数据，并按主题生成 references 文档。

用法:
    python scripts/build_bank.py <源文件.txt> [--repo-root <仓库根目录>]

输出:
    data/questions.jsonl      每行一条题目记录
    data/questions.csv        便于用表格软件打开
    references/by-topic/*.md  按主题分组的可读题库(原文照录)
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

TYPE_CODE = {"填空题": "TF", "判断题": "PD", "单选题": "SC", "多选题": "MC"}
TYPE_ORDER = ["填空题", "判断题", "单选题", "多选题"]

# 主题关键词：(主题键, 显示名, 关键词列表)
TOPICS = [
    ("xueji", "01-学籍与注册", [
        "注册", "学籍", "转专业", "转学", "休学", "复学", "退学", "新生", "入学资格",
        "毕业", "结业", "肄业", "学生证", "档案", "学制", "最长学习年限", "报到",
        "入伍", "应征", "离校", "变更", "信息核对",
    ]),
    ("kaoshi", "02-考试与成绩", [
        "考试", "考场", "监考", "补考", "重修", "缓考", "成绩", "课程", "学分",
        "教材", "选课", "上课", "试卷", "学业", "课堂", "作业",
    ]),
    ("kaoping", "03-综合素质考评", [
        "德育", "考评", "综合考评", "综合素质", "基准分", "加分", "扣分", "体能素质",
        "文化专业素质", "美育", "劳动教育", "德育学分", "考评成绩", "考评办法",
    ]),
    ("jiangzhu", "04-奖助学金与评优", [
        "奖学金", "助学金", "励志", "评优", "三好学生", "优秀学生干部", "先进班级",
        "优良学风班", "优秀毕业生", "积极分子", "荣誉", "奖金", "评选", "评比",
        "名额", "表彰", "评先",
    ]),
    ("jilv", "05-纪律与处分", [
        "处分", "违纪", "违规", "警告", "记过", "留校察看", "开除学籍", "通报批评",
        "申诉", "作弊", "旷课", "打架", "斗殴", "偷窃", "赌博", "酗酒", "吸烟",
        "处分期限", "解除处分",
    ]),
    ("gongyu", "06-学生公寓与住宿", [
        "公寓", "寝室", "宿舍", "住宿学生", "校外住宿", "文明寝室", "学习型寝室", "违禁电器", "夜不归宿",
        "留宿", "床位", "退宿", "门禁", "熄灯", "内务", "电炉", "热得快",
    ]),
    ("qingjia", "07-请假、考勤与出入校门", [
        "请假", "销假", "补假", "假条", "考勤", "点名", "校门", "门卫", "出入",
        "外出", "进出", "出入证", "审批", "三天", "一周",
    ]),
    ("xingwei", "08-行为规范与校园秩序", [
        "集会", "礼仪", "礼貌", "尊敬师长", "公共场所", "楼道", "喧哗", "文明",
        "会客", "来访", "商户", "经营", "租房", "宗教", "安全", "消防", "交通",
        "机动车", "诈骗", "食堂", "就餐", "绿色学校", "垃圾分类", "光盘", "节能",
        "环保", "生态文明", "节约", "垃圾", "仪表", "自尊自爱", "他人房间", "打断",
        "发言", "烟花爆竹", "思想品德", "品德", "散会", "会场", "就座",
    ]),
    ("shetuan", "09-社团、班集体与学生组织", [
        "社团", "学生会", "团委", "班集体", "班级", "活动", "志愿者", "社会实践",
        "军训", "军事训练", "升旗", "国旗", "章程", "指导员", "纳新", "学生组织", "班长",
    ]),
    ("tushu", "10-图书借阅与体育", [
        "图书", "借阅", "阅览", "书刊", "期刊", "现刊", "超期", "赔偿", "阳光长跑",
        "体育", "体质", "运动", "锻炼", "体测", "场馆", "健康标准",
    ]),
    ("zizhu", "11-学生资助与勤工助学", [
        "勤工助学", "岗位", "酬金", "资助", "资助对象", "发展性资助", "认定",
        "家庭经济", "低保", "建档立卡", "退役士兵", "征兵", "学费补偿", "助学贷款",
        "减免", "保险", "慰问金", "困难", "补助", "六位一体", "专款专用", "资金",
    ]),
]

UNCLASSIFIED = ("other", "99-未分类")


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u3000", " ")
    return text


def clean_line(line: str) -> str:
    return line.strip().strip("\ufeff").strip()


PAGE_REF = re.compile(r"P\s*\d{1,4}")


def join_wrapped(parts):
    """把被硬换行拆开的句子拼回去：中文直接相连，英文/数字之间补空格。"""
    out = ""
    for piece in parts:
        p = piece.strip()
        if not p:
            continue
        if not out:
            out = p
            continue
        prev, nxt = out[-1], p[0]
        if prev.isascii() and prev.isalnum() and nxt.isascii() and nxt.isalnum():
            out += " " + p
        else:
            out += p
    return out


OPTION_RE = re.compile(r"^([A-EＡ-Ｅ])\s*(?:[\.\、,，:：\)）]\s*)?([^\s].*)$")
OPTION_BARE_RE = re.compile(r"^([A-EＡ-Ｅ])\s*(?:[\.\、,，:：\)）])?\s*$")
ANSWER_MARK_RE = re.compile(r"(?:参考答案|正确答案|标准答案)\s*[:：;；]?\s*(.*)$")
JUDGE_TOKEN_RE = re.compile(r"^[:：]?\s*(对|错|正确|错误|√|×|T|F)\s*[。.]?$")
JUDGE_GLUED_RE = re.compile(r"[:：]\s*(对|错|正确|错误)\s*[。.]?\s*$")
TAIL_LETTERS_RE = re.compile(r"([。；;，,\s])\s*([A-E]{1,5})\s*$")
QSTART_RE = re.compile(r"^(\d{1,3})\s*[\.、]\s*\(\s*(填空题|判断题|单选题|多选题)\s*\)\s*(.*)$")


def parse_blocks(text: str):
    lines = [clean_line(l) for l in normalize(text).split("\n")]
    starts = []
    for idx, line in enumerate(lines):
        m = QSTART_RE.match(line)
        if m:
            starts.append((idx, int(m.group(1)), m.group(2), m.group(3)))
    blocks = []
    section = 0
    last_no = 0
    for k, (idx, no, qtype, tail) in enumerate(starts):
        if k > 0 and (no == 1 or no < last_no):
            section += 1
        last_no = no
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        body = [tail] + lines[idx + 1:end]
        blocks.append({"no": no, "type": qtype, "section": section, "lines": body})
    return blocks


def parse_block(block):
    qtype = block["type"]
    body = [PAGE_REF.sub("", l).strip() if PAGE_REF.search(l) else l for l in block["lines"]]

    # 1) 定位答案起始行
    ans_idx = None
    inline_answer = ""
    for i, line in enumerate(body):
        if i == 0:
            continue
        m = ANSWER_MARK_RE.search(line)
        if m:
            ans_idx = i
            inline_answer = m.group(1).strip()
            break
    if ans_idx is None and qtype == "判断题":
        for i in range(len(body) - 1, 0, -1):
            if JUDGE_TOKEN_RE.match(body[i]):
                ans_idx = i
                inline_answer = body[i].strip()
                break
    if ans_idx is None and qtype in ("单选题", "多选题"):
        last = max((i for i, l in enumerate(body) if l), default=None)
        if last is not None and last > 0 and re.fullmatch(r"[A-E]{1,5}", body[last].strip()):
            ans_idx = last
            inline_answer = body[last].strip()
    stem_lines = body if ans_idx is None else body[:ans_idx]
    ans_lines = [] if ans_idx is None else body[ans_idx:]

    # 2) 拆题干与选项：选项以 A-E 开头，后续行可能是上一个选项的折行
    stem_parts, options = [], []
    cur_opt = None
    for line in stem_lines:
        if not line:
            continue
        m_opt = OPTION_RE.match(line)
        if m_opt:
            cur_opt = {"key": m_opt.group(1), "text": m_opt.group(2).strip()}
            options.append(cur_opt)
            continue
        m_bare = OPTION_BARE_RE.match(line)
        if m_bare:
            cur_opt = {"key": m_bare.group(1), "text": ""}
            options.append(cur_opt)
            continue
        if cur_opt is not None:
            cur_opt["text"] = cur_opt["text"] + line.strip()
        else:
            stem_parts.append(line)
    stem = join_wrapped(stem_parts).strip()

    # 3) 答案本体（标记行内联内容 + 其后的续行）
    payload_parts = []
    if ans_lines:
        if inline_answer:
            payload_parts = [inline_answer] + [l for l in ans_lines[1:] if l]
        else:
            payload_parts = [l for l in ans_lines if l]
    payload_text = "\n".join([p for p in payload_parts if p]).strip()

    # 4) 兜底：答案被黏在题干或最后一个选项末尾
    if not payload_text:
        glued = JUDGE_GLUED_RE.search(stem)
        if qtype == "判断题" and glued:
            payload_text = glued.group(1)
            stem = JUDGE_GLUED_RE.sub("", stem).strip()
        elif options:
            m = TAIL_LETTERS_RE.search(options[-1]["text"])
            if m and qtype in ("单选题", "多选题"):
                payload_text = m.group(2)
                options[-1]["text"] = TAIL_LETTERS_RE.sub(m.group(1), options[-1]["text"]).strip()
    if not payload_text and qtype == "判断题":
        m = TAIL_LETTERS_RE.search(stem)
        if m and JUDGE_TOKEN_RE.match(m.group(2)):
            payload_text = m.group(2)
            stem = TAIL_LETTERS_RE.sub(m.group(1), stem).strip()

    blanks = []
    if qtype == "填空题":
        for line in payload_text.split("\n"):
            m = re.match(r"[\(（]\s*\d+\s*[\)）]\s*(.*)$", line.strip())
            if m:
                blanks.append(m.group(1).strip())
        if not blanks and payload_text:
            blanks = [payload_text.replace("\n", " ").strip()]
    letters = ""
    if qtype in ("单选题", "多选题"):
        letters = "".join(sorted(set(re.sub(r"[^A-E]", "", payload_text.upper()))))
    judge = None
    if qtype == "判断题":
        norm = payload_text.strip().strip("。.").lstrip(":：").strip()
        if norm in ("对", "正确", "√", "T", "True", "true"):
            judge = True
        elif norm in ("错", "错误", "×", "F", "False", "false"):
            judge = False

    answered = bool(blanks) or bool(letters) or judge is not None
    return {
        "stem": stem,
        "options": options,
        "answer_raw": payload_text,
        "blanks": blanks,
        "letters": letters,
        "judge": judge,
        "answered": answered,
    }


def classify(stem: str, options) -> str:
    text = stem + "".join(o["text"] for o in options)
    scores = defaultdict(int)
    for key, _name, words in TOPICS:
        for w in words:
            n = text.count(w)
            if n:
                scores[key] += n
    if not scores:
        return UNCLASSIFIED[0]
    top = max(scores.values())
    for key, _name, _words in TOPICS:
        if scores.get(key, 0) == top:
            return key
    return UNCLASSIFIED[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--repo-root", default=None)
    args = ap.parse_args()
    repo_root = args.repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(args.source, "rb") as f:
        data = f.read()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = data.decode("utf-16")
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("gb18030")

    blocks = parse_blocks(text)
    records = []
    seq = Counter()
    topic_names = {k: n for k, n, _ in TOPICS}
    topic_names[UNCLASSIFIED[0]] = UNCLASSIFIED[1]
    for b in blocks:
        parsed = parse_block(b)
        seq[b["type"]] += 1
        if b["type"] == "判断题":
            display = {True: "对", False: "错"}.get(parsed["judge"], parsed["answer_raw"].strip())
        elif b["type"] == "填空题":
            display = "；".join(parsed["blanks"]) if parsed["blanks"] else parsed["answer_raw"].strip()
        else:
            display = parsed["letters"] or parsed["answer_raw"].strip()
        rec = {
            "id": f"{TYPE_CODE[b['type']]}-{seq[b['type']]:03d}",
            "type": b["type"],
            "source_section": b["section"] + 1,
            "source_no": b["no"],
            "stem": parsed["stem"],
            "options": [{"key": o["key"], "text": o["text"]} for o in parsed["options"]],
            "answer": display,
            "answer_raw": parsed["answer_raw"],
            "answer_blanks": parsed["blanks"],
            "answer_letters": parsed["letters"],
            "answer_bool": parsed["judge"],
            "answered": parsed["answered"],
            "topic": classify(parsed["stem"], parsed["options"]),
            "topic_name": topic_names[classify(parsed["stem"], parsed["options"])],
        }
        records.append(rec)

    os.makedirs(os.path.join(repo_root, "data"), exist_ok=True)
    jsonl_path = os.path.join(repo_root, "data", "questions.jsonl")
    with open(jsonl_path, "w", encoding="utf-8", newline="\n") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    csv_path = os.path.join(repo_root, "data", "questions.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "topic", "stem", "options", "answer", "answer_blanks", "answered"])
        for r in records:
            opts = " | ".join(f"{o['key']}.{o['text']}" for o in r["options"])
            w.writerow([r["id"], r["type"], topic_names[r["topic"]], r["stem"], opts,
                        r["answer"].replace("\n", " "), " / ".join(r["answer_blanks"]),
                        "Y" if r["answered"] else "N"])

    # 按主题输出可读题库
    out_dir = os.path.join(repo_root, "references", "by-topic")
    os.makedirs(out_dir, exist_ok=True)
    # 清掉上一轮生成的主题文件，避免旧主题残留
    for name in os.listdir(out_dir):
        if name.endswith(".md"):
            os.remove(os.path.join(out_dir, name))
    groups = defaultdict(list)
    for r in records:
        groups[r["topic"]].append(r)
    order = [k for k, _, _ in TOPICS] + [UNCLASSIFIED[0]]
    written = []
    for key in order:
        items = groups.get(key, [])
        if not items:
            continue
        name = topic_names[key]
        path = os.path.join(out_dir, name + ".md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {name.split('-', 1)[-1]}\n\n")
            f.write(f"共 {len(items)} 题。每题标注题号（对应 data/questions.jsonl 的 id），答案原文照录。\n\n")
            f.write("| 题号 | 类型 | 题目 |\n|---|---|---|\n")
            for r in items:
                f.write(f"| {r['id']} | {r['type']} | {r['stem'].replace('|', '｜')} |\n")
            f.write("\n---\n\n")
            for r in items:
                f.write(f"### {r['id']} · {r['type']}\n\n")
                f.write(f"**题目**：{r['stem']}\n\n")
                if r["options"]:
                    for o in r["options"]:
                        f.write(f"- {o['key']}. {o['text']}\n")
                    f.write("\n")
                f.write(f"**答案**：{format_answer(r)}\n\n")
        written.append((name, len(items)))

    stats = Counter(r["type"] for r in records)
    unanswered = [r["id"] for r in records if not r["answered"]]
    print("已生成记录:", len(records))
    for t in TYPE_ORDER:
        print(f"  {t}: {stats.get(t, 0)}")
    print("主题分布:")
    for name, n in written:
        print(f"  {name}: {n}")
    print("未解析出答案:", len(unanswered), unanswered[:20])


def format_answer(r):
    return r["answer"]


if __name__ == "__main__":
    main()
