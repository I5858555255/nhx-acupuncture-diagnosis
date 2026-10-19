#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-B 全量评分（LLM 开放重提炼 · 全 66 折 / 全 86 案）。

用唯一正式评分器口径（canonical_scorer.normalize_units + 宏平均 F1）复算：
  LLM 全量 vs v14r5 基线 vs v17 vs v18。
输出逐折表 + 全86聚合 + 泄漏登记（HARD-04）。
只读；写 PN_all_score.txt / PN_all_summary.json。
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
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")
PN = HERE
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}

FOLDS = json.load(io.open(os.path.join(PN, "PN_folds_all.json"), encoding="utf-8"))
ALLF = sorted(FOLDS["done"] + FOLDS["todo"])


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
# v18
import re  # noqa: E402
rule = json.load(io.open(os.path.join(PN, "PN_followup_rule.json"), encoding="utf-8"))
MARK = re.compile(rule["延续标记正则"])
V18 = json.loads(json.dumps(V17))
for g, ids in rule["患者分组(仅多案组)"].items():
    ids = sorted(ids, key=lambda x: (int(x.split("_")[1]), x))
    for i in range(1, len(ids)):
        if MARK.search(SYM[ids[i]]):
            V18[ids[i]] = list(V18[ids[i - 1]])

LEAK = {
    "303_01": "首跑 grep 误命中 SKILL.md（透露含「列缺」）；单穴视为可能污染",
    "221_01": "首跑 grep 误命中 SKILL.md/变更记录行（子代理称未据以增删）",
    "160_01": "首跑 grep 误命中 SKILL.md/变更记录行（子代理称未据以增删）",
    "156_06": "grep 误命中 SKILL.md+变更记录_SF10_v11/v12（含 M2-06 利水组、156_06 被列为触发案）",
    "194_01": "grep 误命中 SKILL.md+变更记录_SF10_v11~v14（含「手腕桡侧痛→肺原太渊」等既有规则）",
    "1_01": "grep 误命中 SKILL.md 第82行+变更记录_SF10_v12 第46行",
    "213_01": "grep 误命中 SKILL.md+变更记录_SF10_v11/v12+知识条目对照审计（含 M2-12 整组等）",
    "216_04": "grep 误命中 SKILL.md 第108行（局部专科穴/透刺惯例段）；本折已因此重置重跑，此为**重跑后**申报",
    "208_01": "grep 误命中非白名单文件 `样例-髋酸胆经虚证-米粒灸鸡眼.md`（非禁读但非白名单）",
    "64_01": "grep 误命中 references/典型案例示范集.md 3 行（案60标题/辨证行、案117标题；与本案 64_01 无关，声明已忽略）",
    "107_01": "首跑误触 references/典型案例示范集.md（含案107答案）→ **已弃用并重置重跑**；重跑声明未触碰",
    "117_01": "首跑误触 references/典型案例示范集.md（含案117答案）→ **已弃用并重置重跑**；重跑声明未触碰",
}

OUT = []
ids_all = []
per = []
for fid in ALLF:
    ids = json.load(io.open(os.path.join(PN, "packets", fid, "留出案输入.json"), encoding="utf-8"))["case_ids"]
    raw = json.load(io.open(os.path.join(PN, "packets", fid, "留出案预测.json"), encoding="utf-8"))
    ids_all += ids
    llm = {c: raw.get(c, []) for c in ids}
    rl, rb, rv, r18 = agg(llm, ids), agg(BASE, ids), agg(V17, ids), agg(V18, ids)
    per.append((fid, len(ids), rl[3], rb[3], rv[3], r18[3]))
    OUT.append("%-14s n=%-2d | LLM %3d/%3d/%3d F1 %.4f | v14r5 F1 %.4f | v17 %.4f | v18 %.4f | ΔLLM-v14r5 %+.4f"
               % (fid, len(ids), rl[0], rl[1], rl[2], rl[3], rb[3], rv[3], r18[3], rl[3] - rb[3]))
    for c in ids:
        if c in LEAK:
            OUT.append("      [WARN] 泄漏登记 %s：%s" % (c, LEAK[c]))

LLM_ALL = {}
for fid in ALLF:
    LLM_ALL.update(json.load(io.open(os.path.join(PN, "packets", fid, "留出案预测.json"), encoding="utf-8")))

r_llm = agg(LLM_ALL, ids_all)
r_base = agg(BASE, ids_all)
r_v17 = agg(V17, ids_all)
r_v18 = agg(V18, ids_all)

H = []
H.append("== P-N-B 全量评分（LLM 开放重提炼）==")
H.append("折数=%d ；覆盖案=%d/%d (%.0f%%)" % (len(ALLF), len(ids_all), len(SC), 100.0 * len(ids_all) / len(SC)))
H.append("")
H.extend(OUT)
H.append("")
H.append("--- 全 %d 案聚合 ---" % len(ids_all))
H.append("LLM 开放重提炼 : TP%d/FP%d/FN%d  F1 %.4f" % r_llm)
H.append("基线 v14r5      : TP%d/FP%d/FN%d  F1 %.4f" % r_base)
H.append("现行 v17        : TP%d/FP%d/FN%d  F1 %.4f" % r_v17)
H.append("现行 v18(+R-FU) : TP%d/FP%d/FN%d  F1 %.4f" % r_v18)
H.append("ΔF1(LLM-v14r5) = %+.4f  |  ΔF1(LLM-v17) = %+.4f  |  ΔF1(LLM-v18) = %+.4f"
         % (r_llm[3] - r_base[3], r_llm[3] - r_v17[3], r_llm[3] - r_v18[3]))
H.append("")
H.append("泄漏登记案 %d 个：%s" % (len([c for c in ids_all if c in LEAK]), "、".join(sorted([c for c in ids_all if c in LEAK]))))

io.open(os.path.join(PN, "PN_all_score.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(H) + "\n")
json.dump({"folds": len(ALLF), "cases": len(ids_all), "coverage_pct": round(100.0 * len(ids_all) / len(SC), 1),
           "aggregate": {"LLM": r_llm, "v14r5": r_base, "v17": r_v17, "v18": r_v18},
           "per_fold": [{"fold": f, "n": n, "llm": a, "v14r5": b, "v17": c, "v18": d} for f, n, a, b, c, d in per],
           "leak_register": LEAK},
          io.open(os.path.join(PN, "PN_all_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n".join(H[-9:]))
print("wrote PN_all_score.txt / PN_all_summary.json")
