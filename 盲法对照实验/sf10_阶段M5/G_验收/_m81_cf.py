# -*- coding: utf-8 -*-
"""M8.1-A: R6 动作级反事实（基于 v14 预测，非 v12）"""
import os, io, json, csv, pickle, sys, hashlib, shutil
ROOT = r"D:\projectAGI\nhx"
BLIND = os.path.join(ROOT, "盲法对照实验")
V14PRED = os.path.join(BLIND, "sf10_阶段M5", "G_验收", "盲法v14r7", "_blind93v14r7_results.json")
sys.path.insert(0, os.path.join(BLIND, "benchmark_v2"))
from normalize_acupoints import normalize_acupoints

g = pickle.load(open(os.path.join(BLIND, "benchmark_v2", "_gold_results93v2.pkl"), "rb"))
NEW = g["results"]; SC = [c for c in g["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}
v14 = json.load(open(V14PRED, encoding="utf-8"))

TRIG = ["199_01","200_01","225_01","323_01","345_01","346_01"]
LEAK = ["201_01","202_01","209_01","212_01"]

def norm(pts): return set(normalize_acupoints(pts))
def score(Pset):
    tp=fp=fn=0
    for c in SC:
        P=Pset[c]; G=GOLD[c]
        tp+=len(P&G); fp+=len(P-G); fn+=len(G-P)
    return tp,fp,fn

base = {c: norm(v14[c].get("主穴",[])) for c in SC}
bTP,bFP,bFN = score(base)
print(f"v14 base: TP={bTP} FP={bFP} FN={bFN}")

# 反事实A: 6触发案追加 后溪/申脉
cfA = {c: set(base[c]) for c in SC}
actions=[]
for c in TRIG:
    before=set(base[c])
    added=[]
    for p in ["后溪","申脉"]:
        if p not in before:
            cfA[c].add(p); added.append(p)
    if added:
        actions.append((c,"追加","+".join(added),"v14预测无后溪申脉"))
aTP,aFP,aFN=score(cfA)
print(f"cfA(追加后溪申脉): TP={aTP} FP={aFP} FN={aFN}  ΔTP={aTP-bTP} ΔFP={aFP-bFP} ΔFN={aFN-bFN}")

# 反事实B: 追加 + 替换(移除外关/足临泣/临泣)
cfB = {c: set(base[c]) for c in SC}
for c in TRIG:
    removed=[]
    for p in ["后溪","申脉"]:
        if p not in cfB[c]: cfB[c].add(p)
    for p in ["外关","足临泣","临泣"]:
        if p in cfB[c]:
            cfB[c].discard(p); removed.append(p)
    if removed:
        actions.append((c,"替换(删)","-".join(removed),"R6分流:项强档外关临泣让位"))
bBTP,bBFP,bBFN=score(cfB)
print(f"cfB(追加+替换): TP={bBTP} FP={bBFP} FN={bBFN}  ΔTP={bBTP-bTP} ΔFP={bBFP-bFP} ΔFN={bBFN-bFN}")

# 泄漏断言: 4案预测逐穴不变
for c in LEAK:
    assert cfA[c]==base[c], f"泄漏: {c} 在 cfA 被改"
    assert cfB[c]==base[c], f"泄漏: {c} 在 cfB 被改"
print("泄漏断言通过: 201/202/209/212 在 cfA/cfB 均逐穴不变")

# 保存 cfA 新预测 JSON
out_json=os.path.join(BLIND,"sf10_阶段M5","G_验收","_r6cfA_results.json")
json.dump({c:sorted(v) for c,v in cfA.items()}, open(out_json,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("已写", out_json)

# 修改动作表
out_csv=os.path.join(BLIND,"sf10_阶段M5","G_验收","M8.1-反事实修改动作表.csv")
with io.open(out_csv,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["案号","动作","穴","原由"])
    for a in actions: w.writerow(a)
print("已写", out_csv)
print("动作明细:", actions)
