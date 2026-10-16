# -*- coding: utf-8 -*-
"""M10-2: RC-2 多指麻 86案扫描"""
import os, io, csv, pickle, sys
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD={c:set(g["results"][c]["gold_members"]) for c in SC}
SYMP=os.path.join(BLIND,"盲法93","symptoms")
PTS=["太渊","合谷","曲池","大陵"]
SIG=["指麻","手指麻","指端麻","手麻","手指時麻","指尖","手指麻木","手指"]
rows=[]
for c in SC:
    t=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
    hits=[w for w in SIG if w in t]
    lines=[l.strip() for l in t.split("\n") if any(w in l for w in SIG)]
    sig=" | ".join(lines)[:130]
    h=GOLD[c]
    if hits:
        trig="触发"
        tp=sum(1 for p in PTS if p in h); fp=len(PTS)-tp
    else:
        trig="不触发"; sig=""; tp=0; fp=0
    rows.append({"案号":c,"信号原文":sig,"信号词":"/".join(hits),"判定":trig,
        "gold太渊":"有" if "太渊" in h else "无","gold合谷":"有" if "合谷" in h else "无",
        "gold曲池":"有" if "曲池" in h else "无","gold大陵":"有" if "大陵" in h else "无",
        "TP":tp,"FP":fp})
out=os.path.join(G,"86案RC2触发表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
trig=[r for r in rows if r["判定"]=="触发"]
print("触发案:",len(trig))
for r in trig: print(r["案号"],"| TP",r["TP"],"FP",r["FP"],"|",r["信号原文"][:90])
print("合计 TP=",sum(r["TP"] for r in trig),"FP=",sum(r["FP"] for r in trig))
