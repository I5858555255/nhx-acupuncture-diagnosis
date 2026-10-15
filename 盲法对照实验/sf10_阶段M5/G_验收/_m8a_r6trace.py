# -*- coding: utf-8 -*-
"""M8-A: R6 逐穴 TP/FP 追溯"""
import json, os, pickle, sys
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
sys.path.insert(0, os.path.join(ROOT, "benchmark_v2"))
from normalize_acupoints import normalize_acupoints
v12 = json.load(open(os.path.join(ROOT, "盲法93_v12", "_blind93v12_results.json"), encoding="utf-8"))
g = pickle.load(open(os.path.join(ROOT, "benchmark_v2", "_gold_results93v2.pkl"), "rb"))
NEW = g["results"]
R6_T = ['212_01','209_01','199_01','200_01','201_01','202_01','216_01']
ADD = {'后溪','申脉'}; DEL = {'外关','足临泣','临泣'}
def pts(rec): return normalize_acupoints(rec.get("主穴", []))
tp=fp=0
for c in R6_T:
    base = set(pts(v12[c])); gold = set(NEW[c]["gold_members"])
    line=[c]
    for p in sorted(ADD):
        already = p in base; hit = p in gold
        if not already:
            if hit: tp+=1; line.append(f"{p}=TP新增")
            else: fp+=1; line.append(f"{p}=FP新增")
    for p in sorted(DEL):
        if p in base and p not in gold:
            line.append(f"{p}=删(本就FP)")
    print(" | ".join(line))
print(f"\n新增TP={tp} 新增FP={fp} （对照报告 ΔTP+7 ΔFP+7）")
