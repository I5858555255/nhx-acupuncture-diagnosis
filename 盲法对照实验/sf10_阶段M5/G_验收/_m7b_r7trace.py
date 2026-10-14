# -*- coding: utf-8 -*-
"""M7-B: R7 逐穴 TP/FP 追溯 + 86案症状信号扫描"""
import json, os, csv, pickle, io, re, sys
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
BENCH = os.path.join(ROOT, "benchmark_v2")
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints

v12 = json.load(open(os.path.join(ROOT, "盲法93_v12", "_blind93v12_results.json"), encoding="utf-8"))
g = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW, CASE_IDS = g["results"], g["case_ids"]
SC = [c for c in CASE_IDS if len(NEW[c]["gold_members"]) > 0]
print("有gold案数(SC):", len(SC))
print("无gold案:", [c for c in CASE_IDS if c not in SC])

def pts(rec): return normalize_acupoints(rec.get("主穴", []))
R7_T = ["207_01", "236_01", "118_01", "194_01"]
ADD = {"丘墟", "侠溪", "商丘", "解溪"}
print("\n=== R7 逐穴追溯（v12 预测 + 4穴 → 对 gold）===")
trace = []
for c in R7_T:
    base = pts(v12[c]); gold = set(NEW[c]["gold_members"])
    for p in sorted(ADD):
        already = p in base
        hit = p in gold
        if already:
            tag = "已在v12预测(不计加穴)"
        elif hit:
            tag = "TP(新增命中gold)"
        else:
            tag = "FP(新增未中gold)"
        trace.append((c, p, "已在v12" if already else "新增", "gold有" if hit else "gold无", tag))
        print(f"{c} {p}: {tag}")
tp = sum(1 for t in trace if "TP" in t[4]); fp = sum(1 for t in trace if "FP" in t[4])
print(f"\n新增TP={tp} 新增FP={fp} （对照报告 ΔTP+9 ΔFP+7）")
