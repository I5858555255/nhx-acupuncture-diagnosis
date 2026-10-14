# -*- coding: utf-8 -*-
"""F1 步骤7 独立复算：v9 vs v10 symptom-only 主穴集合一致案数（整体单元，不展开透刺/X+Y）"""
import json, pickle, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = r"D:\projectAGI\nhx\盲法对照实验"
BENCH = os.path.join(ROOT, "benchmark_v2")
v9 = json.load(open(os.path.join(ROOT, "盲法93_v9", "_blind93v9_results.json"), encoding="utf-8"))
v10 = json.load(open(os.path.join(ROOT, "盲法93_v10", "_blind93v10_results.json"), encoding="utf-8"))
with open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb") as f:
    g = pickle.load(f)
CASE_IDS = g["case_ids"]

same = 0; diff = []; du = 0
for c in CASE_IDS:
    a = set(v9.get(c, {}).get('主穴', []))
    b = set(v10.get(c, {}).get('主穴', []))
    if a == b:
        same += 1
    else:
        diff.append(c)
        du += len(a ^ b)

print("CASE_IDS 总数:", len(CASE_IDS))
print("一致案:", same)
print("差异案:", len(diff))
print("差异单元总数:", du)
print("差异案清单:", diff)

# 与 v10 汇总记录对照
S = json.load(open(os.path.join(ROOT, "盲法93_v10", "判分汇总v10.json"), encoding="utf-8"))
rec = S["执行方差_v10_vs_v9"]
print("\n--- 与 判分汇总v10.json 记录对照 ---")
print("记录 一致案:", rec["一致案"], " 复算:", same, " match=", rec["一致案"] == same)
print("记录 差异案:", rec["差异案"], " 复算:", len(diff), " match=", rec["差异案"] == len(diff))
print("记录 差异单元总数:", rec["差异单元总数"], " 复算:", du, " match=", rec["差异单元总数"] == du)
print("\n结论: 复算一致案 = %d/93 ; 报告(v10评分报告.md)声称 53/93 ; 匹配 = %s" % (same, same == 53))
