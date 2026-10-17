#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-C：机械「复诊延续」量化（全 86，无 LLM）。

明确区分两种口径（方法学要点）：
  A 部署上界：预测复诊案 = 该患者**上一次就诊**的主穴（跨全案取，含同折留出者）。
    —— 在真实部署中「上次处方」客观已知；但 M9 整链留出时它属同折 gold ⇒ **LOCO 下为泄漏**，
       故仅作 **部署上界**记录。
  B 合法 LOCO：仅当**上一次就诊案落在训练集**（不在本折）时才沿用其主穴，否则回落基线。
    —— 只有「首诊留出、复诊在册」类折（如 216_04）可合法测量。

患者分组：链标签（followup_*/anchor_* → 组=后缀）优先，否则 case_id 前缀；组内按案号数值排序。
只读；写 PN_c_*.txt/json。
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
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}

rows = list(csv.DictReader(io.open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig")))
chain_of = {r["case_id"]: r["chain"] for r in rows if r["case_id"] in set(SC)}

CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    if not str(r.get("在86判分", "")).strip().isdigit() or int(str(r["在86判分"]).strip()) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in set(SC)]
    if ids:
        CHAINS[r["链ID"]] = ids


def group_of(c):
    ch = chain_of.get(c, "")
    if ch.startswith("followup_") or ch.startswith("anchor_"):
        return ch.split("_", 1)[1]
    return c.split("_")[0]


GROUPS = {}
for c in SC:
    GROUPS.setdefault(group_of(c), []).append(c)
for g in GROUPS:
    GROUPS[g].sort(key=lambda x: (int(x.split("_")[1]), x))
FOLD_OF = {c: fid for fid, ids in CHAINS.items() for c in ids}

B = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
BASE = {c: [str(x) for x in (B[c].get("主穴", []) or [])] for c in SC}


def f1(P, g):
    P = set(normalize_units(P))
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


# 复诊案 = 组内存在更早案
PREV = {}
for g, ids in GROUPS.items():
    for i, c in enumerate(ids):
        if i > 0:
            PREV[c] = ids[i - 1]

PA = {c: list(BASE[c]) for c in SC}
PB = {c: list(BASE[c]) for c in SC}
legit = []
for c, p in PREV.items():
    PA[c] = sorted(GOLD[p])                       # A 部署上界（含同折 gold）
    if FOLD_OF.get(p) != FOLD_OF.get(c):          # p 在训练集（另一折 / 非链折）
        PB[c] = sorted(GOLD[p])
        legit.append(c)

OUT = []
OUT.append("复诊案数（组内存在更早案）=%d / %d" % (len(PREV), len(SC)))
OUT.append("其中【合法 LOCO 可测】（上一次就诊落在别折/训练集）=%d 案：%s" % (len(legit), "、".join(sorted(legit))))
OUT.append("")
OUT.append("基线 v14r5（全 86）: %s" % (agg(BASE, SC),))
OUT.append("A 部署上界（复诊=上次主穴）: %s" % (agg(PA, SC),))
OUT.append("B 合法 LOCO（仅训练集内的上次）: %s" % (agg(PB, SC),))
OUT.append("")
OUT.append("--- 复诊子集（%d 案）上的对比 ---" % len(PREV))
ids_p = sorted(PREV)
OUT.append("基线 : %s F1 %.4f" % (agg(BASE, ids_p)[:3], agg(BASE, ids_p)[3]))
OUT.append("A    : %s F1 %.4f  Δ=%+.4f" % (agg(PA, ids_p)[:3], agg(PA, ids_p)[3], agg(PA, ids_p)[3] - agg(BASE, ids_p)[3]))
OUT.append("B    : %s F1 %.4f  Δ=%+.4f" % (agg(PB, ids_p)[:3], agg(PB, ids_p)[3], agg(PB, ids_p)[3] - agg(BASE, ids_p)[3]))
OUT.append("")
OUT.append("--- 合法 LOCO 子集（%d 案） ---" % len(legit))
for lbl, P in (("基线", BASE), ("A", PA), ("B", PB)):
    r = agg(P, legit)
    OUT.append("%-4s: %s F1 %.4f" % (lbl, r[:3], r[3]))
OUT.append("")
for c in sorted(PREV):
    OUT.append("%-8s prev=%-8s fold=%-13s prevfold=%-13s | 基线F1 %.3f A %.3f B %.3f"
               % (c, PREV[c], FOLD_OF.get(c, "-"), FOLD_OF.get(PREV[c], "-"),
                  f1(BASE[c], GOLD[c]), f1(PA[c], GOLD[c]), f1(PB[c], GOLD[c])))

io.open(os.path.join(HERE, "PN_c_followup.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
json.dump({"prev_cases": len(PREV), "legit_cases": legit,
           "base86": agg(BASE, SC), "A86": agg(PA, SC), "B86": agg(PB, SC),
           "subset_base": agg(BASE, ids_p), "subset_A": agg(PA, ids_p), "subset_B": agg(PB, ids_p)},
          io.open(os.path.join(HERE, "PN_c_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote PN_c_followup.txt / PN_c_summary.json")
