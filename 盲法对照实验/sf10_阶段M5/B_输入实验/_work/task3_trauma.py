# -*- coding: utf-8 -*-
"""任务3：全93案外伤信号扫描（full原案 + symptoms_v2盲法输入）。"""
import os, re, json, io, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _commons import SYM_V2_DIR, FULL_DIR, OUT_DIR

TRAWORDS = ["跌打","外傷","外伤","瘀血","瘀血","車禍","车祸","撞傷","撞伤","摔伤","摔傷",
            "受傷","受伤","創傷","创伤","跌傷","跌伤","骨折","扭傷","扭伤","碰傷","碰伤",
            "跌","瘀血","瘀青","瘀青","車禍","手術","刀傷","刀伤","燒燙","燙傷","燒傷"]
# 只保留明确外伤/跌打/瘀血信号
STRONG_TRAUMA = ["跌打","外傷","外伤","瘀血","車禍","车祸","撞傷","撞伤","摔伤","摔傷",
                 "創傷","创伤","跌傷","跌伤","骨折","扭傷","扭伤","碰傷","碰伤","刀傷","刀伤",
                 "燙傷","燒傷","摔倒","跌倒","粉碎","摔傷","受傷","受伤"]

def cid_list():
    return sorted(f.replace("_symptoms_v2.json","") for f in os.listdir(SYM_V2_DIR) if f.endswith(".json"))

rows=[]
for cid in cid_list():
    fullp=os.path.join(FULL_DIR, cid+"_full.txt")
    full_txt=io.open(fullp,encoding="utf-8").read() if os.path.exists(fullp) else ""
    d=json.load(io.open(os.path.join(SYM_V2_DIR,cid+"_symptoms_v2.json"),encoding="utf-8"))
    sym_txt=""
    for k,v in d.items():
        if isinstance(v,dict): sym_txt+=(v.get("片段","") or "")+" "
        elif isinstance(v,list):
            for it in v: sym_txt+=(it.get("片段","") if isinstance(it,dict) else str(it))+" "
        elif isinstance(v,str): sym_txt+=v+" "
    full_hits=sorted(set(w for w in STRONG_TRAUMA if w in full_txt))
    sym_hits=sorted(set(w for w in STRONG_TRAUMA if w in sym_txt))
    if full_hits or sym_hits:
        rows.append({"案号":cid,"原案full外伤词":"/".join(full_hits),"盲法输入外伤词":"/".join(sym_hits)})

# 写CSV
with io.open(os.path.join(OUT_DIR,"全库外伤信号扫描.csv"),"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["案号","原案full外伤词","盲法输入外伤词"]); w.writeheader()
    for r in rows: w.writerow(r)

print("有外伤信号的案数:",len(rows))
for r in rows:
    print(r["案号"],"| full:",r["原案full外伤词"],"| 盲法:",r["盲法输入外伤词"] or "(无)")
