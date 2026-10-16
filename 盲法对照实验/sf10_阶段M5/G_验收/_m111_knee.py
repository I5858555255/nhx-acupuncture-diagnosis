# -*- coding: utf-8 -*-
"""M11-1: 膝五针单点 86案扫描"""
import os, io, csv, pickle, sys
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD={c:set(g["results"][c]["gold_members"]) for c in SC}
SYMP=os.path.join(BLIND,"盲法93","symptoms")
PTS=["鹤顶","阳陵泉","阴陵泉"]  # 膝五针组成(膝眼/鹤顶常归一)
SIG=["膝痛","膝腫","膝肿","膝蓋","膝盖","膝無力","膝无力","雙膝","双膝","右膝","左膝","膝"]
rows=[]
for c in SC:
    t=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
    if "膝" not in t: continue
    lines=[l.strip() for l in t.split("\n") if "膝" in l]
    sig=" | ".join(lines)[:130]
    h=GOLD[c]
    tp=sum(1 for p in PTS if p in h); fp=len(PTS)-tp
    rows.append({"案号":c,"信号原文":sig,"gold阳陵泉":"有" if "阳陵泉" in h else "无",
        "gold阴陵泉":"有" if "阴陵泉" in h else "无","TP":tp,"FP":fp})
out=os.path.join(G,"86案膝五针触发表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("膝部症状案:",len(rows))
for r in rows: print(r["案号"],"TP",r["TP"],"FP",r["FP"],"|",r["信号原文"][:80])
print("合计 TP=",sum(r["TP"] for r in rows),"FP=",sum(r["FP"] for r in rows))
