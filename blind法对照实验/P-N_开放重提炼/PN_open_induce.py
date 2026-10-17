#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-A：开放式每折从零重提炼（机械归纳，全 66 折，真 LOCO）。

与既有方法的区别：
  - M9 = 固定规则池 + 逐折**选择**；P-M = 固定假设空间（八脉/R2）的逐折**参数重提炼**；
  - **本脚本 = 开放假设空间**：不使用任何人工规则族、不使用 M5-C 归因池；
    每折仅用**训练链**的「症状文本 → gold 主穴」配对，从零归纳预测器，再预测留出链。

两个从零归纳器（均只读训练链）：
  L1 k-NN：症状字符 2-gram 余弦相似 → 取最近 k 训练案的 gold，频次≥f 者入主穴；
  L2 关联规则：对每个候选穴 u（训练 gold 频次≥3）与每个症状 n-gram t，
     取 支持度(t)≥s、置信度(u|t)≥c 的 (u,t)；留出案命中任一 t 则预测 u。
网格：k∈{3,5,10} × f∈{0.3,0.5,0.7}；s∈{3,5,8} × c∈{0.4,0.6,0.8}。

只读输入；只写本目录；唯一正式评分器 canonical（宏平均 F1）。
"""
import csv
import io
import json
import math
import os
import pickle
import statistics
import sys
from collections import Counter

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
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}
EXCLUDE = set(r["case_id"] for r in csv.DictReader(io.open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
CORE = [c for c in SC if c not in EXCLUDE]
CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    v = str(r.get("在86判分", "")).strip()
    if not v.isdigit() or int(v) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in set(SC)]
    if ids:
        CHAINS[r["链ID"]] = ids
assert len({c for v in CHAINS.values() for c in v}) == len(SC)


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


def ngrams(t, n):
    t = "".join(ch for ch in t if ch.strip())
    return set(t[i:i + n] for i in range(len(t) - n + 1))


GRAM = {c: ngrams(SYM[c], 2) for c in SC}


def blk(pred):
    tp = fp = fn = 0
    f1s = []
    for c in SC:
        P = set(normalize_units(pred.get(c, [])))
        g = GOLD[c]
        t = len(P & g)
        tp += t
        fp += len(P - g)
        fn += len(g - P)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        f1s.append(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0)
    return tp, fp, fn, round(statistics.mean(f1s), 4)


def blk_ids(pred, ids):
    tp = fp = fn = 0
    f1s = []
    for c in ids:
        P = set(normalize_units(pred.get(c, [])))
        g = GOLD[c]
        t = len(P & g)
        tp += t
        fp += len(P - g)
        fn += len(g - P)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        f1s.append(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0)
    return tp, fp, fn, round(statistics.mean(f1s), 4)


BASE = {c: set(normalize_units(json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))[c].get("主穴", []))) for c in SC}
print("基线 v14r5:", blk(BASE))

OUT = []


# ---------- L1: k-NN ----------
def knn_loco(k, f):
    pred = {}
    for hid, cases in CHAINS.items():
        train = [c for c in SC if c not in set(cases)]
        for h in cases:
            g = GRAM[h]
            sims = []
            for t in train:
                gt = GRAM[t]
                inter = len(g & gt)
                if not inter:
                    continue
                sims.append((inter / math.sqrt(max(len(g), 1) * max(len(gt), 1)), t))
            sims.sort(reverse=True)
            nb = [t for _, t in sims[:k]]
            cnt = Counter()
            for t in nb:
                for u in GOLD[t]:
                    cnt[u] += 1
            need = max(1, int(math.ceil(f * len(nb))))
            pred[h] = [u for u, n in cnt.items() if n >= need]
    return pred


print("\n== L1 k-NN（症状 2-gram 余弦，仅训练链） ==")
best = None
for k in (3, 5, 10):
    for f in (0.3, 0.5, 0.7):
        p = knn_loco(k, f)
        r = blk(p)
        r64 = blk_ids(p, CORE)
        line = "  k=%2d f=%.1f | 86 TP%d/FP%d/FN%d/F1 %.4f | 64 F1 %.4f" % (k, f, r[0], r[1], r[2], r[3], r64[3])
        print(line)
        OUT.append(line)
        if best is None or r[3] > best[1][3]:
            best = (("knn k=%d f=%.1f" % (k, f)), r)
print("  最佳 L1：%s → F1 %.4f（基线 %.4f，差 %+.4f）" % (best[0], best[1][3], blk(BASE)[3], best[1][3] - blk(BASE)[3]))
OUT.append("最佳 L1：%s → F1 %.4f（基线 %.4f）" % (best[0], best[1][3], blk(BASE)[3]))


# ---------- L2: 关联规则 ----------
def rule_loco(sup, conf):
    pred = {}
    for hid, cases in CHAINS.items():
        train = [c for c in SC if c not in set(cases)]
        # 候选穴
        gcnt = Counter()
        for t in train:
            for u in GOLD[t]:
                gcnt[u] += 1
        cand = [u for u, n in gcnt.items() if n >= 3]
        # 症状 token → 出现训练案集合
        t2c = {}
        for t in train:
            for g in GRAM[t]:
                t2c.setdefault(g, set()).add(t)
        # 对每个候选穴：哪些 token 的 置信度≥conf 且 支持度≥sup
        u2tok = {}
        for u in cand:
            toks = set()
            for g, cs in t2c.items():
                if len(cs) < sup:
                    continue
                hit = len([t for t in cs if u in GOLD[t]])
                if hit / len(cs) >= conf:
                    toks.add(g)
            u2tok[u] = toks
        for h in cases:
            gh = GRAM[h]
            pts = [u for u, toks in u2tok.items() if toks & gh]
            pred[h] = pts
    return pred


print("\n== L2 关联规则（(u,t) 支持/置信，仅训练链） ==")
best2 = None
for s in (3, 5, 8):
    for c in (0.4, 0.6, 0.8):
        p = rule_loco(s, c)
        r = blk(p)
        r64 = blk_ids(p, CORE)
        line = "  sup=%d conf=%.1f | 86 TP%d/FP%d/FN%d/F1 %.4f | 64 F1 %.4f" % (s, c, r[0], r[1], r[2], r[3], r64[3])
        print(line)
        OUT.append(line)
        if best2 is None or r[3] > best2[1][3]:
            best2 = (("rule sup=%d conf=%.1f" % (s, c)), r, p)
print("  最佳 L2：%s → F1 %.4f（基线 %.4f，差 %+.4f）" % (best2[0], best2[1][3], blk(BASE)[3], best2[1][3] - blk(BASE)[3]))
OUT.append("最佳 L2：%s → F1 %.4f（基线 %.4f）" % (best2[0], best2[1][3], blk(BASE)[3]))

# ---------- 参考：v17/出厂表（现行技能）与 M9 口径 ----------
print("\n== 参考（非本脚本产出，来自既有冻结产物） ==")
OUT.append("参考：v14r5 0.5185；v17(现行技能口径) 0.5233；M9 固定池+逐折选择 0.5207")

# ---------- 逐链对比（最佳 L1/L2 vs 基线） ----------
print("\n== 逐链（最佳 L1/L2 相对基线的链级 F1 差） ==")
OUT.append("\n逐链（最佳 L2 相对基线）：")
pl2 = best2[2]
for hid in CHAINS:
    ids = CHAINS[hid]
    d = blk_ids(pl2, ids)[3] - blk_ids(BASE, ids)[3]
    OUT.append("  %-18s n=%-2d ΔF1_L2 %+.4f" % (hid, len(ids), d))

SUMMARY = {"baseline_86": blk(BASE), "best_knn": {"cfg": best[0], "r86": best[1]},
           "best_rule": {"cfg": best2[0], "r86": best2[1]}}
json.dump(SUMMARY, io.open(os.path.join(HERE, "PN_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
io.open(os.path.join(HERE, "PN_result.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(OUT) + "\n")
print("\nwrote PN_summary.json / PN_result.txt")
