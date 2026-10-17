#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""核查：留出案**自身症状文本**含多少 gold 主穴（字面出现）——判断 LLM 优势是否源于
"原文自带处方引文"（数据集文本自带答案）而非纯推理。

只读；输出 PN_selftext_check.txt
"""
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
BENCH = os.path.join(EXP, "benchmark_v2")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
CODES = {"三阴交": "三陰交", "阴陵泉": "陰陵泉", "中极": "中極", "关元": "關元", "地机": "地機",
         "公孙": "公孫", "内关": "內關", "复溜": "復溜", "阴谷": "陰谷", "列缺": "列缺",
         "照海": "照海", "外关": "外關", "足临泣": "足臨泣", "后溪": "後溪", "申脉": "申脈",
         "膈俞": "膈俞", "血海": "血海", "督俞": "督俞", "合谷": "合谷", "曲池": "曲池",
         "委中": "委中", "筑宾": "築賓", "肩井": "肩井", "足三里": "足三里", "大陵": "大陵"}

FOLDS = json.load(io.open(os.path.join(HERE, "PN_folds.json"), encoding="utf-8"))["folds"]
OUT = []
for fid in FOLDS:
    ids = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]
    tot = hit = 0
    det = []
    for c in ids:
        d = json.load(io.open(os.path.join(SD, "%s_symptoms_v2.json" % c), encoding="utf-8"))
        t = "".join((str(v["片段"]) if isinstance(v, dict) and "片段" in v else (v if isinstance(v, str) else "")) for v in d.values())
        g = normalize_units(NEW[c]["gold_members"])
        h = [u for u in g if (u in t or CODES.get(u, "@@") in t)]
        tot += len(g)
        hit += len(h)
        det.append("%s %d/%d" % (c, len(h), len(g)))
    OUT.append("%-14s 原文含 gold 穴位：%d/%d = %.0f%%   [%s]" % (fid, hit, tot, 100.0 * hit / max(tot, 1), "  ".join(det)))

io.open(os.path.join(HERE, "PN_selftext_check.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
print("\n".join(OUT))
