# -*- coding: utf-8 -*-
"""_score_core.py — SF10 核心集评测：排除"天然不可开"案后在 v5/v6/v9/v10 上重算。
口径与 score_benchmark_v2 / score_sf10_v10.py 完全一致（normalize_acupoints + _gold_results93v2.pkl 点级宏/微）。
唯一差异：SCORED 子集过滤（读排除清单.csv）与输出目录。
- 86 全量（不排除）作控制组，必须与既有数字一致（脚本自证口径未变）。
- 排除清单.csv 由核心集审计产出：列 case_id（必需）+ 主类别/证据列（本脚本只取 case_id 与主类别）。
运行：python _score_core.py  （输出判分明细_核心集.csv / 判分汇总_核心集.json / 控制台）
"""
import json, os, sys, csv, statistics, pickle

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints

ROOT = r"D:\projectAGI\nhx\盲法对照实验"
FILES = {
    "v5":  os.path.join(ROOT, "盲法93_v5", "_blind93v5_results.json"),
    "v6":  os.path.join(ROOT, "盲法93_v6", "_blind93v6_results.json"),
    "v9":  os.path.join(ROOT, "盲法93_v9", "_blind93v9_results.json"),
    "v10": os.path.join(ROOT, "盲法93_v10", "_blind93v10_results.json"),
}
CMP = ["v5", "v6", "v9", "v10"]

with open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb") as f:
    g = pickle.load(f)
NEW_RESULTS = g["results"]; CASE_IDS = g["case_ids"]; SUMMARY = g["summary"]

BLIND = {lab: json.load(open(FILES[lab], encoding="utf-8")) for lab in CMP}

