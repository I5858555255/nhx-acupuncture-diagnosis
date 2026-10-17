#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R1 审查配套：对"原书从零表 + 微修候选"做量化（只读）。

变体：
  ① v16_从零（现行）= PM_原书词表.json
  ② 从零 + 列缺.皮（肺主皮毛/肺经络穴，指南6.4；用于保留 303_01 的 列缺）
  ③ 从零 + 列缺.皮 + (列缺+照海).乾 + 照海.乾（再保留 160_01 的 口干）
只读；只写本目录。
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
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

SPEC = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
KW_NEW = json.load(io.open(os.path.join(PM, "PM_原书词表.json"), encoding="utf-8"))["单元证候关键词"]
ADD = SPEC["已登记规则追加关键词"]

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}
EXCLUDE = set(r["case_id"] for r in csv.DictReader(io.open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
CORE = [c for c in SC if c not in EXCLUDE]
PRED = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
REC = {c: {str(e.get("穴", "")).strip(): e for e in (PRED[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: ln for ln, pts in (PRED[c].get("主穴分层") or {}).items() for u in pts} for c in SC}
COND = {"条件_依据含_M2-04_或_腋": lambda d: ("M2-04" in d or "腋" in d),
        "条件_依据含_R2_或_M2-05_或_心脏条": lambda d: ("R2" in d or "M2-05" in d or "心脏条" in d)}


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


def dels(c, kwt):
    out = set()
    for u in (PRED[c].get("主穴", []) or []):
        if LAYER[c].get(u, "") != SPEC["作用层"] or u in SPEC["排除单元"]:
            continue
        keys = kwt.get(u)
        if keys is None:
            continue
        keys = list(keys)
        dep = str(REC[c].get(str(u).strip(), {}).get("依据", ""))
        for cond, ex in ADD.items():
            if COND[cond](dep):
                keys += ex
        if not [k for k in keys if k in SYM[c]]:
            out |= set(normalize_units([u]))
    return out


def evalset(pred):
    per = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        g = GOLD[c]
        t = len(P & g)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        per[c] = (t, len(P - g), len(g - P), (2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0))
    return per


def blk(per, ids):
    return (sum(per[c][0] for c in ids), sum(per[c][1] for c in ids), sum(per[c][2] for c in ids),
            round(statistics.mean([per[c][3] for c in ids]), 4))


BASE = evalset(PRED)
b86 = blk(BASE, SC)
print("基线 v14r5:", b86)


def with_kw(extra):
    t = {u: list(v) for u, v in KW_NEW.items()}
    for u, ks in extra.items():
        t[u] = list(dict.fromkeys(t[u] + ks))
    return t


VARIANTS = [
    ("v16_从零（现行）", {}),
    ("从零+列缺.皮", {"列缺": ["皮"]}),
    ("从零+列缺.皮+照海.乾+pair.乾", {"列缺": ["皮"], "照海": ["乾", "干"], "列缺+照海": ["乾", "干"]}),
]
res = []
for name, extra in VARIANTS:
    kwt = with_kw(extra)
    D = {c: dels(c, kwt) for c in SC}
    D = {c: v for c, v in D.items() if v}
    data = json.loads(json.dumps(PRED))
    for c, d in D.items():
        data[c]["主穴"] = [p for p in data[c].get("主穴", []) if not (normalize_units([p]) and next(iter(normalize_units([p]))) in d)]
    per = evalset(data)
    r86 = blk(per, SC)
    r64 = blk(per, CORE)
    side = [c for c in SC if per[c][0] < BASE[c][0] or per[c][1] > BASE[c][1]]
    res.append((name, sorted(D), sum(len(v) for v in D.values()), r86, r64, side))
    print("%-34s 触发%2d案 删%2d穴 | 86 %s ΔTP%+d ΔFP%+d ΔF1%+.4f | 64 F1 %.4f(Δ%+.4f) | 副作用%s"
          % (name, len(D), sum(len(v) for v in D.values()), r86,
             r86[0] - b86[0], r86[1] - b86[1], r86[3] - b86[3], r64[3], r64[3] - blk(BASE, CORE)[3],
             "、".join(side) or "0"))

out = ["R1 微修量化（基线 v14r5：TP%d/FP%d/FN%d/F1 %.4f）" % b86]
for name, trig, units, r86, r64, side in res:
    out.append("- %s：触发 %s（%d 案/%d 穴）" % (name, "、".join(trig), len(trig), units))
    out.append("    全量86 TP%d/FP%d/FN%d/F1 %.4f | 64 F1 %.4f | 副作用 %s"
               % (r86[0], r86[1], r86[2], r86[3], r64[3], "、".join(side) or "0"))
io.open(os.path.join(HERE, "R1_surgical_quant.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("wrote R1_surgical_quant.txt")
