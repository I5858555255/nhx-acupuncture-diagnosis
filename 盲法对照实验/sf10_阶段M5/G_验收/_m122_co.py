# -*- coding: utf-8 -*-
"""M12-2: M2-05 心脏三针 vs M2-06 利水 共触发"""
import os, io, csv, json, pickle, sys
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
GOLD={c:set(g["results"][c]["gold_members"]) for c in SC}
PRED=json.load(io.open(os.path.join(G,"盲法v14r2","_blind93v14r2_results.json"),encoding="utf-8"))
SYMP=os.path.join(BLIND,"盲法93","symptoms")
HEART=["心痛","心下","胸膈","氣堵","气堵","心痛徹背","胸痛徹背","不能側臥","胸脅","胸肋","積水","肺積水","胸水"]
WATER=["水腫","水肿","利水","腹水","小便不利","腳腫","脚肿","積水","肺積水","腫"]
rows=[]
for c in SC:
    t=io.open(os.path.join(SYMP,c+"_symptoms.txt"),encoding="utf-8").read()
    hh=[w for w in HEART if w in t]; wh=[w for w in WATER if w in t]
    if not hh or not wh: continue
    lines=[l.strip() for l in t.split("\n") if any(w in l for w in HEART+WATER)]
    pred=normalize_acupoints(PRED[c].get("主穴",[]))
    h=GOLD[c]
    hpts=[p for p in ["巨阙","天突","关元","公孙","内关"] if p in pred]
    wpts=[p for p in ["阴陵泉","三阴交","地机","复溜","水泉","照海","水道","中极","水分"] if p in pred]
    rows.append({"案号":c,"心信号":"/".join(hh[:4]),"水信号":"/".join(wh[:4]),
        "原文":" | ".join(lines)[:110],"pred心穴":"/".join(hpts),"pred水穴":"/".join(wpts),
        "pred穴数":len(pred),"gold心穴":"/".join(p for p in ["巨阙","天突","关元","公孙","内关"] if p in h),
        "gold水穴":"/".join(p for p in ["阴陵泉","三阴交","地机","复溜","水泉","照海"] if p in h)})
out=os.path.join(G,"86案共触发触发表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("共触发案:",len(rows))
for r in rows: print(r["案号"],"穴数",r["pred穴数"],"心:",r["pred心穴"],"水:",r["pred水穴"],"|",r["原文"][:70])