# ---- 排除清单 ----
excl_csv = os.path.join(HERE, "排除清单.csv")
EXCLUDED = {}   # cid -> 主类别
if os.path.exists(excl_csv):
    with open(excl_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = (row.get("case_id") or "").strip()
            if cid:
                EXCLUDED[cid] = (row.get("主类别") or "").strip()
else:
    print("WARN: 排除清单.csv 不存在，本运行=86 全量控制组")

# ---- visit_type（组装清单.csv）----
vt_csv = os.path.join(ROOT, "sf10_阶段D", "组装清单.csv")
VISIT = {}
if os.path.exists(vt_csv):
    with open(vt_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            cid = (row.get("case_id") or "").strip()
            if cid:
                VISIT[cid] = (row.get("visit_type") or "").strip()
else:
    print("WARN: 组装清单.csv 不存在，分层输出缺 visit_type")

def per_case_metrics(G, P):
    tp = len(P & G); fp = len(P - G); fn = len(G - P)
    recall = tp / len(G) if G else None
    prec = tp / len(P) if P else None
    f1 = (2 * prec * recall / (prec + recall)) if (prec and recall and (prec + recall) > 0) else (0.0 if tp == 0 else None)
    jac = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=recall, prec=prec, f1=f1, jac=jac)

PER = {}
for cid in CASE_IDS:
    G = set(NEW_RESULTS[cid]["gold_members"])
    d = {}
    for lab in CMP:
        rec = BLIND[lab].get(cid)
        if rec is None:
            d[lab] = None; continue
        Pm = normalize_acupoints(rec.get("主穴", []))
        Pa = normalize_acupoints(rec.get("主穴", []) + rec.get("佐穴", []))
        d[lab] = dict(units_main=len(rec.get("主穴", [])), points_main=len(Pm), points_all=len(Pa),
                      main=per_case_metrics(G, Pm), all=per_case_metrics(G, Pa),
                      pred_main=sorted(Pm), layers=rec.get("主穴分层", {}))
    PER[cid] = dict(gold=sorted(G), gc=len(G), new=d,
                    chain=SUMMARY["chain_map"].get(cid, "first_visit"),
                    visit=VISIT.get(cid, ""), note=NEW_RESULTS[cid]["note"])

SCORED = [c for c in CASE_IDS if PER[c]["gc"] > 0]
UNSCORED = [c for c in CASE_IDS if PER[c]["gc"] == 0]
CORE = [c for c in SCORED if c not in EXCLUDED]

def macro(lab, subset, metric, cids):
    v = []
    for c in cids:
        dd = PER[c]["new"].get(lab)
        if dd is None: continue
        x = dd[subset][metric]
        if x is not None: v.append(x)
    return statistics.mean(v) if v else None

def micro(lab, subset, metric, cids):
    tp = fp = fn = 0
    for c in cids:
        dd = PER[c]["new"].get(lab)
        if dd is None: continue
        m = dd[subset]; tp += m["tp"]; fp += m["fp"]; fn += m["fn"]
    if metric == "recall": return tp / (tp + fn) if (tp + fn) else None
    if metric == "prec": return tp / (tp + fp) if (tp + fp) else None
    if metric == "f1":
        r = tp / (tp + fn) if (tp + fn) else 0; p = tp / (tp + fp) if (tp + fp) else 0
        return 2 * p * r / (p + r) if (p + r) else 0.0
    if metric == "jac": return tp / (tp + fp + fn) if (tp + fp + fn) else 0.0

def dist(vals):
    b = {"100%": 0, "80-99%": 0, "60-79%": 0, "40-59%": 0, "<40%": 0}
    for x in vals:
        if x is None: continue
        if x >= 0.999: b["100%"] += 1
        elif x >= 0.8: b["80-99%"] += 1
        elif x >= 0.6: b["60-79%"] += 1
        elif x >= 0.4: b["40-59%"] += 1
        else: b["<40%"] += 1
    return b

ro = lambda x: None if x is None else round(x, 4)

def block(lab, cids, tag):
    ms = {}
    for subset in ("main", "all"):
        ms[subset] = dict(
            macro=dict(recall=ro(macro(lab, subset, "recall", cids)), prec=ro(macro(lab, subset, "prec", cids)),
                       f1=ro(macro(lab, subset, "f1", cids)), jac=ro(macro(lab, subset, "jac", cids))),
            micro=dict(recall=ro(micro(lab, subset, "recall", cids)), prec=ro(micro(lab, subset, "prec", cids)),
                       f1=ro(micro(lab, subset, "f1", cids)), jac=ro(micro(lab, subset, "jac", cids))))
    units = [PER[c]["new"][lab]["units_main"] for c in cids if PER[c]["new"].get(lab)]
    points = [PER[c]["new"][lab]["points_main"] for c in cids if PER[c]["new"].get(lab)]
    return dict(tag=tag, n=len(cids), metrics=ms,
                mean_units_main=round(statistics.mean(units), 3) if units else None,
                mean_points_main=round(statistics.mean(points), 3) if points else None,
                sum_tp_main=sum(PER[c]["new"][lab]["main"]["tp"] for c in cids if PER[c]["new"].get(lab)),
                dist_recall_main=dist([PER[c]["new"][lab]["main"]["recall"] for c in cids if PER[c]["new"].get(lab)]))

S = dict(n_cases=len(CASE_IDS), n_scorable=len(SCORED), n_unscored=len(UNSCORED),
         excluded=EXCLUDED, n_excluded=len(EXCLUDED), n_core=len(CORE),
         core_list=sorted(CORE),
         unscored={c: PER[c]["note"] for c in UNSCORED})
S["全量86"] = {lab: block(lab, SCORED, "全量86") for lab in CMP}
S["核心集"] = {lab: block(lab, CORE, "核心集") for lab in CMP}

# 核心集内分层：visit_type 首诊 vs 复诊（按前缀分桶，兼容"复诊（依据：…）"注释值）
def vt_bucket(c):
    v = PER[c]["visit"] or ""
    if v.startswith("复诊") or v.startswith("復診"): return "复诊"
    if v.startswith("首诊") or v.startswith("首診"): return "首诊"
    return "其他"
vt_fz = [c for c in CORE if vt_bucket(c) == "复诊"]
vt_sz = [c for c in CORE if vt_bucket(c) == "首诊"]
vt_qt = [c for c in CORE if vt_bucket(c) == "其他"]
S["核心集_visit分层"] = dict(
    复诊=dict(n=len(vt_fz), cases=sorted(vt_fz),
              **{lab: dict(main_macro_recall=ro(macro(lab, "main", "recall", vt_fz)),
                           main_macro_f1=ro(macro(lab, "main", "f1", vt_fz)),
                           all_macro_recall=ro(macro(lab, "all", "recall", vt_fz))) for lab in CMP}),
    首诊=dict(n=len(vt_sz), cases=sorted(vt_sz),
              **{lab: dict(main_macro_recall=ro(macro(lab, "main", "recall", vt_sz)),
                           main_macro_f1=ro(macro(lab, "main", "f1", vt_sz)),
                           all_macro_recall=ro(macro(lab, "all", "recall", vt_sz))) for lab in CMP}),
    其他=dict(n=len(vt_qt), cases=sorted(vt_qt)))
# 核心集内 chain 分层（跟随案已排除，应有 followup=0；anchor+first 列示）
follow = [c for c in CORE if PER[c]["chain"].startswith("followup")]
af = [c for c in CORE if not PER[c]["chain"].startswith("followup")]
S["核心集_chain分层"] = dict(followup=dict(n=len(follow), cases=sorted(follow)),
                            anchor_first=dict(n=len(af), cases=sorted(af),
                            **{lab: dict(main_macro_recall=ro(macro(lab, "main", "recall", af)),
                                         main_macro_f1=ro(macro(lab, "main", "f1", af))) for lab in CMP}))

# 零命中/满分（核心集）
S["核心集零命中"] = {lab: [c for c in CORE if PER[c]["new"][lab]["main"]["tp"] == 0] for lab in CMP}
S["核心集满分"] = {lab: [c for c in CORE if PER[c]["new"][lab]["main"]["recall"] and PER[c]["new"][lab]["main"]["recall"] >= 0.999] for lab in CMP}

# ---- 明细 CSV（93 行：86 判分 + 7 未判分，含排除标记与核心集口径）----
header = ["case_id", "chain", "visit_type", "排除主类别", "排除?", "gold穴数",
          "v10单元数", "v10点数", "v10_tp", "v10_recall_main", "v10_prec_main", "v10_f1_main", "v10_jac_main",
          "命中清单", "漏穴清单", "未命中清单", "备注"]
rows = []
for c in SCORED:
    n = PER[c]["new"]["v10"]; G = set(PER[c]["gold"]); P = set(n["pred_main"])
    ex = EXCLUDED.get(c, "")
    rows.append([c, PER[c]["chain"], PER[c]["visit"], ex, "排除" if ex else "保留",
                 PER[c]["gc"], n["units_main"], n["points_main"], n["main"]["tp"],
                 ro(n["main"]["recall"]), ro(n["main"]["prec"]), ro(n["main"]["f1"]), ro(n["main"]["jac"]),
                 ";".join(sorted(P & G)), ";".join(sorted(G - P)), ";".join(sorted(P - G)), PER[c]["note"]])
for c in UNSCORED:
    ex = EXCLUDED.get(c, "")
    rows.append([c, PER[c]["chain"], PER[c]["visit"], ex, "未判分",
                 0, "", "", "", "", "", "", "", "", "", "", PER[c]["note"]])
with open(os.path.join(HERE, "判分明细_核心集.csv"), "w", newline="", encoding="utf-8-sig") as f:
    csv.writer(f).writerows([header] + rows)
with open(os.path.join(HERE, "判分汇总_核心集.json"), "w", encoding="utf-8") as f:
    json.dump(S, f, ensure_ascii=False, indent=2)

# ---- 控制台 ----
print("n_scorable=%d n_excluded=%d n_core=%d" % (len(SCORED), len(EXCLUDED), len(CORE)))
print("排除案(主类别):", json.dumps(EXCLUDED, ensure_ascii=False))
for tag, blk in (("全量86", S["全量86"]), ("核心集", S["核心集"])):
    print("== " + tag + " ==")
    for lab in CMP:
        m = blk[lab]["metrics"]
        print(f"{lab} main: R={m['main']['macro']['recall']} P={m['main']['macro']['prec']} F1={m['main']['macro']['f1']} Jac={m['main']['macro']['jac']} | units均={blk[lab]['mean_units_main']} 点均={blk[lab]['mean_points_main']} tp={blk[lab]['sum_tp_main']} n={blk[lab]['n']}")
        print(f"{lab} all : R={m['all']['macro']['recall']} P={m['all']['macro']['prec']} F1={m['all']['macro']['f1']} Jac={m['all']['macro']['jac']}")
        print(f"{lab} micro main: R={m['main']['micro']['recall']} P={m['main']['micro']['prec']} F1={m['main']['micro']['f1']} Jac={m['main']['micro']['jac']}")
print("核心集零命中:", json.dumps(S["核心集零命中"], ensure_ascii=False))
print("核心集满分:", json.dumps(S["核心集满分"], ensure_ascii=False))
print("visit分层 n:", S["核心集_visit分层"]["复诊"]["n"], S["核心集_visit分层"]["首诊"]["n"])
