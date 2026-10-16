# -*- coding: utf-8 -*-
"""M12-1: M2-03 手麻 vs R1 足跟痛 分流边界"""
import os, io, csv, json, pickle, sys
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD={c:set(g["results"][c]["gold_members"]) for c in SC}
PRED=json.load(io.open(os.path.join(G,"盲法v14r2","_blind93v14r2_results.json"),encoding="utf-8"))
SYMP=os.path.join(BLIND,"盲法93","symptoms")
HAND=["手麻","指麻","指端麻","手指麻","指尖麻","手指"]
HEEL=["足跟","腳跟","脚跟","腳跟"]
rows=[]
for c in SC:
    t=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
    hh=[w for w in HAND if w in t]; eh=[w for w in HEEL if w in t]
    if not hh and not eh: continue
    lines=[l.strip() for l in t.split("\n") if any(w in l for w in HAND+HEEL)]
    pred=normalize_acupoints(PRED[c].get("主穴",[]))
    h=GOLD[c]
    rows.append({"案号":c,"手麻信号":"/".join(hh),"足跟信号":"/".join(eh),
        "原文":" | ".join(lines)[:120],
        "pred大陵":"有" if "大陵" in pred else "无","pred水泉":"有" if "水泉" in pred else "无",
        "gold大陵":"有" if "大陵" in h else "无","gold水泉":"有" if "水泉" in h else "无"})
out=os.path.join(G,"86案分流触发表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("手麻或足跟案:",len(rows))
overlap=[r for r in rows if r["手麻信号"] and r["足跟信号"]]
print("重叠案(手麻+足跟):",[r["案号"] for r in overlap])
for r in rows: print(r["案号"],"手",r["手麻信号"],"跟",r["足跟信号"],"pred陵/泉",r["pred大陵"],r["pred水泉"],"gold陵/泉",r["gold大陵"],r["gold水泉"],"|",r["原文"][:60])
