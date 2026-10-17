#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-L：M9 式按链留出（leave-one-chain-out）复核 —— 候选A（八脉分流）与候选B-v2（R2 分期）。

沿用既有 M9/M6-D 范式（固定规则版逐链留出），并追加两组本批特有检验：
  1) 逐链 Δ 分解：受益是否集中于少数链？有无"净有害链"？
  2) 派生来源（in-sample / out-of-sample）对照：词表从哪些链的数据得来，与受益链是否重合。
  3) 严格 LOCO：对**观察驱动**的关键词修正（221_01 核定），把留出链 S_221_01 的观察移除后重评。

诚实声明（同 M6-D）：**每折重新提炼规则的完整盲法重跑未执行**；
本报告为"固定规则版逐链留出性能"，不是泛化上界。唯一正式评分器，只读输入。
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
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")


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
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}
SCSET = set(SC)

# ---- 链分组（M9-链分组表.csv）----
CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    v = str(r.get("在86判分", "")).strip()
    if not v.isdigit() or int(v) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in SCSET]
    if ids:
        CHAINS[r["链ID"]] = ids
CH_OF = {c: k for k, v in CHAINS.items() for c in v}
assert len(CH_OF) == len(SC), "链映射未全覆盖 86 案: %d vs %d" % (len(CH_OF), len(SC))

BASE = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))

CAND = [
    ("候选A·八脉分流（含 221_01 核定）", os.path.join(PC, "_blind93_pcZ_A_results.json")),
    ("候选A·八脉分流（**无核定**＝严格 LOCO@S_221_01）", os.path.join(PC, "_blind93_pcC1b_results.json")),
    ("候选B-v2·R2分期（精简词表）", os.path.join(PC, "_blind93_pcZ_B-v2_results.json")),
    ("组合 候选A + 候选B-v2", os.path.join(PC, "_blind93_pcZ_A+B-v2（规则级组合）_results.json")),
]

# 词表派生来源（人工登记，供 in/out-of-sample 对照）
PROVENANCE = {
    "候选A·八脉分流（含 221_01 核定）": {
        "派生链": ["S_221_01"], "依据": "指南6.4（原书，外部）+ 221_01 观察核定（链内）",
        "受益链": ["followup_146", "S_213_01", "followup_216", "S_216_05", "S_318_01", "S_61_01", "S_62_01"]},
    "候选A·八脉分流（**无核定**＝严格 LOCO@S_221_01）": {
        "派生链": [], "依据": "指南6.4（原书，外部）", "受益链": []},
    "候选B-v2·R2分期（精简词表）": {
        "派生链": ["S_140_01", "S_141_01", "S_142_01", "S_143_01", "S_144_01", "S_145_01", "followup_146"],
        "依据": "140 链家族 9 案输入（全为链内观察）", "受益链": ["S_144_01", "S_145_01", "followup_146"]},
    "组合 候选A + 候选B-v2": {"派生链": ["S_221_01", "S_140_01", "S_141_01", "S_142_01", "S_143_01",
                                       "S_144_01", "S_145_01", "followup_146"], "依据": "见上两行", "受益链": []},
}


def per_case(pred):
    out = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        g = GOLD[c]
        t = len(P & g)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        out[c] = dict(tp=t, fp=len(P - g), fn=len(g - P),
                      f1=(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0))
    return out


PB = per_case(BASE)

