# -*- coding: utf-8 -*-
"""生成 逐案新旧差异表.csv（86 判分案，v9→v10 symptom-only）。
数据源全部只读：
- 盲法93_v9/判分明细.csv（v9: gold穴数, v9主穴数, v9命中主）
- 盲法93_v10/判分明细v10.csv（v10 逐案指标 + chain）
- 盲法93_v10/判分汇总v10.json（逐案_v9_v10 配对列 + 执行方差差异清单）
口径：点级（归一化后规范穴点），与 baseline_冻结.json / 判分汇总v10.json 一致。
"""
import csv, json, os

BASE = r"D:\projectAGI\nhx\盲法对照实验"
OUT = os.path.join(BASE, "sf10_阶段F", "逐案新旧差异表.csv")

# ---- v9 明细 ----
v9 = {}
with open(os.path.join(BASE, "盲法93_v9", "判分明细.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        v9[row["case_id"]] = row

# ---- v10 明细 ----
v10 = {}
with open(os.path.join(BASE, "盲法93_v10", "判分明细v10.csv"), encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        v10[row["case_id"]] = row

# ---- v10 汇总：配对列 + 差异清单 ----
with open(os.path.join(BASE, "盲法93_v10", "判分汇总v10.json"), encoding="utf-8") as f:
    summ = json.load(f)
paired = {r["case_id"]: r for r in summ["逐案_v9_v10"]}
diff_map = {}
for d in summ["执行方差_v10_vs_v9"]["差异清单"]:
    diff_map[d["case_id"]] = d["v9"]  # v9 有而 v10 删除的单元

def f2(x):
    try:
        return round(float(x), 4)
    except Exception:
        return ""

rows = []
for cid, r10 in v10.items():
    if r10["chain"] == "unscored" or r10["gold穴数"] in ("", "0"):
        continue  # 7 个不可判分案不进 86 行表
    gold = float(r10["gold穴数"])
    tp10 = float(r10["v10_tp"] or 0)
    pts10 = float(r10["v10点数"] or 0)
    p9 = paired[cid]
    # v9 指标口径说明：盲法93_v9/判分明细.csv 的“v9主穴数/v9命中主”为旧口径
    # （sum_tp=258、sum_单元=593，见 baseline_冻结.json.旧口径汇总_v9），与新点级口径
    # （sum_tp=268、sum_points=746）不可混比。因此 v9 逐案 recall/f1 直接取
    # 判分汇总v10.json.逐案_v9_v10 配对列；prec 由 R/F1 代数反解 P=R*F1/(2R-F1)，
    # TP=R*|G|、|P|=TP/P、Jaccard=TP/(|G|+|P|-TP)，不重跑任何实验。
    recall9 = float(p9["v9_recall"])
    f1_9 = float(p9["v9_f1"])
    if f1_9 > 0 and (2*recall9 - f1_9) > 1e-9:
        prec9 = recall9*f1_9/(2*recall9 - f1_9)
    else:
        prec9 = 0.0
    tp9 = recall9 * gold
    pts9 = tp9/prec9 if prec9 > 1e-9 else 0.0
    jac9 = tp9/(gold + pts9 - tp9) if (gold + pts9 - tp9) > 1e-9 else 0.0
    # v10 指标直接取明细
    recall10 = float(r10["v10_recall_main"])
    prec10 = float(r10["v10_prec_main"])
    f1_10 = float(r10["v10_f1_main"])
    jac10 = float(r10["v10_jac_main"])
    # 集合变化
    if cid in diff_map:
        chg = "减穴"
        note = "v9较v10多出单元: " + "、".join(diff_map[cid])
    else:
        chg = "不变"
        note = "主穴集合与v9一致"
    rows.append({
        "case_id": cid,
        "chain": r10["chain"],
        "gold穴数": int(gold),
        "v9_recall": round(recall9, 4), "v9_prec": round(prec9, 4),
        "v9_f1": round(f1_9, 4), "v9_jac": round(jac9, 4),
        "v9_tp(派生)": round(tp9, 1), "v9_fp(派生)": round(pts9 - tp9, 1), "v9_fn": int(gold - tp9),
        "v9主穴点数(派生)": round(pts9, 1),
        "v10_recall": round(recall10, 4), "v10_prec": round(prec10, 4),
        "v10_f1": round(f1_10, 4), "v10_jac": round(jac10, 4),
        "v10_tp": int(tp10), "v10_fp": int(pts10 - tp10), "v10_fn": int(gold - tp10),
        "v10主穴点数": int(pts10),
        "Δf1(v10-v9)": round(f1_10 - f1_9, 4),
        "主穴集合变化": chg,
        "差异说明": note,
    })

rows.sort(key=lambda r: r["case_id"])

cols = ["case_id","chain","gold穴数",
        "v9_recall","v9_prec","v9_f1","v9_jac","v9_tp(派生)","v9_fp(派生)","v9_fn","v9主穴点数(派生)",
        "v10_recall","v10_prec","v10_f1","v10_jac","v10_tp","v10_fp","v10_fn","v10主穴点数",
        "Δf1(v10-v9)","主穴集合变化","差异说明"]
with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)

# ---- 自检 ----
n = len(rows)
mr9 = sum(r["v9_recall"] for r in rows)/n
mp9 = sum(r["v9_prec"] for r in rows)/n
mf9 = sum(r["v9_f1"] for r in rows)/n
mj9 = sum(r["v9_jac"] for r in rows)/n
mr10 = sum(r["v10_recall"] for r in rows)/n
mp10 = sum(r["v10_prec"] for r in rows)/n
mf10 = sum(r["v10_f1"] for r in rows)/n
mj10 = sum(r["v10_jac"] for r in rows)/n
print("行数:", n)
print(f"v9  宏 recall={mr9:.4f} prec={mp9:.4f} f1={mf9:.4f} jac={mj9:.4f}")
print(f"v10 宏 recall={mr10:.4f} prec={mp10:.4f} f1={mf10:.4f} jac={mj10:.4f}")
print("v9  sum_tp(派生)=", round(sum(r["v9_tp(派生)"] for r in rows),1),
      " sum_points(派生)=", round(sum(r["v9主穴点数(派生)"] for r in rows),1))
print("v10 sum_tp=", sum(r["v10_tp"] for r in rows), " sum_points=", sum(r["v10主穴点数"] for r in rows))
print("集合变化: 不变=", sum(1 for r in rows if r["主穴集合变化"]=="不变"),
      " 减穴=", sum(1 for r in rows if r["主穴集合变化"]=="减穴"))
print("输出:", OUT)
