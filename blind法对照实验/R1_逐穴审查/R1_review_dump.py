#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R1 逐穴临床正当性审查：只读取数。

对 v16 新增删除案的八脉单元（160_01/207_01/303_01 的 列缺/照海），
导出：原文症情全文、v14r5 主穴与分层与依据、v15/v16 两版词表命中词、
gold、以及原书 列缺/照海 主治行号摘录。

只读；只写本目录。
"""
import csv
import io
import json
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
assert EXP
BENCH = os.path.join(EXP, "benchmark_v2")
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")

sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
KW_OLD = spec["单元证候关键词"]
KW_NEW = json.load(io.open(os.path.join(PM, "PM_原书词表.json"), encoding="utf-8"))["单元证候关键词"]
ADD = spec["已登记规则追加关键词"]

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
GOLD = {c: list(NEW[c]["gold_members"]) for c in gold["case_ids"]}

PRED = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))

CASES = ["160_01", "207_01", "303_01"]
CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    for c in str(r["案号列表"]).split():
        CHAINS[c] = r["链ID"]


def sym_text(c):
    p = os.path.join(SD, "%s_symptoms_v2.json" % c)
    d = json.load(io.open(p, encoding="utf-8"))
    buf = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            buf.append(str(v["片段"]))
        elif isinstance(v, str):
            buf.append(v)
    return "【原始输入全文】" + "".join(buf)


out = []
for c in CASES:
    out.append("=" * 100)
    out.append("### 案 %s  （链 %s）" % (c, CHAINS.get(c, "?")))
    out.append(sym_text(c))
    rec = PRED[c]
    out.append("")
    out.append("【v14r5 主穴】" + "、".join(rec.get("主穴", [])))
    lay = rec.get("主穴分层") or {}
    for k, v in lay.items():
        out.append("  层 %s：%s" % (k, "、".join(v)))
    recs = {str(e.get("穴", "")).strip(): e for e in (rec.get("主穴记录", []) or [])}
    out.append("")
    out.append("【八脉层单元明细】")
    layer_units = [u for u in rec.get("主穴", []) if (lay.get(spec["作用层"]) or []) and u in (lay[spec["作用层"]])]
    for u in layer_units:
        dep = str(recs.get(str(u).strip(), {}).get("依据", ""))
        add_hit = []
        if ("M2-04" in dep or "腋" in dep):
            add_hit += ADD["条件_依据含_M2-04_或_腋"]
        if ("R2" in dep or "M2-05" in dep or "心脏条" in dep):
            add_hit += ADD["条件_依据含_R2_或_M2-05_或_心脏条"]
        t = sym_text(c)
        mo = [k for k in KW_OLD.get(u, []) if k in t]
        mn = [k for k in KW_NEW.get(u, []) if k in t]
        ma = [k for k in add_hit if k in t]
        out.append("  · %s" % u)
        out.append("      依据：%s" % dep[:200])
        out.append("      v15表命中：%s" % ("、".join(mo + ma) if (mo or ma) else "（无）"))
        out.append("      v16表命中：%s" % ("、".join(mn + ma) if (mn or ma) else "（无）"))
    out.append("")
    out.append("【gold】" + "、".join(GOLD[c]))
    out.append("【定义为删除的单元】" + "、".join(sorted(set(normalize_units([x for x in rec.get("主穴", [])])) & set()) or []))

io.open(os.path.join(HERE, "R1_dump.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")

# 原书 列缺/照海 主治行摘录
bk = os.path.join(ROOT, "教程_utf8.txt")
lines = []
if os.path.exists(bk):
    ls = io.open(bk, encoding="utf-8", errors="ignore").read().split("\n")
    for i, l in enumerate(ls):
        if ("列缺" in l or "照海" in l) and ("主" in l or "治" in l or "喉" in l or "任脉" in l or "阴跷" in l or "阴蹻" in l):
            lines.append("L%d: %s" % (i + 1, l[:300]))
io.open(os.path.join(HERE, "R1_book_lines.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines[:60]) + "\n")
print("wrote R1_dump.txt / R1_book_lines.txt ; cases=%d book_lines=%d" % (len(CASES), len(lines)))
