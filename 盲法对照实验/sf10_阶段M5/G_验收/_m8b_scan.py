# -*- coding: utf-8 -*-
"""M8-B 终版: 86案 R6 项强信号全量扫描（含后项/项痛细档）"""
import os, io, csv, pickle
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
SYMP = os.path.join(ROOT, "盲法93", "symptoms")
OUT = os.path.join(ROOT, "sf10_阶段M5", "G_验收", "86案R6触发表.csv")
g = pickle.load(open(os.path.join(ROOT, "benchmark_v2", "_gold_results93v2.pkl"), "rb"))
SC = [c for c in g["case_ids"] if len(g["results"][c]["gold_members"]) > 0]
GOLD = {c: set(g["results"][c]["gold_members"]) for c in SC}

# 就诊类型
visits = {}
with io.open(os.path.join(ROOT, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        visits[r.get("盲法案号","")] = r.get("就诊类型","")[:10]

# 严格项强触发词族（排除 颈部关节痛=寒痹档、颈部淋巴结、肩后少阳头痛）
TRIG = ["项强","項強","脖子僵硬","脖子鬆","脖子松","後枕","后枕","後腦","后脑",
        "後項","后项","頸項痛","颈项痛","後頭痛","后头痛","後項會很緊","后项紧","項痛","项痛"]
EXCLUDE_CONTEXT = ["頸部及手足關節痛","颈部及手足关节痛","頸部淋巴結","颈部淋巴结"]

rows=[]
for cid in SC:
    text = io.open(os.path.join(SYMP, cid+"_symptoms.txt"), encoding="utf-8").read()
    hits=[w for w in TRIG if w in text]
    excl=[w for w in EXCLUDE_CONTEXT if w in text]
    lines=[l.strip() for l in text.split("\n") if any(w in l for w in TRIG)]
    sig=" | ".join(lines)[:120]
    hx="后溪" in GOLD[cid]; sm="申脉" in GOLD[cid]
    if hits and not excl:
        trig="触发(项强)"; dtp=(1 if hx else 0)+(1 if sm else 0); dfp=(0 if hx else 1)+(0 if sm else 1)
        cls="命中(gold有)" if (hx or sm) else "误触发(gold无)"
    else:
        trig="不触发"; sig=sig if excl else ""; dtp=0; dfp=0
        cls="寒痹/淋巴结排除档" if excl else "无项强信号"
    rows.append({"案号":cid,"就诊类型":visits.get(cid,""),"项强信号原文":sig,
        "信号词":"/".join(hits),"触发判定":trig,"预计穴":"后溪+申脉" if hits and not excl else "",
        "触发分类":cls,"gold含后溪":"有" if hx else "无","gold含申脉":"有" if sm else "无",
        "ΔTP":dtp,"ΔFP":dfp})

with io.open(OUT,"w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

trig=[r for r in rows if r["触发判定"]=="触发(项强)"]
print("总案",len(rows),"| 严格项强触发",len(trig))
for r in trig: print(r["案号"],r["信号词"],"| gold后溪",r["gold含后溪"],"申脉",r["gold含申脉"],"| ΔTP",r["ΔTP"],"ΔFP",r["ΔFP"])
tp=sum(r["ΔTP"] for r in trig); fp=sum(r["ΔFP"] for r in trig)
print(f"\n盲法预期合计: ΔTP={tp} ΔFP={fp}")
