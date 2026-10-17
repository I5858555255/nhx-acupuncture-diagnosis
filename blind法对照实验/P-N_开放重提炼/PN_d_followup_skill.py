#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-D：复诊延续「升级版」——用**技能自己对上次案的输出**（非 gold）作输入，全 86 复算。

关键：技能是**确定性逐案函数**，output(p) 与折无关；故 rule「复诊 c = output(上一诊 p)」
  不构成 LOCO 泄漏（P-N-C-A 用的是 gold，才是泄漏）。此为**可交付**增益。
组内按案号顺序**迭代组合**（若 p 本身是复诊，则用 p 的组合后输出）。

变体：
  D1 全部复诊案（组内存在更早案者，共 25）
  D2 仅"链内复诊"（chain∈followup_*，共 20）
  D3 仅"上次落在别折"（合法可测子集，共 5）
基线 = v17（现行技能）与 v14r5。
只读；写 PN_d_*.txt/json。
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

rows = list(csv.DictReader(io.open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig")))
chain_of = {r["case_id"]: r["chain"] for r in rows if r["case_id"] in set(SC)}
CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    if not str(r.get("在86判分", "")).strip().isdigit() or int(str(r["在86判分"]).strip()) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in set(SC)]
    if ids:
        CHAINS[r["链ID"]] = ids
FOLD_OF = {c: fid for fid, ids in CHAINS.items() for c in ids}


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

# v14r5 与 v17 输出
B = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
BASE = {c: [str(x) for x in (B[c].get("主穴", []) or [])] for c in SC}
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


def apply_rule(base, restrict):
    """按组顺序迭代组合：c 的输出 = 其紧邻上一诊的输出（若启用的复诊案）。"""
    P = json.loads(json.dumps(base))
    fired = []
    for g, ids in GROUPS.items():
        for i in range(1, len(ids)):
            c, p = ids[i], ids[i - 1]
            if c in restrict:
                P[c] = list(P[p])
                fired.append(c)
    return P, fired


ALL_FU = [ids[i] for ids in GROUPS.values() for i in range(1, len(ids))]
CHAIN_FU = [c for c in ALL_FU if chain_of.get(c, "").startswith("followup_")]
PREV = {ids[i]: ids[i - 1] for ids in GROUPS.values() for i in range(1, len(ids))}
LEGIT_FU = [c for c in ALL_FU if FOLD_OF.get(c) != FOLD_OF.get(PREV[c])]

OUT = []
OUT.append("复诊案（组内有更早案）=%d；链内复诊=%d；上次落别折（合法）=%d：%s"
           % (len(ALL_FU), len(CHAIN_FU), len(LEGIT_FU), "、".join(sorted(LEGIT_FU))))
OUT.append("")
OUT.append("v14r5 基线          : %s" % (agg(BASE, SC),))
OUT.append("v17  现行技能       : %s" % (agg(V17, SC),))
for name, restrict in (("D1 全部复诊", ALL_FU), ("D2 仅链内复诊", CHAIN_FU), ("D3 仅合法子集", LEGIT_FU)):
    P, fired = apply_rule(V17, set(restrict))
    rb = agg(V17, SC)
    r = agg(P, SC)
    OUT.append("%-16s : %s  ΔTP%+d ΔFP%+d ΔFN%+d ΔF1 %+.4f  (触发 %d 案)"
               % (name, r, r[0] - rb[0], r[1] - rb[1], r[2] - rb[2], r[3] - rb[3], len(fired)))
OUT.append("")
OUT.append("--- 逐案（复诊案：v17 基线 vs 复诊延续输出）---")
P1, _ = apply_rule(V17, set(ALL_FU))
for c in sorted(ALL_FU, key=lambda x: (group_of(x), int(x.split("_")[1]))):
    OUT.append("%-8s 组%-4s v17 %.3f → 延续 %.3f  (Δ%+.3f)"
               % (c, group_of(c), f1(V17[c], GOLD[c]), f1(P1[c], GOLD[c]), f1(P1[c], GOLD[c]) - f1(V17[c], GOLD[c])))
OUT.append("")
OUT.append("--- 副作用（TP 下降案）---")
side = [c for c in SC if f1(P1[c], GOLD[c]) < f1(V17[c], GOLD[c])]
OUT.append("有 %d 案：%s" % (len(side), "、".join("%s(%.2f→%.2f)" % (c, f1(V17[c], GOLD[c]), f1(P1[c], GOLD[c])) for c in side) or "0"))

# ---- D4/D5：条件化（原文载「同前穴/同前/服前方後…」才延续）----
import re as _re
res = {}
MARK = _re.compile(r"同前穴|針同前|同前|同穴|作療程中|服前方後|服前方后|如前|原方")
MARK_FU = [c for c in ALL_FU if MARK.search(SYM[c])]
OUT.append("")
OUT.append("原文含延续标记('同前穴/同前/服前方後…')的复诊案=%d：%s" % (len(MARK_FU), "、".join(sorted(MARK_FU))))
for name, restrict in (("D4 标记条件(全部复诊∩含标记)", set(MARK_FU)),
                       ("D5 标记条件(链内∩含标记)", set(MARK_FU) & set(CHAIN_FU))):
    P, fired = apply_rule(V17, restrict)
    rb = agg(V17, SC)
    r = agg(P, SC)
    sd = [c for c in SC if f1(P[c], GOLD[c]) < f1(V17[c], GOLD[c])]
    OUT.append("%-28s : %s  ΔTP%+d ΔFP%+d ΔF1 %+.4f (触发 %d 案, 副作用 %d 案: %s)"
               % (name, r, r[0] - rb[0], r[1] - rb[1], r[3] - rb[3], len(fired), len(sd),
                  "、".join(sd) or "0"))
    res[name[:2]] = {"agg": r, "fired": fired, "side": sd}

io.open(os.path.join(HERE, "PN_d_followup_skill.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
for name, restrict in (("D1", ALL_FU), ("D2", CHAIN_FU), ("D3", LEGIT_FU)):
    P, fired = apply_rule(V17, set(restrict))
    res[name] = {"agg": agg(P, SC), "fired": fired}
json.dump({"v14r5": agg(BASE, SC), "v17": agg(V17, SC), "ALL_FU": ALL_FU, "CHAIN_FU": CHAIN_FU,
           "LEGIT_FU": LEGIT_FU, "results": res},
          io.open(os.path.join(HERE, "PN_d_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote PN_d_followup_skill.txt / PN_d_summary.json")

# 规则真相源（v18）
P4, F4 = apply_rule(V17, set(MARK_FU))
rule = {
    "规则": "R-FU 复诊延续层（v18）",
    "触发": "本案为某患者复诊（下表分组内存在更早案）且本案原文含『延续标记』",
    "延续标记正则": MARK.pattern,
    "组合语义": "组内按案号升序逐一：含标记者 主穴 := 上一案的（已组合）主穴；不含标记者维持原四层组方",
    "患者分组(仅多案组)": {g: ids for g, ids in GROUPS.items() if len(ids) > 1},
    "预期_全86": list(agg(P4, SC)),
    "触发案": F4,
    "副作用案": [c for c in SC if f1(P4[c], GOLD[c]) < f1(V17[c], GOLD[c])],
    "边界": "机制级：需上游提供『上一诊主穴』；无上游通道时不触发（退化为四层组方）",
}
json.dump(rule, io.open(os.path.join(HERE, "PN_followup_rule.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote PN_followup_rule.json  expected_86=%s fired=%d" % (list(agg(P4, SC)), len(F4)))
