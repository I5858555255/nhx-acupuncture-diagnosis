# -*- coding: utf-8 -*-
"""M9-C2: 66折规则成立性矩阵聚合"""
import os, io, json, csv, pickle, sys, glob, re
ROOT=r"D:\projectAGI\nhx"; BLIND=os.path.join(ROOT,"盲法对照实验"); G=os.path.join(BLIND,"sf10_阶段M5","G_验收")
sys.path.insert(0,os.path.join(BLIND,"benchmark_v2"))
from normalize_acupoints import normalize_acupoints

rules_pool=json.load(io.open(os.path.join(G,"M9-规则池定义.json"),encoding="utf-8"))["rules"]
RULE_PTS={r["id"]:r["选穴组"] for r in rules_pool}
RULE_NAME={r["id"]:r["名称"] for r in rules_pool}

g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
GOLD={c:set(g["results"][c]["gold_members"]) for c in g["case_ids"]}

files=sorted(glob.glob(os.path.join(G,"M9-fold_*_rules.json")))
print("rules.json 数:",len(files))

agg={}  # rid -> {启用,收缩,关闭,held_tp,held_fp,held_cases}
for r in rules_pool:
    agg[r["id"]]={"启用":0,"收缩":0,"关闭":0,"held_tp":0,"held_fp":0,"held_启用折":0}

for fp in files:
    base=os.path.basename(fp).replace("M9-fold_","").replace("_rules.json","")
    data=json.load(io.open(fp,encoding="utf-8"))
    held_cases=data["留出案"]
    predp=os.path.join(G,f"M9-fold_{base}_pred.json")
    pred=json.load(io.open(predp,encoding="utf-8")) if os.path.exists(predp) else {}
    for r in data["规则"]:
        rid=r["id"]; v=r["判定"]
        if v.startswith("启用"): agg[rid]["启用"]+=1
        elif v.startswith("收缩"): agg[rid]["收缩"]+=1
        else: agg[rid]["关闭"]+=1
        # 留出链侧命中核验
        ptset=RULE_PTS.get(rid,[])
        if v.startswith("启用") and ptset:
            agg[rid]["held_启用折"]+=1
            for c in held_cases:
                if c in pred:
                    pnorm=set(normalize_acupoints(pred[c].get("主穴",[])))
                    h=GOLD.get(c,set())
                    hit=[p for p in ptset if p in pnorm and p in h]
                    miss=[p for p in ptset if p in pnorm and p not in h]
                    agg[rid]["held_tp"]+=len(hit); agg[rid]["held_fp"]+=len(miss)

# 输出矩阵 CSV
out=os.path.join(G,"M9-规则成立性矩阵.csv")
with io.open(out,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.writer(f); w.writerow(["规则ID","名称","启用折","收缩折","关闭折","启用占比%","留出TP","留出FP","净TP","误触发率%","成立性结论"])
    for rid,a in agg.items():
        tot=a["启用"]+a["收缩"]+a["关闭"]
        en=a["启用"]/tot*100 if tot else 0
        net=a["held_tp"]-a["held_fp"]
        fp_rate=a["held_fp"]/(a["held_tp"]+a["held_fp"])*100 if (a["held_tp"]+a["held_fp"]) else 0
        # 判定
        if a["启用"]>=tot*0.8 and net>=0 and fp_rate<50: concl="站得住"
        elif a["收缩"]>=tot*0.5 or (a["启用"]>=tot*0.5 and fp_rate>=50): concl="需收缩"
        elif a["启用"]<tot*0.3: concl="局部修补/无证据"
        else: concl="局部修补"
        w.writerow([rid,RULE_NAME[rid],a["启用"],a["收缩"],a["关闭"],round(en,1),a["held_tp"],a["held_fp"],net,round(fp_rate,1),concl])
        print(f"{rid:8} 启用{a['启用']:2} 收缩{a['收缩']:2} 关闭{a['关闭']:2} | 留出TP{a['held_tp']:2} FP{a['held_fp']:2} 净{net:3} -> {concl}")
print("已写",out)
