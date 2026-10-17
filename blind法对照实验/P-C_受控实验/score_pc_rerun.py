#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-C 复算：对 v14r5（基线）与 P-C 两套受控 patch 重跑集分别评分（唯一正式评分器），
产出分层对比、逐案差异、自检，写入本目录。只读输入。

两套重跑（见 apply_pc_patch.py）：
  A `_blind93_pcC23_results.json`       —— 分期按 C_残余归因登记的原案对照
  B `_blind93_pcC23_indep_results.json` —— 分期按独立盲法执行的判定
评分实现：benchmark_v2/canonical_scorer.py（唯一正式实现，未改指标/分母）。
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


def find_experiment_root(root):
    for name in sorted(os.listdir(root)):
        cand = os.path.join(root, name)
        if os.path.isfile(os.path.join(cand, "benchmark_v2", "canonical_scorer.py")):
            return cand
    return None


EXP = find_experiment_root(ROOT)
BENCH = os.path.join(EXP, "benchmark_v2")
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")

sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
CASE_IDS = gold["case_ids"]
SC = [c for c in CASE_IDS if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}

EXCLUDE = set(r["case_id"] for r in csv.DictReader(
    io.open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
M1 = set(r["case_id"] for r in csv.DictReader(
    io.open(os.path.join(M5, "A_迁移核验", "迁移核验逐案表.csv"), encoding="utf-8-sig")) if r["M1审计案"] == "Y")
VT = {r["case_id"]: str(r.get("visit_type", "")) for r in csv.DictReader(
    io.open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig"))}
CHAIN = {}
for r in csv.DictReader(io.open(os.path.join(M5, "E_分组验证", "分组交叉验证表.csv"), encoding="utf-8-sig")):
    for x in (r["案号"] or "").split(";"):
        if x:
            CHAIN[x] = r["患者链"]

BASE = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
RUNS = [("A·登记分期", os.path.join(HERE, "_blind93_pcC23_results.json")),
        ("B·独立判定", os.path.join(HERE, "_blind93_pcC23_indep_results.json"))]

CORE = [c for c in SC if c not in EXCLUDE]
FU = [c for c in SC if VT.get(c, "").startswith("复诊")]
FS = [c for c in SC if c not in FU]
LAYERS = [("全量86", SC), ("核心集64", CORE), ("M1_28", [c for c in SC if c in M1]),
          ("未M1_58", [c for c in SC if c not in M1]), ("复诊", FU), ("首诊", FS)]


def evalset(pred):
    per = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        G2 = GOLD[c]
        t, f = len(P & G2), len(P - G2)
        rc = t / len(G2) if G2 else 0.0
        pr = t / len(P) if P else 0.0
        f1 = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
        ja = t / len(P | G2) if (P | G2) else 0.0
        per[c] = dict(P=P, tp=t, fp=f, fn=len(G2 - P), recall=rc, prec=pr, f1=f1, jac=ja)
    return per


def blk(per, cids):
    return dict(TP=sum(per[c]["tp"] for c in cids), FP=sum(per[c]["fp"] for c in cids),
                FN=sum(per[c]["fn"] for c in cids),
                R=round(statistics.mean([per[c]["recall"] for c in cids]), 4),
                P=round(statistics.mean([per[c]["prec"] for c in cids]), 4),
                F1=round(statistics.mean([per[c]["f1"] for c in cids]), 4),
                Jac=round(statistics.mean([per[c]["jac"] for c in cids]), 4))


PER_B = evalset(BASE)
ref = json.load(io.open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))["全量86"]["v14r5"]
b86 = blk(PER_B, SC)
selfcheck = (b86["TP"] == ref["TP"] and b86["FP"] == ref["FP"] and b86["FN"] == ref["FN"]
             and abs(b86["F1"] - ref["F1"]) < 1e-9 and abs(b86["Jac"] - ref["Jac"]) < 1e-9)

summary = {"selfcheck": selfcheck, "runs": {}}
lines = ["# P-C 复算结果（v14r5 基线 vs C2+C3 受控 patch 重跑）", ""]
lines.append("- 自检（基线 vs 官方 `判分汇总v14r5.json`）：**%s**" % ("PASS" if selfcheck else "FAIL"))
lines.append("- 评分：`benchmark_v2/canonical_scorer.py`（唯一正式实现，未改指标/分母）")
lines.append("- A＝分期取 `C_残余归因` 登记的原案对照；B＝分期取**独立盲法执行**的判定（仅凭输入+规则文本）")
lines.append("")

for tag, path in RUNS:
    RUN = json.load(io.open(path, encoding="utf-8"))
    PER_R = evalset(RUN)
    rows = []
    for name, cids in LAYERS:
        b, r = blk(PER_B, cids), blk(PER_R, cids)
        rows.append(dict(分层=name, 案数=len(cids), TP_b=b["TP"], TP_r=r["TP"], FP_b=b["FP"], FP_r=r["FP"],
                         FN_b=b["FN"], FN_r=r["FN"], F1_b=b["F1"], F1_r=r["F1"],
                         F1_d=round(r["F1"] - b["F1"], 4), Jac_b=b["Jac"], Jac_r=r["Jac"],
                         Jac_d=round(r["Jac"] - b["Jac"], 4)))
    per_case = []
    for c in SC:
        db, df, dn = PER_R[c]["tp"] - PER_B[c]["tp"], PER_R[c]["fp"] - PER_B[c]["fp"], PER_R[c]["fn"] - PER_B[c]["fn"]
        if db or df or dn:
            per_case.append(dict(case_id=c, chain=CHAIN.get(c, ""), 访次="复诊" if c in FU else "首诊",
                                 TP_d=db, FP_d=df, FN_d=dn, F1_b=round(PER_B[c]["f1"], 4),
                                 F1_r=round(PER_R[c]["f1"], 4),
                                 added="+".join(sorted(PER_R[c]["P"] - PER_B[c]["P"])) or "-",
                                 removed="+".join(sorted(PER_B[c]["P"] - PER_R[c]["P"])) or "-"))
    summary["runs"][tag] = {"layers": rows, "per_case": per_case}

    lines.append("## 重跑 %s" % tag)
    lines.append("")
    lines.append("| 分层 | 案数 | TP 基线→重跑 | FP 基线→重跑 | FN 基线→重跑 | F1 基线→重跑 (Δ) | Jac 基线→重跑 (Δ) |")
    lines.append("|---|---:|---|---|---|---|---|")
    for r in rows:
        lines.append("| %s | %d | %d→%d | %d→%d | %d→%d | %.4f→%.4f (%+.4f) | %.4f→%.4f (%+.4f) |"
                     % (r["分层"], r["案数"], r["TP_b"], r["TP_r"], r["FP_b"], r["FP_r"], r["FN_b"], r["FN_r"],
                        r["F1_b"], r["F1_r"], r["F1_d"], r["Jac_b"], r["Jac_r"], r["Jac_d"]))
    lines.append("")
    lines.append("| 案号 | 链 | 访次 | ΔTP | ΔFP | ΔFN | F1 基线→重跑 | 加穴 | 删穴 |")
    lines.append("|---|---|---|---:|---:|---:|---|---|---|")
    for p in per_case:
        lines.append("| %s | %s | %s | %+d | %+d | %+d | %.4f→%.4f | %s | %s |"
                     % (p["case_id"], p["chain"], p["访次"], p["TP_d"], p["FP_d"], p["FN_d"],
                        p["F1_b"], p["F1_r"], p["added"], p["removed"]))
    lines.append("")

with io.open(os.path.join(HERE, "P-C_判分汇总.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=2)
with io.open(os.path.join(HERE, "P-C_复算结果.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print("self-check:", "PASS" if selfcheck else "FAIL")
for tag, _ in RUNS:
    r86 = [x for x in summary["runs"][tag]["layers"] if x["分层"] == "全量86"][0]
    r64 = [x for x in summary["runs"][tag]["layers"] if x["分层"] == "核心集64"][0]
    print("%s  全量86: TP%d->%d FP%d->%d F1 %.4f->%.4f (%+.4f) | 核心64 F1 %+.4f"
          % (tag, r86["TP_b"], r86["TP_r"], r86["FP_b"], r86["FP_r"], r86["F1_b"], r86["F1_r"],
             r86["F1_d"], r64["F1_d"]))
sys.exit(0 if selfcheck else 1)
