# -*- coding: utf-8 -*-
"""M9: 链分组表（锚案移动并入复诊链，对齐 M6-D）"""
import os, io, csv, pickle
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
rows=list(csv.DictReader(io.open(os.path.join(BLIND,"sf10_阶段D","组装清单.csv"),encoding="utf-8-sig")))
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=set(c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0)
ANCHOR={"followup_66":"66_01","followup_198":"198_01","followup_146":"146_01","followup_216":"216_01"}

bychain={}
for r in rows: bychain.setdefault(r["chain"],[]).append(r["case_id"])

final={}
used=set()
for ch in ["followup_66","followup_198","followup_146","followup_216"]:
    cids=set(bychain[ch]) | {ANCHOR[ch]}
    final[ch]=sorted(cids); used|=cids
# 其余 first_visit 单案链
for c in bychain.get("first_visit",[]):
    if c not in used: final["S_"+c]=[c]
# unscored 链
for c in bychain.get("unscored",[]):
    final["U_"+c]=[c]

out=os.path.join(G,"M9-链分组表.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["链ID","案号列表","案数","链类型","在86判分","unscored"])
    for ch,cids in sorted(final.items(),key=lambda x:(-len(x[1]),x[0])):
        scored=[c for c in cids if c in SC]; unsc=[c for c in cids if c not in SC]
        typ="复诊多案链" if len(cids)>1 else ("单案链" if c.startswith("S_") else "unscored单案")
        w.writerow([ch," ".join(cids),len(cids),typ,len(scored),"/".join(unsc)])
multi=[(ch,len(c)) for ch,c in final.items() if len(c)>1]
print("链总数:",len(final),"| 多案链:",multi,"| 总案:",sum(len(c) for c in final.values()))
print("86案判分集链数:",len([1 for c in final.values() if any(x in SC for x in c)]))
