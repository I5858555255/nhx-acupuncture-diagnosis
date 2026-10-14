# -*- coding: utf-8 -*-
"""score_sf10_v10_hist.py — v10 history-aware 评分（benchmark_v2 口径）。
hist 合并文件 _results.json 截断（仅21案），从 part1..part5（JSON数组，合计93案）合并。
与 v10 symptom-only 分层对比；两模式分数不合并。"""
import json, os, sys, csv, statistics, pickle

HERE = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段D"
BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints

# ---- 读 hist 分片合并 ----
HDIR = os.path.join(ROOT, "盲法93_v10_hist")
HIST = {}
for i in range(1, 6):
    arr = json.load(open(os.path.join(HDIR, f"_blind93v10_hist_part{i}.json"), encoding="utf-8"))
    for e in arr:
        HIST[e["case_id"]] = e
# ---- 读 symptom-only ----
SYM = json.load(open(os.path.join(ROOT, "盲法93_v10", "_blind93v10_results.json"), encoding="utf-8"))

with open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb") as f:
    g = pickle.load(f)
NEW=g["results"]; CASE_IDS=g["case_ids"]; SUMMARY=g["summary"]

# ---- visit_type ----
VT={}
for row in csv.DictReader(open(os.path.join(HERE,"组装清单.csv"),encoding="utf-8-sig")):
    VT[row["case_id"]]=row.get("visit_type","")

def pm(G,P):
    tp=len(P&G);fp=len(P-G);fn=len(G-P)
    recall=tp/len(G) if G else None
    prec=tp/len(P) if P else None
    f1=(2*prec*recall/(prec+recall)) if (prec and recall and (prec+recall)>0) else (0.0 if tp==0 else None)
    jac=tp/(tp+fp+fn) if (tp+fp+fn)>0 else 0.0
    return dict(tp=tp,fp=fp,fn=fn,recall=recall,prec=prec,f1=f1,jac=jac)

def score_rec(rec):
    Pm=normalize_acupoints(rec.get("主穴",[])); Pa=normalize_acupoints(rec.get("主穴",[])+rec.get("佐穴",[]))
    return dict(Pm=Pm,Pa=Pa,units_main=len(rec.get("主穴",[])),points_main=len(Pm),points_all=len(Pa),
                main=None,all=None,layers=rec.get("主穴分层",{}))

PER={}
for cid in CASE_IDS:
    G=set(NEW[cid]["gold_members"])
    s=score_rec(SYM[cid]); h=score_rec(HIST[cid])
    s["main"]=pm(G,s["Pm"]); s["all"]=pm(G,s["Pa"])
    h["main"]=pm(G,h["Pm"]); h["all"]=pm(G,h["Pa"])
    PER[cid]=dict(G=sorted(G),gc=len(G),sym=s,hist=h,chain=SUMMARY["chain_map"].get(cid,"first_visit"),
                  vt=VT.get(cid,""),note=NEW[cid]["note"])

SCORED=[c for c in CASE_IDS if PER[c]["gc"]>0]
UNSCORED=[c for c in CASE_IDS if PER[c]["gc"]==0]

def macro(mode,subset,metric,cids=None):
    cids=cids or SCORED;v=[]
    for c in cids:
        x=PER[c][mode][subset][metric]
        if x is not None:v.append(x)
    return statistics.mean(v) if v else None
def micro(mode,subset,metric,cids=None):
    cids=cids or SCORED;tp=fp=fn=0
    for c in cids:
        m=PER[c][mode][subset];tp+=m["tp"];fp+=m["fp"];fn+=m["fn"]
    if metric=="recall":return tp/(tp+fn) if (tp+fn) else None
    if metric=="prec":return tp/(tp+fp) if (tp+fp) else None
    if metric=="f1":
        r=tp/(tp+fn) if (tp+fn) else 0;p=tp/(tp+fp) if (tp+fp) else 0
        return 2*p*r/(p+r) if (p+r) else 0.0
    if metric=="jac":return tp/(tp+fp+fn) if (tp+fp+fn) else 0.0
