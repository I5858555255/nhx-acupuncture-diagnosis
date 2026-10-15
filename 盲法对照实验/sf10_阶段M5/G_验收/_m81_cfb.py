# -*- coding: utf-8 -*-
"""M8.1 补充: 落盘 _r6cfB_results.json + 被删穴核算 + 泄漏断言"""
import os, io, json, csv, pickle, sys
ROOT = r"D:\projectAGI\nhx"
BLIND = os.path.join(ROOT, "盲法对照实验")
G = os.path.join(BLIND, "sf10_阶段M5", "G_验收")
sys.path.insert(0, os.path.join(BLIND, "benchmark_v2"))
from normalize_acupoints import normalize_acupoints

g = pickle.load(open(os.path.join(BLIND, "benchmark_v2", "_gold_results93v2.pkl"), "rb"))
NEW = g["results"]; SC = [c for c in g["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}
v14 = json.load(open(os.path.join(G, "盲法v14r7", "_blind93v14r7_results.json"), encoding="utf-8"))

def norm(pts): return set(normalize_acupoints(pts))
base = {c: norm(v14[c].get("主穴", [])) for c in SC}
TRIG = ["199_01","200_01","225_01","323_01","345_01","346_01"]
LEAK = ["201_01","202_01","209_01","212_01"]

cfB = {c: set(base[c]) for c in SC}
for c in TRIG:
    for p in ["后溪","申脉"]:
        if p not in cfB[c]: cfB[c].add(p)
    for p in ["外关","足临泣","临泣"]:
        cfB[c].discard(p)

# 落盘 cfB JSON（与 cfA 同格式 sorted list）
out = os.path.join(G, "_r6cfB_results.json")
json.dump({c: sorted(v) for c, v in cfB.items()}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写", out)

# 被删穴核算
print("\n=== 被删穴核算（199/200 移除外关/足临泣/临泣）===")
rows=[]
for c in ["199_01","200_01"]:
    for p in ["外关","足临泣","临泣"]:
        in_pred = p in base[c]; in_gold = p in GOLD[c]
        if in_pred:
            effect = "FP减少(-1)" if not in_gold else "TP损失(-1)"
        else:
            effect = "该穴不在v14预测,无操作"
        rows.append((c,p,"在v14" if in_pred else "不在v14","gold有" if in_gold else "gold无",effect))
        print(c,p,"|","v14有" if in_pred else "v14无","|","gold有" if in_gold else "gold无","->",effect)

# 追加穴核算（cfA 新增加的后溪申脉）
print("\n=== 追加穴核算（cfA/cfB 新增后溪申脉）===")
for c in TRIG:
    for p in ["后溪","申脉"]:
        if p not in base[c]:
            in_gold = p in GOLD[c]
            print(c,p,"新增 |","gold有=TP" if in_gold else "gold无=FP")

# 泄漏断言 cfB
for c in LEAK:
    assert cfB[c]==base[c], f"泄漏 {c}"
print("\n泄漏断言通过: cfB 下 201/202/209/212 逐穴不变")

# 写被删穴核算 CSV
with io.open(os.path.join(G,"M8.1-被删穴核算.csv"),"w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["案号","被删穴","v14是否含","gold是否含","影响"])
    for r in rows: w.writerow(r)
print("已写 M8.1-被删穴核算.csv")
