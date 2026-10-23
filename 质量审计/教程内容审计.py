#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""教程内容审计：结构覆盖 + 穴位覆盖 + 错章检测。

只读：doubao-acupuncture-diagnosis/教程_utf8.txt、针灸篇-知识条目整理.md
输出：同目录 `2026-10-23_内容审计_原始输出.txt`

用法：python 教程内容审计.py
"""
import io
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SK = os.path.join(ROOT, "doubao-acupuncture-diagnosis")
L = io.open(os.path.join(SK, "教程_utf8.txt"), encoding="utf-8", errors="ignore").read().splitlines()
KJ = io.open(os.path.join(SK, "针灸篇-知识条目整理.md"), encoding="utf-8", errors="ignore").read().splitlines()
DOTS = "\u00b7"
BODY_END = 4944          # 正文止于「穴位拼音索引」前

import re


def clean_title(s):
    s = re.sub(r"（[^）]*）", "", s)
    s = re.sub(r"[\u2460-\u2473]", "", s)
    return s.strip()


def bare_sec(s):
    return re.sub(r"^[一二三四五六七八九十]+、", "", clean_title(s)).strip()


# ---------------- 结构 ----------------
chap_at, sec_at, sub_at = [], [], []
for i, l in enumerate(L[:BODY_END]):
    s = l.strip()
    if DOTS in s or not s:
        continue
    if re.match(r"^第[一二三四五六七八九十]+章", s):
        chap_at.append(i)
    elif re.match(r"^[一二三四五六七八九十]+、", s) and len(s) <= 40:
        sec_at.append(i)
    elif re.search(r"（\d+-\d\d:\d\d:\d\d）\s*$", s) and len(s) <= 40:
        sub_at.append(i)

bounds = sorted(set(chap_at + sec_at)) + [BODY_END]


def seg(i):
    nxt = next(b for b in bounds if b > i)
    return "\n".join(L[i:nxt])


def chapter_of(i):
    ch = None
    for j in chap_at:
        if j <= i:
            ch = j
    return ch


body = "\n".join(L[chap_at[0]:BODY_END])

# ---------------- 索引穴位名 ----------------
idx = []
for i in range(5757, min(6562, len(L))):
    s = L[i].strip()
    if DOTS not in s:
        continue
    nm = re.sub(r"\d[\d,\s]*$", "", s.split(DOTS)[0]).strip()
    if re.match(r"^[\u4e00-\u9fff]{2,5}$", nm) and not nm.endswith("划"):
        idx.append(nm)
idx = sorted(set(idx))

# ---------------- 知识条目 ----------------
entries = []
cur_ch = cur_sec = None
for i, l in enumerate(KJ):
    m = re.match(r"^(#{1,3})\s*(.+?)\s*$", l)
    if not m:
        continue
    lvl, t = len(m.group(1)), m.group(2).strip()
    if lvl == 1:
        cur_ch, cur_sec = t, None
    elif lvl == 2:
        cur_sec = t
    entries.append(dict(lvl=lvl, title=t, ch=cur_ch, sec=cur_sec))

kj_all = "\n".join(KJ)
kj_heads = "\n".join(e["title"] for e in entries)

o = ["# 教程内容审计 · 原始输出", ""]
o.append("- 教程 %d 行；正文章节起于 L%d，正文止于 L%d" % (len(L), chap_at[0] + 1, BODY_END))
o.append("- 结构：章 **%d**、节 **%d**、时间戳小节 **%d**" % (len(chap_at), len(sec_at), len(sub_at)))
o.append("- 知识条目：标题 %d（章 %d / 节 %d / 三级 %d）"
         % (len(entries), sum(1 for e in entries if e["lvl"] == 1),
            sum(1 for e in entries if e["lvl"] == 2),
            sum(1 for e in entries if e["lvl"] == 3)))
o.append("- 书末索引穴位名（去重后）：**%d**" % len(idx))
o.append("")

# ---------------- A. 章/节 ----------------
o.append("## A. 章级 / 节级覆盖")
o.append("")
kj_ch = [e["title"] for e in entries if e["lvl"] == 1]
kj_sec = set(clean_title(e["title"]) for e in entries if e["lvl"] == 2)
miss_ch = []
for i in chap_at:
    num = re.match(r"^(第[一二三四五六七八九十]+章)", L[i].strip()).group(1)
    if not any(c.startswith(num) for c in kj_ch):
        miss_ch.append(clean_title(L[i]))
miss_sec = [bare_sec(L[i]) for i in sec_at
            if bare_sec(L[i]) not in set(re.sub(r"^[一二三四五六七八九十]+、", "", s) for s in kj_sec)]
o.append("- 章：%d / %d 覆盖；缺 %s" % (len(chap_at) - len(miss_ch), len(chap_at), miss_ch or "无"))
o.append("- 节：%d / %d 覆盖；缺 %s" % (len(sec_at) - len(miss_sec), len(sec_at), miss_sec or "无"))
o.append("")

# ---------------- B. 穴位覆盖 ----------------
o.append("## B. 穴位覆盖（三级入口径）")
o.append("")
tiers = {"有独立条目": [], "仅正文提及": [], "字面缺失": []}
for p in idx:
    if p in kj_heads:
        tiers["有独立条目"].append(p)
    elif p in kj_all:
        tiers["仅正文提及"].append(p)
    else:
        tiers["字面缺失"].append(p)
o.append("| 级别 | 数量 | 占比 |")
o.append("|---|---|---|")
for k in ("有独立条目", "仅正文提及", "字面缺失"):
    o.append("| %s | %d | %.1f%% |" % (k, len(tiers[k]), 100.0 * len(tiers[k]) / len(idx)))
o.append("")
o.append("### B1. 字面缺失（教程正文出现，但知识条目零次提及）")
o.append("")
o.append("| 穴 | 教程正文次数 |")
o.append("|---|---|")
for p in sorted(tiers["字面缺失"], key=lambda x: -body.count(x)):
    o.append("| %s | %d |" % (p, body.count(p)))
o.append("")
o.append("### B2. 仅正文提及（无独立条目，但正文有提到），全量按正文次数降序")
o.append("")
o.append("| 穴 | 教程正文 | 知识条目提及 |")
o.append("|---|---|---|")
for p in sorted(tiers["仅正文提及"], key=lambda x: -body.count(x)):
    o.append("| %s | %d | %d |" % (p, body.count(p), kj_all.count(p)))
o.append("")

# ---------------- C. 错章 ----------------
o.append("## C. 错章检测（实体锚定）")
o.append("")
o.append("判据：条目标题中的穴位名 → 在教程各「节」的出现次数 → 取最多的节；")
o.append("与条目挂的节不同、且两侧计数均 ≥3 时列为候选。")
o.append("")
sec_txt = {i: seg(i) for i in sec_at}
pt_sec = {}
for p in idx:
    c = Counter()
    for i, t in sec_txt.items():
        n = t.count(p)
        if n:
            c[i] = n
    pt_sec[p] = c

mis = []
for e in entries:
    if e["lvl"] != 3 or not e["sec"]:
        continue
    m = re.search(r"[\u4e00-\u9fff]{2,5}", e["title"])
    if not m or m.group(0) not in idx:
        continue
    p = m.group(0)
    c = pt_sec[p]
    if not c:
        continue
    top_i, top_n = c.most_common(1)[0]
    mine = bare_sec(e["sec"])
    top = bare_sec(L[top_i])
    if mine == top:
        continue
    mine_i = next((i for i in sec_at if bare_sec(L[i]) == mine), None)
    mine_n = c.get(mine_i, 0) if mine_i is not None else 0
    if top_n >= 3 and mine_n >= 3:
        mis.append((e["title"], mine, top, mine_n, top_n))

o.append("| 条目 | 挂在 | 教程最集中 | 计数 |")
o.append("|---|---|---|---|")
for t, a, b, x, y in mis:
    o.append("| %s | %s | %s | %d / %d |" % (t[:18], a, b, x, y))
o.append("")
o.append("错章候选：**%d**" % len(mis))
o.append("")

# ---------------- D. 小节关键词覆盖 ----------------
o.append("## D. 时间戳小节的关键词覆盖（弱判据）")
o.append("")


def terms(t):
    t = re.sub(r"^\d+[、.]", "", t)
    t = re.sub(r"（[^）]*）", "", t).strip()
    t = re.sub(r"^[奇]穴[:：]", "", t)
    return [x for x in re.split(r"[与和、，,/—\-－：:\s]|至", t) if len(x) >= 2]


ok = 0
bad = []
for i in sub_at:
    t = re.sub(r"（\d+-\d\d:\d\d:\d\d）\s*$", "", L[i].strip()).strip()
    ts = terms(t)
    if not ts:
        continue
    if any(x in kj_all or (x.endswith("穴") and x[:-1] in kj_all) or (x + "穴") in kj_all
           for x in ts):
        ok += 1
    else:
        bad.append((t, chapter_of(i)))
o.append("- 小节 %d；关键词命中 **%d**；未命中 **%d**" % (len(sub_at), ok, len(bad)))
o.append("")
for t, ch in bad:
    o.append("- 未命中：%s（%s）"
             % (t[:30], clean_title(L[ch])[:12] if ch is not None else "—"))
o.append("")

# ---------------- E. 局限 ----------------
o.append("## E. 方法局限（必须随结论一起读）")
o.append("")
o.append("1. 知识条目是**深度改写**，实测与教程的最长逐字连续重合仅 4–8 字；")
o.append("   因此任何 n-gram / 相似度判据都不可靠（5-gram 实测 82% 条目 <0.15），本审计**不采用**。")
o.append("2. 结论只建立在两类可验证事实上：(a) 结构标题对齐；(b) 穴位名在具体章节的出现计数。")
o.append("3. 「仅正文提及」不等于漏项——大量穴位是被 `中府穴至经渠` 这类**区间条目**覆盖的。")
o.append("4. 「关键词命中」不等于内容等价，只用于把待复核范围缩小。")

out = os.path.join(HERE, "2026-10-23_内容审计_原始输出.txt")
io.open(out, "w", encoding="utf-8", newline="\n").write("\n".join(o) + "\n")
sys.stdout.buffer.write(("ok -> %s\n" % os.path.basename(out)).encode("utf-8"))