def dist(vals):
    b={"100%":0,"80-99%":0,"60-79%":0,"40-59%":0,"<40%":0}
    for x in vals:
        if x is None:continue
        if x>=0.999:b["100%"]+=1
        elif x>=0.8:b["80-99%"]+=1
        elif x>=0.6:b["60-79%"]+=1
        elif x>=0.4:b["40-59%"]+=1
        else:b["<40%"]+=1
    return b
ro=lambda x:None if x is None else round(x,4)

S=dict(n_cases=len(CASE_IDS),n_scorable=len(SCORED),n_unscored=len(UNSCORED),unscored={c:PER[c]["note"] for c in UNSCORED})
for mode in ("sym","hist"):
    ms={}
    for subset in ("main","all"):
        ms[subset]=dict(
            macro=dict(recall=ro(macro(mode,subset,"recall")),prec=ro(macro(mode,subset,"prec")),f1=ro(macro(mode,subset,"f1")),jac=ro(macro(mode,subset,"jac"))),
            micro=dict(recall=ro(micro(mode,subset,"recall")),prec=ro(micro(mode,subset,"prec")),f1=ro(micro(mode,subset,"f1")),jac=ro(micro(mode,subset,"jac"))))
    units=[PER[c][mode]["units_main"] for c in SCORED]
    points=[PER[c][mode]["points_main"] for c in SCORED]
    S[mode]=dict(metrics=ms,mean_units_main=round(statistics.mean(units),3),mean_points_main=round(statistics.mean(points),3),
                 sum_tp_main=sum(PER[c][mode]["main"]["tp"] for c in SCORED))
    S[f"dist_{mode}_recall"]=dist([PER[c][mode]["main"]["recall"] for c in SCORED])
    S[f"{mode}零命中"]=[c for c in SCORED if PER[c][mode]["main"]["tp"]==0]
    S[f"{mode}满分"]=[c for c in SCORED if PER[c][mode]["main"]["recall"] and PER[c][mode]["main"]["recall"]>=0.999]

# ---- 链分层 ----
follow=[c for c in SCORED if PER[c]["chain"].startswith("followup")]
anchor=[c for c in SCORED if PER[c]["chain"] in ("first_visit",) or PER[c]["chain"].startswith("anchor")]
S["链分层_chainmap"]={}
for cset,nm in [(follow,"followup"),(anchor,"anchor_first")]:
    S["链分层_chainmap"][nm]={}
    for mode in ("sym","hist"):
        S["链分层_chainmap"][nm][mode]=dict(n=len(cset),recall=ro(macro(mode,"main","recall",cset)),prec=ro(macro(mode,"main","prec",cset)),f1=ro(macro(mode,"main","f1",cset)),jac=ro(macro(mode,"main","jac",cset)))
# visit_type 分层
visits=[c for c in SCORED if PER[c]["vt"]=="复诊"]
firsts=[c for c in SCORED if PER[c]["vt"]=="首诊"]
S["链分层_visittype"]={}
for cset,nm in [(visits,"复诊"),(firsts,"首诊")]:
    S["链分层_visittype"][nm]={}
    for mode in ("sym","hist"):
        S["链分层_visittype"][nm][mode]=dict(n=len(cset),recall=ro(macro(mode,"main","recall",cset)),prec=ro(macro(mode,"main","prec",cset)),f1=ro(macro(mode,"main","f1",cset)),jac=ro(macro(mode,"main","jac",cset)))

# ---- 逐案集合差异 ----
diffs=[]
for c in SCORED:
    su=set(SYM[c].get("主穴",[]));hu=set(HIST[c].get("主穴",[]))
    if su==hu:cat="无变化"
    else:cat="历史延续/症状字段改变"
    diffs.append(dict(case_id=c,vt=PER[c]["vt"],chain=PER[c]["chain"],cat=cat,
        sym_units=sorted(su),hist_units=sorted(hu),removed=sorted(su-hu),added=sorted(hu-su),
        sym_recall=ro(PER[c]["sym"]["main"]["recall"]),hist_recall=ro(PER[c]["hist"]["main"]["recall"]),
        sym_f1=ro(PER[c]["sym"]["main"]["f1"]),hist_f1=ro(PER[c]["hist"]["main"]["f1"]),
        sym_tp=PER[c]["sym"]["main"]["tp"],hist_tp=PER[c]["hist"]["main"]["tp"],
        sym_jac=ro(PER[c]["sym"]["main"]["jac"]),hist_jac=ro(PER[c]["hist"]["main"]["jac"])))
