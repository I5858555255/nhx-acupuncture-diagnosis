#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WS-5 口径差异：canonical 86 案（v14r5） vs 真盲法 86 可判分案（`盲法140`）。

产出可核对的分解数字：同一批案号上的
  - canonical：TP/FP/FN、recall、precision、macro-F1（统一归一化点级）
  - 真盲法140：重合率(主) = blind主∩gold / gold（均值、逐案）
并计算两集合交叠、以及**限制在同一交叠集合**上的两口径差。
只读；写 WS-5_口径差异_数字.txt。
"""
import csv
import io
import json
import os
import pickle
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))          # blind法对照实验
REPO = os.path.dirname(HERE)                                # 仓库根
OTHER = os.path.join(REPO, "盲法对照实验")                  # 历史实验树（只读）
BENCH = os.path.join(OTHER, "benchmark_v2")
G = os.path.join(OTHER, "sf10_阶段M5", "G_验收")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}
B = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
PRED = {c: [str(x) for x in (B[c].get("主穴", []) or [])] for c in SC}

rows = list(csv.DictReader(io.open(os.path.join(OTHER, "盲法140", "判分明细.csv"),
                                   encoding="utf-8-sig")))


def fnum(s):
    try:
        return float(str(s).strip())
    except Exception:
        return None


m140 = {}
for r in rows:
    cid = str(r.get("case_id", "")).strip()
    g = fnum(r.get("gold穴数"))
    if cid and g and g > 0:
        m140[cid] = {"gold": int(g), "recall": fnum(r.get("重合率主"))}


def canon(ids):
    tp = fp = fn = 0
    fs, rs = [], []
    for c in ids:
        P = set(normalize_units(PRED.get(c, [])))
        g = GOLD[c]
        t = len(P & g)
        tp += t
        fp += len(P - g)
        fn += len(g - P)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        rs.append(rc)
        fs.append(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0)
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    pre = tp / (tp + fp) if (tp + fp) else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=round(rec, 4), precision=round(pre, 4),
                macro_f1=round(statistics.mean(fs), 4) if fs else 0.0,
                mean_recall=round(statistics.mean(rs), 4) if rs else 0.0)


inter = sorted(set(SC) & set(m140))
can_all, can_int = canon(SC), canon(inter)
r140_all = [m140[c]["recall"] for c in m140 if m140[c]["recall"] is not None]
r140_int = [m140[c]["recall"] for c in inter if m140[c]["recall"] is not None]

OUT = []
OUT.append("== WS-5 口径差异：数字分解 ==")
OUT.append("")
OUT.append("canonical 可判分集（_gold_results93v2）案数 = %d" % len(SC))
OUT.append("真盲法140 可判分集（判分明细.csv gold>0）案数 = %d" % len(m140))
OUT.append("两集合**交叠**案数 = %d；canonical-only = %d；140-only = %d"
           % (len(inter), len(set(SC) - set(inter)), len(set(m140) - set(inter))))
OUT.append("")
OUT.append("--- A. canonical v14r5（统一点级归一化）---")
OUT.append("全 %d 案 : TP%d/FP%d/FN%d  recall %.4f  precision %.4f  macro-F1 %.4f  逐案recall均值 %.4f"
           % (len(SC), can_all["tp"], can_all["fp"], can_all["fn"], can_all["recall"],
              can_all["precision"], can_all["macro_f1"], can_all["mean_recall"]))
OUT.append("交叠 %d 案: TP%d/FP%d/FN%d  recall %.4f  precision %.4f  macro-F1 %.4f  逐案recall均值 %.4f"
           % (len(inter), can_int["tp"], can_int["fp"], can_int["fn"], can_int["recall"],
              can_int["precision"], can_int["macro_f1"], can_int["mean_recall"]))
OUT.append("")
OUT.append("--- B. 真盲法140 口径（重合率(主)=命中/gold，独立盲跑 _blind140）---")
OUT.append("全 %d 案 重合率(主) 均值 %.4f" % (len(r140_all), statistics.mean(r140_all)))
if r140_int:
    OUT.append("交叠 %d 案 重合率(主) 均值 %.4f（中位 %.4f）"
               % (len(r140_int), statistics.mean(r140_int), statistics.median(r140_int)))
OUT.append("")
OUT.append("--- C. 分解（同一判分集交叠 %d 案）---" % len(inter))
if r140_int:
    d = can_int["mean_recall"] - statistics.mean(r140_int)
    OUT.append("canonical 逐案recall均值 %.4f  −  真盲法 重合率主均值 %.4f  =  %+.4f 个绝对百分点"
               % (can_int["mean_recall"], statistics.mean(r140_int), d))
OUT.append("")
OUT.append("--- D. 交叠案内「口径差」的构成（供报告引用）---")
OUT.append("1) 预测来源不同：canonical 用 `_blind93v14r5_results.json`（v14r5 冻结跑）；")
OUT.append("   真盲法用 `_blind140_results.json`（严格盲：输入仅症状、剥离诊断行、处方隔离、无自我判分）。")
OUT.append("2) 指标不同：canonical 报 F1（precision+recall 调和）；真盲法报 recall-only（重合率主）。")
OUT.append("3) gold 解析不同：真盲法140 剥侧别前缀、透刺按两端点、别名归并、gold 去重端点；")
OUT.append("   canonical 用 `normalize_units` 统一归一化（含膝五针/三皇/开四关展开规则）。")
OUT.append("4) 集合不同：两 86 案**并非同一批案号**（见上：交叠 %d，canonical-only %d，140-only %d）。"
           % (len(inter), len(set(SC) - set(inter)), len(set(m140) - set(inter))))

io.open(os.path.join(HERE, "WS-5_口径差异_数字.txt"), "w",
        encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
try:
    print("\n".join(OUT))
except UnicodeEncodeError:
    print("(非 GBK 字符略；结果已写入 WS-5_口径差异_数字.txt)")
