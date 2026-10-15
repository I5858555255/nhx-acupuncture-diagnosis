# -*- coding: utf-8 -*-
"""fold_ruleselect.py — 按链留出的规则选择脚本
用法: python fold_ruleselect.py --heldout followup_198
只读其余链 symptoms+gold；绝不可读留出链 gold（内部断言）。
"""
import os, io, csv, json, pickle, argparse, sys
ROOT = r"D:\projectAGI\nhx"
BLIND = os.path.join(ROOT, "盲法对照实验")
G = os.path.join(BLIND, "sf10_阶段M5", "G_验收")
SYMP = os.path.join(BLIND, "盲法93", "symptoms")
sys.path.insert(0, os.path.join(BLIND, "benchmark_v2"))
from normalize_acupoints import normalize_acupoints

ap = argparse.ArgumentParser(); ap.add_argument("--heldout", required=True)
a = ap.parse_args()

rules = json.load(io.open(os.path.join(G,"M9-规则池定义.json"),encoding="utf-8"))["rules"]
chain_rows = list(csv.DictReader(io.open(os.path.join(G,"M9-链分组表.csv"),encoding="utf-8-sig")))
# 链ID -> 案号列表
chain_map = {r["链ID"]: r["案号列表"].split() for r in chain_rows}
if a.heldout not in chain_map:
    print("未知链:",a.heldout,"可选:",list(chain_map)); sys.exit(1)
held_cases = set(chain_map[a.heldout])

g = pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC = [c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD = {c: set(g["results"][c]["gold_members"]) for c in SC}

# 其余链 = 全部SC案 - 留出案
train_cases = [c for c in SC if c not in held_cases]

# 断言: 不触碰留出链 gold（这里 train_cases 不含 held_cases，gold 查询也只对 train_cases）
results=[]
for r in rules:
    T=[]
    for c in train_cases:
        text=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
        if any(w in text for w in r["信号词族"]):
            T.append(c)
    tp=fp=0; detail=[]
    for c in T:
        # gold 仅对 train_cases 查询
        h=GOLD[c]
        hit=[p for p in r["选穴组"] if p in h]
        miss=[p for p in r["选穴组"] if p not in h and r["选穴组"]]
        tp+=len(hit); fp+=len(miss)
        detail.append(f"{c}:TP{hit} FP{miss}")
    net = tp-fp
    has_book = r["原书出处"] not in ["-",""]
    if not T: verdict="关闭(无触发)"
    elif not has_book: verdict="关闭(无原书依据)"
    elif net>=0: verdict=f"启用(净{net})"
    else: verdict=f"收缩(净{net},误触发{[d.split(':')[0] for d in detail]})"
    results.append({"id":r["id"],"名称":r["名称"],"触发案数":len(T),"TP":tp,"FP":fp,"净":net,"判定":verdict,"明细":detail})

out=os.path.join(G,f"M9-fold_{a.heldout}_rules.json")
json.dump({"heldout":a.heldout,"留出案":sorted(held_cases),"训练案数":len(train_cases),"规则":results},
          io.open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"heldout={a.heldout} 训练案={len(train_cases)} 留出案={sorted(held_cases)}")
for x in results: print(f"  {x['id']:8} 触发{x['触发案数']:2} TP{x['TP']} FP{x['FP']} 净{x['净']:3} -> {x['判定']}")
print("已写",out)
