# -*- coding: utf-8 -*-
"""M10-4: R7a 外踝胆经痛 86案扫描（排除足外侧冷档）"""
import os, io, csv, pickle, sys
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD={c:set(g["results"][c]["gold_members"]) for c in SC}
SYMP=os.path.join(BLIND,"盲法93","symptoms")
PTS=["丘墟","侠溪","足临泣"]
SIG=["外踝","踝扭傷","踝扭伤","踝腫","踝肿","踝緊","踝紧","足外側","足外侧"]
rows=[]
for c in SC:
    t=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
    hits=[w for w in SIG if w in t]
    lines=[l.strip() for l in t.split("\n") if any(w in l for w in SIG)]
    sig=" | ".join(lines)[:130]
    h=GOLD[c]
    cold = "足外側" in t and "冰" in t  # 足外侧冷档
    if hits:
        trig="排除(足外侧冷)" if cold else "触发"
        tp=sum(1 for p in PTS if p in h); fp=len(PTS)-tp
    else:
        trig="不触发"; sig=""; tp=0; fp=0
    rows.append({"案号":c,"信号原文":sig,"信号词":"/".join(hits),"判定":trig,
        "gold丘墟":"有" if "丘墟" in h else "无","gold侠溪":"有" if "侠溪" in h else "无",
        "gold足临泣":"有" if "足临泣" in h else "无","TP":tp,"FP":fp})
out=os.path.join(G,"86案R7a触发表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
trig=[r for r in rows if r["判定"]=="触发"]
excl=[r for r in rows if r["判定"].startswith("排除")]
print("触发案:",[r["案号"] for r in trig],"排除:",[r["案号"] for r in excl])
for r in trig+excl: print(r["案号"],r["判定"],"TP",r["TP"],"FP",r["FP"],"|",r["信号原文"][:70])
print("当前(含236) TP=",sum(r["TP"] for r in trig+excl),"FP=",sum(r["FP"] for r in trig+excl))
print("收紧后(仅触发) TP=",sum(r["TP"] for r in trig),"FP=",sum(r["FP"] for r in trig))