S["逐案"]=diffs
S["变化案数"]=sum(1 for d in diffs if d["cat"]!="无变化")
S["无变化案数"]=sum(1 for d in diffs if d["cat"]=="无变化")

# 8 延续案
CONT=["156_06","199_01","200_01","201_01","202_01","213_01","216_01","216_02"]
S["延续8案"]={}
for c in CONT:
    if c in PER:
        S["延续8案"][c]=dict(gold=PER[c]["G"],sym_tp=PER[c]["sym"]["main"]["tp"],hist_tp=PER[c]["hist"]["main"]["tp"],
            sym_recall=ro(PER[c]["sym"]["main"]["recall"]),hist_recall=ro(PER[c]["hist"]["main"]["recall"]),
            sym命中=PER[c]["sym"]["Pm"] and sorted(PER[c]["sym"]["Pm"]),
            hist命中=PER[c]["hist"]["Pm"] and sorted(PER[c]["hist"]["Pm"]),
            hist_units=HIST[c].get("主穴",[]))

# ---- 明细 CSV ----
header=["case_id","chain","visit_type","gold穴数","单元数","点数","TP","recall_main","prec_main","f1_main","jac_main","命中清单","漏穴清单","未命中清单","备注"]
rows=[]
for c in SCORED:
    n=PER[c]["hist"];G=set(PER[c]["G"]);P=n["Pm"]
    rows.append([c,PER[c]["chain"],PER[c]["vt"],PER[c]["gc"],n["units_main"],n["points_main"],n["main"]["tp"],
        ro(n["main"]["recall"]),ro(n["main"]["prec"]),ro(n["main"]["f1"]),ro(n["main"]["jac"]),
        ";".join(sorted(P&G)),";".join(sorted(G-P)),";".join(sorted(P-G)),PER[c]["note"]])
for c in UNSCORED:
    rows.append([c,PER[c]["chain"],PER[c]["vt"],0,"","","","","","","","","","",PER[c]["note"]])
csv.writer(open(os.path.join(HERE,"判分明细v10_hist.csv"),"w",newline="",encoding="utf-8-sig")).writerows([header]+rows)
json.dump(S,open(os.path.join(HERE,"判分汇总v10_hist.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# 审计
audit={}
for c in SCORED:
    rec=HIST[c]
    audit[c]=dict(gold=PER[c]["G"],gold_count=PER[c]["gc"],chain=PER[c]["chain"],vt=PER[c]["vt"],
                   main_units=rec.get("主穴",[]),main_points=sorted(PER[c]["hist"]["Pm"]),主穴记录=rec.get("主穴记录",[]))
json.dump(audit,open(os.path.join(HERE,"审计日志v10_hist.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)

print("=== symptom-only ===")
print("main macro:",S["sym"]["metrics"]["main"]["macro"],"units均",S["sym"]["mean_units_main"])
print("all macro:",S["sym"]["metrics"]["all"]["macro"])
print("=== hist ===")
print("main macro:",S["hist"]["metrics"]["main"]["macro"],"units均",S["hist"]["mean_units_main"])
print("all macro:",S["hist"]["metrics"]["all"]["macro"])
print("链chainmap:",json.dumps(S["链分层_chainmap"],ensure_ascii=False))
print("visittype:",json.dumps(S["链分层_visittype"],ensure_ascii=False))
print("零命中 sym",S["sym零命中"],"hist",S["hist零命中"])
print("变化案数",S["变化案数"],"无变化",S["无变化案数"])
print("延续8案:",json.dumps(S["延续8案"],ensure_ascii=False))
