# -*- coding: utf-8 -*-
"""SF10 阶段A：导出冻结产物 baseline_冻结.json + v9_逐案TP_FP_FN.csv"""
import json, os, sys, csv, pickle

BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段A"
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints

# ---------- 1) baseline_冻结.json ----------
with open(os.path.join(BENCH, "判分汇总v2.json"), encoding="utf-8") as f:
    S = json.load(f)

base = {
    "口径": "点级 precision/recall/F1/Jaccard；宏平均=逐案先算再平均，微平均=全案TP求和；main=主穴，all=主+佐；86案同gold（开发集）",
    "n_cases": S["n_cases"],
    "n_scorable": S["n_scorable"],
    "n_unscored": S["n_unscored"],
    "unscored": S["unscored"],
    "chain_map摘要": {
        "anchor案": sorted([v for v in S["分层_v9"]["chain_names"] if v.startswith("anchor")]),
        "followup链": sorted([v for v in S["分层_v9"]["chain_names"] if v.startswith("followup")]),
        "followup案数": S["分层_v9"]["followup"]["n"],
        "anchor_first案数": S["分层_v9"]["anchor_first"]["n"],
        "chain_names": S["分层_v9"]["chain_names"],
    },
}
for lab in ["v5", "v6", "v9"]:
    L = S[lab]
    base[lab] = {
        "metrics": L["metrics"],  # 含 main/all × macro/micro × recall/prec/f1/jac
        "mean_units_main": L["mean_units_main"],
        "mean_points_main": L["mean_points_main"],
        "sum_points_main": L["sum_points_main"],
        "sum_points_all": L["sum_points_all"],
        "sum_tp_main": L["sum_tp_main"],
        "sum_tp_all": L["sum_tp_all"],
    }
# v9 附加统计
base["v9附加"] = {
    "分布_recall_main": S["dist_v9_recall_main"],
    "分布_jac_main": S["dist_v9_jac_main"],
    "零命中案": S["v9零命中_recall"],
    "分层": {
        "followup_macro_recall": S["分层_v9"]["followup"]["macro_recall"],
        "followup_macro_prec": S["分层_v9"]["followup"]["macro_prec"],
        "anchor_first_macro_recall": S["分层_v9"]["anchor_first"]["macro_recall"],
        "anchor_first_macro_prec": S["分层_v9"]["anchor_first"]["macro_prec"],
    },
    "旧口径汇总_v9": S["旧口径汇总_v9"],
}
with open(os.path.join(OUT, "baseline_冻结.json"), "w", encoding="utf-8") as f:
    json.dump(base, f, ensure_ascii=False, indent=2)
print("baseline_冻结.json written")

# ---------- 2) v9_逐案TP_FP_FN.csv ----------
with open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb") as f:
    GOLD = pickle.load(f)
RESULTS = GOLD["results"]; CASE_IDS = GOLD["case_ids"]; SUMMARY = GOLD["summary"]
with open(os.path.join(os.path.dirname(BENCH), "盲法93_v9", "_blind93v9_results.json"), encoding="utf-8") as f:
    BLIND9 = json.load(f)

def f4(x):
    return "" if x is None else f"{x:.4f}"

rows = []
zero_hit = []; full_mark = []
recs_r = []; recs_p = []; recs_f = []; recs_j = []
for cid in CASE_IDS:
    G = set(RESULTS[cid]["gold_members"])
    gc = len(G)
    rec = BLIND9.get(cid)
    chain = SUMMARY["chain_map"].get(cid, "first_visit")
    note = RESULTS[cid]["note"]
    if rec is None or gc == 0:
        rows.append([cid, chain, gc, "", "", "", "", "", "", "", "", "", "", "",
                     ("不可判分: " + note) if gc == 0 else "无v9记录"])
        continue
    main_units = rec.get("主穴", [])
    Pm = normalize_acupoints(main_units)
    tp_set = Pm & G
    fp_set = Pm - G
    fn_set = G - Pm
    tp = len(tp_set); fp = len(fp_set); fn = len(fn_set)
    recall = tp / gc if gc else None
    prec = tp / len(Pm) if Pm else None
    f1 = (2*prec*recall/(prec+recall)) if (prec and recall and prec+recall > 0) else (0.0 if tp == 0 else None)
    jac = tp / (tp+fp+fn) if (tp+fp+fn) else 0.0
    rows.append([cid, chain, gc, len(main_units), len(Pm), tp, fp, fn,
                 f4(recall), f4(prec), f4(f1), f4(jac),
                 ";".join(sorted(tp_set)), ";".join(sorted(fn_set)), ";".join(sorted(fp_set))])
    # 统计
    if tp == 0: zero_hit.append(cid)
    if gc > 0 and tp == gc: full_mark.append(cid)
    if recall is not None: recs_r.append(recall)
    if prec is not None: recs_p.append(prec)
    if f1 is not None: recs_f.append(f1)
    recs_j.append(jac)

header = ["case_id", "chain", "gold_count", "units_main", "points_main",
          "tp", "fp", "fn", "recall", "prec", "f1", "jac",
          "命中清单(TP=pred∩gold)", "漏穴清单(FN=gold−pred)", "未命中清单(FP=pred−gold)"]
with open(os.path.join(OUT, "v9_逐案TP_FP_FN.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(rows)
print(f"v9_逐案TP_FP_FN.csv written: {len(rows)} rows")

# 汇总打印（供报告引用）
import statistics
print(f"零命中案({len(zero_hit)}): {zero_hit}")
print(f"满分案({len(full_mark)}): {full_mark}")
print(f"v9 逐案宏均值: recall={statistics.mean(recs_r):.4f} prec={statistics.mean(recs_p):.4f} f1={statistics.mean(recs_f):.4f} jac={statistics.mean(recs_j):.4f}")

# 把统计写入 sidecar 供报告引用
sidecar = {
    "zero_hit": zero_hit, "full_mark": full_mark,
    "macro_recall": statistics.mean(recs_r), "macro_prec": statistics.mean(recs_p),
    "macro_f1": statistics.mean(recs_f), "macro_jac": statistics.mean(recs_j),
}
with open(os.path.join(OUT, "_v9_per_case_stats.json"), "w", encoding="utf-8") as f:
    json.dump(sidecar, f, ensure_ascii=False, indent=2)