rows = []
summary = {"chains_total": len(CHAINS), "cases": len(SC), "candidates": {}}
for tag, path in CAND:
    PCASE = per_case(json.load(io.open(path, encoding="utf-8")))
    changed_chains = []
    for cid, cases in sorted(CHAINS.items()):
        dtp = sum(PCASE[c]["tp"] - PB[c]["tp"] for c in cases)
        dfp = sum(PCASE[c]["fp"] - PB[c]["fp"] for c in cases)
        dfn = sum(PCASE[c]["fn"] - PB[c]["fn"] for c in cases)
        f1b = statistics.mean([PB[c]["f1"] for c in cases])
        f1r = statistics.mean([PCASE[c]["f1"] for c in cases])
        stat = "改" if (dtp or dfp or dfn) else "不变"
        rows.append(dict(候选=tag, 链ID=cid, 案号=" ".join(cases), 案数=len(cases), 状态=stat,
                         ΔTP=dtp, ΔFP=dfp, ΔFN=dfn, F1_base=round(f1b, 4), F1_run=round(f1r, 4),
                         ΔF1=round(f1r - f1b, 4)))
        if stat == "改":
            changed_chains.append(dict(链ID=cid, 案号=cases, ΔTP=dtp, ΔFP=dfp, ΔF1=round(f1r - f1b, 4)))
    # 全量 + 分层
    def blk(cases):
        return dict(TP=sum(PCASE[c]["tp"] for c in cases), FP=sum(PCASE[c]["fp"] for c in cases),
                    FN=sum(PCASE[c]["fn"] for c in cases),
                    F1=round(statistics.mean([PCASE[c]["f1"] for c in cases]), 4))
    allr = blk(SC)
    allb = dict(TP=sum(PB[c]["tp"] for c in SC), FP=sum(PB[c]["fp"] for c in SC),
                FN=sum(PB[c]["fn"] for c in SC), F1=round(statistics.mean([PB[c]["f1"] for c in SC]), 4))
    harm = [x for x in changed_chains if x["ΔTP"] < 0 or x["ΔFP"] > 0]
    prov = PROVENANCE.get(tag, {})
    benef = sorted(set(x["链ID"] for x in changed_chains if x["ΔF1"] > 0)) or prov.get("受益链", [])
    oos = [k for k in benef if k not in prov.get("派生链", [])]
    summary["candidates"][tag] = {
        "sha256_src": path, "changed_chains": changed_chains, "changed_chain_n": len(changed_chains),
        "harm_chains": harm, "base": allb, "run": allr,
        "dTP": allr["TP"] - allb["TP"], "dFP": allr["FP"] - allb["FP"], "dF1": round(allr["F1"] - allb["F1"], 4),
        "derive_chains": prov.get("派生链", []), "benefit_chains": benef,
        "out_of_sample_chains": oos, "oos_ratio": "%d/%d" % (len(oos), len(benef)) if benef else "n/a",
    }
    print("%s | 改动链 %d | 有害链 %d | ΔTP %+d ΔFP %+d ΔF1 %+.4f | 派生链 %s | 受益链 %s | OOS %s"
          % (tag, len(changed_chains), len(harm), allr["TP"] - allb["TP"], allr["FP"] - allb["FP"],
             allr["F1"] - allb["F1"], prov.get("派生链", []), benef, summary["candidates"][tag]["oos_ratio"]))

with io.open(os.path.join(HERE, "P-L_逐链明细.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["候选", "链ID", "案号", "案数", "状态", "ΔTP", "ΔFP", "ΔFN",
                                      "F1_base", "F1_run", "ΔF1"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

# ---- 逐案敏感性（候选B：受益仅 3 案）----
sens = {}
b = list(json.load(io.open(os.path.join(PC, "_blind93_pcZ_B-v2_results.json"), encoding="utf-8")).items())
PBASE = per_case(BASE)
PRUN = per_case({k: v for k, v in b})
for c in ["144_01", "145_01", "148_01"]:
    d1 = round((PRUN[c]["f1"] - PBASE[c]["f1"]) / len(SC), 6)
    sens[c] = {"ΔF1_全量贡献": d1, "链": CH_OF.get(c)}
summary["B_逐案敏感性"] = sens

io.open(os.path.join(HERE, "P-L_判分汇总.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=2))
print("wrote P-L_逐链明细.csv / P-L_判分汇总.json")
sys.exit(0)
