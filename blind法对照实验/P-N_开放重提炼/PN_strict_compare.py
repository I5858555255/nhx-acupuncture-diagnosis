#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-B「严格洁净复跑」对比：6 个协议泄漏案以最严读取纪律重跑后的结果。

- 原跑（as-run，含协议泄漏，已归档为 `留出案预测_复跑前.json`） vs 严格复跑（当前 `留出案预测.json`）
- 其余 60 折两者相同；仅这 6 案变化。
输出 PN_strict_score.txt / PN_strict_summary.json（**不覆盖** as-run 的 PN_all_*）。
只读；唯一评分器口径。
"""
import io
import json
import os
import pickle
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}
FOLDS = json.load(io.open(os.path.join(HERE, "PN_folds_all.json"), encoding="utf-8"))
ALLF = sorted(FOLDS["done"] + FOLDS["todo"])
RERUN = ["S_156_06", "S_194_01", "S_1_01", "S_208_01", "S_213_01", "S_216_04"]


def f1(P, g):
    P = set(P)
    t = len(P & g)
    rc = t / len(g) if g else 0.0
    pr = t / len(P) if P else 0.0
    return (2 * pr * rc / (pr + rc)) if (pr + rc) > 0 else 0.0


def agg(pred, ids):
    tp = fp = fn = 0
    fs = []
    for c in ids:
        P = set(normalize_units(pred.get(c, [])))
        g = GOLD[c]
        tp += len(P & g)
        fp += len(P - g)
        fn += len(g - P)
        fs.append(f1(P, g))
    return tp, fp, fn, (round(statistics.mean(fs), 4) if fs else 0.0)


STRICT, ASRUN = {}, {}
ids_all = []
for fid in ALLF:
    ids = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]
    ids_all += ids
    cur = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案预测.json"), encoding="utf-8"))
    STRICT.update(cur)
    old = os.path.join(HERE, "packets", fid, "留出案预测_复跑前.json")
    ASRUN.update(json.load(io.open(old, encoding="utf-8")) if os.path.isfile(old) else cur)

r_s = agg(STRICT, ids_all)
r_a = agg(ASRUN, ids_all)

OUT = ["== P-N-B 严格洁净复跑（6 案）对比 ==", ""]
nchg = 0
for fid in RERUN:
    ids = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]
    cur = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案预测.json"), encoding="utf-8"))
    old = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案预测_复跑前.json"), encoding="utf-8"))
    for c in ids:
        a, s = f1(old.get(c, []), GOLD[c]), f1(cur.get(c, []), GOLD[c])
        tag = "  <== 变化" if abs(a - s) > 1e-9 else ""
        if tag:
            nchg += 1
        OUT.append("%-8s 原跑(含泄漏) %.4f (%d穴) → 严格复跑 %.4f (%d穴)  Δ%+.4f%s"
                   % (c, a, len(old.get(c, [])), s, len(cur.get(c, [])), s - a, tag))
OUT.append("")
OUT.append("--- 全 %d 案聚合 ---" % len(ids_all))
OUT.append("原跑（as-run，含 12 条协议泄漏） : TP%d/FP%d/FN%d  F1 %.4f" % r_a)
OUT.append("严格复跑（6 案洁净）            : TP%d/FP%d/FN%d  F1 %.4f" % r_s)
OUT.append("ΔF1(严格-原跑) = %+.4f ；变化案 %d/6" % (r_s[3] - r_a[3], nchg))
OUT.append("")
OUT.append("注：仍为**上界估计**（执行者＝同族 LLM，非独立临床盲审；天真全案再推理）。")
OUT.append("参考：v14r5 0.5185 / v17 0.5233 / v18 0.5949 / 机械 k-NN 0.4307 / 关联规则 0.3007。")

io.open(os.path.join(HERE, "PN_strict_score.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
json.dump({"strict": r_s, "as_run": r_a, "changed_cases": nchg, "rerun_folds": RERUN},
          io.open(os.path.join(HERE, "PN_strict_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n".join(OUT))
