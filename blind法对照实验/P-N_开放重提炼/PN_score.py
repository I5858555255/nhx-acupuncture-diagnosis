#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-B 评分：对 LLM 开放重提炼的留出预测（盲包）用唯一正式评分器复算。

输出：逐折 F1、30 案聚合 F1、与基线 v14r5 / 现行 v17 在同案上的对比；
并显式登记**泄漏事件**（子代理误读 SKILL.md 行的案）。

只读输入 + packets/ 的 留出案预测.json；只写 PN_b_score.txt / PN_b_summary.json。
"""
import csv
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
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}

FOLDS = json.load(io.open(os.path.join(HERE, "PN_folds.json"), encoding="utf-8"))["folds"]


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
    return tp, fp, fn, round(statistics.mean(fs), 4)


# v14r5 基线
B = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
BASE = {c: [str(x) for x in (B[c].get("主穴", []) or [])] for c in SC}

# 现行 v17 技能口径（自算）
spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
add_kw = spec["已登记规则追加关键词"]
kw17 = json.load(io.open(os.path.join(PM, "PM_原书词表_v17.json"), encoding="utf-8"))["单元证候关键词"]
REC = {c: {str(e.get("穴", "")).strip(): e for e in (B[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: ln for ln, pts in (B[c].get("主穴分层") or {}).items() for u in pts} for c in SC}


def sym(c):
    d = json.load(io.open(os.path.join(SD, "%s_symptoms_v2.json" % c), encoding="utf-8"))
    b = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            b.append(str(v["片段"]))
        elif isinstance(v, str):
            b.append(v)
    return "".join(b)


SYM = {c: sym(c) for c in SC}
COND = {"条件_依据含_M2-04_或_腋": lambda d: ("M2-04" in d or "腋" in d),
        "条件_依据含_R2_或_M2-05_或_心脏条": lambda d: ("R2" in d or "M2-05" in d or "心脏条" in d)}
V17 = json.loads(json.dumps(BASE))
for c in SC:
    d = set()
    for u in BASE[c]:
        if LAYER[c].get(u, "") != spec["作用层"] or u in spec["排除单元"]:
            continue
        keys = kw17.get(u)
        if keys is None:
            continue
        keys = list(keys)
        dep = str(REC[c].get(str(u).strip(), {}).get("依据", ""))
        for cond, ex in add_kw.items():
            if COND[cond](dep):
                keys += ex
        if not [k for k in keys if k in SYM[c]]:
            d |= set(normalize_units([u]))
    V17[c] = [p for p in BASE[c] if not (normalize_units([p]) and next(iter(normalize_units([p]))) in d)]

LEAK = {"303_01": "grep 误命中 SKILL.md 行（透露 303_01 含「列缺」）——预测可能受污染",
        "221_01": "grep 误命中 SKILL.md/变更记录行（子代理称未据以增删）",
        "160_01": "grep 误命中 SKILL.md/变更记录行（子代理称未据以增删）"}

OUT = []
ids_all = []
for fid in FOLDS:
    pj = os.path.join(HERE, "packets", fid, "留出案预测.json")
    raw = json.load(io.open(pj, encoding="utf-8"))
    ids = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]
    ids_all += ids
    llm = {c: raw.get(c, []) for c in ids}
    rl = agg(llm, ids)
    rb = agg(BASE, ids)
    rv = agg(V17, ids)
    OUT.append("%-14s n=%-2d | LLM %s F1 %.4f | 基线 %s F1 %.4f | v17 %s F1 %.4f | Δ(LLM-基线) %+.4f"
               % (fid, len(ids), (rl[0], rl[1], rl[2]), rl[3], (rb[0], rb[1], rb[2]), rb[3],
                  (rv[0], rv[1], rv[2]), rv[3], rl[3] - rb[3]))
    if any(c in LEAK for c in ids):
        OUT.append("      [WARN] 泄漏登记：%s" % "；".join("%s: %s" % (c, LEAK[c]) for c in ids if c in LEAK))

print("== P-N-B 评分（LLM 开放重提炼 · 10 折 / %d 案 = %.0f%% of 86） ==" % (len(ids_all), 100.0 * len(ids_all) / len(SC)))
for l in OUT:
    print(l)

# 汇总：LLM 预测（合并所有折）
LLM_ALL = {}
for fid in FOLDS:
    raw = json.load(io.open(os.path.join(HERE, "packets", fid, "留出案预测.json"), encoding="utf-8"))
    LLM_ALL.update(raw)
r_llm = agg(LLM_ALL, ids_all)
r_base = agg(BASE, ids_all)
r_v17 = agg(V17, ids_all)
print("\n--- 聚合（仅这 %d 案，非全 86） ---" % len(ids_all))
print("LLM 开放重提炼 : TP%d/FP%d/FN%d  F1 %.4f" % r_llm)
print("基线 v14r5      : TP%d/FP%d/FN%d  F1 %.4f" % r_base)
print("现行 v17        : TP%d/FP%d/FN%d  F1 %.4f" % r_v17)
print("ΔF1(LLM-基线) = %+.4f  |  ΔF1(LLM-v17) = %+.4f" % (r_llm[3] - r_base[3], r_llm[3] - r_v17[3]))
print("\n[全 86 参照] v14r5 F1 0.5185；v17 F1 0.5233；机械 k-NN 0.4307；机械关联规则 0.3007")

idmap = {c: fid for fid in FOLDS for c in json.load(io.open(os.path.join(HERE, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]}
json.dump({"sampled_cases": len(ids_all), "coverage_pct": round(100.0 * len(ids_all) / len(SC), 1),
           "aggregate": {"LLM": r_llm, "baseline_v14r5": r_base, "v17": r_v17},
           "folds": FOLDS, "leak_register": LEAK},
          io.open(os.path.join(HERE, "PN_b_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
io.open(os.path.join(HERE, "PN_b_score.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
print("\nwrote PN_b_score.txt / PN_b_summary.json")
