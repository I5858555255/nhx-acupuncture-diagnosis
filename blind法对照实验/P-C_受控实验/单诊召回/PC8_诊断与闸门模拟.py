#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PC8/PC9：R-FU 适用性闸门模拟（负结果）+ 单诊失分结构诊断。

只读：gold pkl、A-1 回传 runs、A-2 回传 runs、PN_followup_rule.json、技能资料目录。
只写：同目录 `PC8_结果.txt`。

用法：python PC8_诊断与闸门模拟.py
"""
import io
import json
import os
import pickle
import statistics
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

A1D = r"D:\_blind_bundle_out\blind_v19_bundle\runs"
A2D = os.path.join(os.environ["TEMP"], "opencode", "runs_A2")
RULE = os.path.join(ROOT, "blind法对照实验", "P-N_开放重提炼", "PN_followup_rule.json")
SKILL = os.path.join(ROOT, "doubao-acupuncture-diagnosis")

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
SC = [c for c in gold["case_ids"] if len(gold["results"][c]["gold_members"]) > 0]
G = {c: set(normalize_units(gold["results"][c]["gold_members"])) for c in SC}

rule = json.load(io.open(RULE, encoding="utf-8"))
CHAIN = {}
for g, ids in rule["患者分组(仅多案组)"].items():
    for c in ids:
        CHAIN[c] = g

PAIR = sorted(f[:-5] for f in os.listdir(A2D) if f.endswith(".json"))
A1 = {c: set(normalize_units(json.load(io.open(os.path.join(A1D, c + ".json"),
                                              encoding="utf-8"))["主穴"])) for c in SC}
A2 = {c: set(normalize_units(json.load(io.open(os.path.join(A2D, c + ".json"),
                                               encoding="utf-8"))["主穴"])) for c in PAIR}
SINGLE = [c for c in SC if c not in CHAIN]


def f1(p_, g):
    t = len(p_ & g)
    pr = t / len(p_) if p_ else 0.0
    rc = t / len(g) if g else 0.0
    return 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0


def jac(a, b):
    return len(a & b) / float(len(a | b)) if (a | b) else 0.0


def cov(u, f):
    return len(u & f) / float(len(u)) if u else 0.0


o = ["# PC8/PC9 结果", ""]
o.append("口径说明：全部数字基于 **A-1 回传**（86 案）与 **A-2 回传**（25 案配对）的盲法主穴，"
         "gold 取自 `_gold_results93v2.pkl`，评分口径与 `canonical_scorer` 一致。")
o.append("")
o.append("## A. C8 候选：R-FU 适用性闸门（模拟）")
o.append("")
o.append("记号：U＝上游（上一诊主穴）；F＝本案独立四层重建（A-2 输出）；G＝gold。")
o.append("")
base_u = statistics.mean([f1(A1[c], G[c]) for c in PAIR])
base_f = statistics.mean([f1(A2[c], G[c]) for c in PAIR])
oracle = statistics.mean([max(f1(A1[c], G[c]), f1(A2[c], G[c])) for c in PAIR])
o.append("| 方案 | F1（n=25） |")
o.append("|---|---|")
o.append("| G0 恒用上游（现状） | **%.4f** |" % base_u)
o.append("| G1 恒用四层（无上游） | **%.4f** |" % base_f)
o.append("| G5 完美闸门（逐案取优，不可实现） | **%.4f** ← 天花板 |" % oracle)
o.append("")
o.append("→ **天花板只有 `+%.4f`**（作用在 25/86 案上，折合整臂约 `+%.4f`）。"
         % (oracle - base_u, (oracle - base_u) * len(PAIR) / len(SC)))
o.append("")
o.append("### G2：上游穴数过少则回退（|U| ≤ k）")
o.append("")
o.append("| k | 回退案数 | F1 |")
o.append("|---|---|---|")
for k in range(0, 9):
    sel = [A2[c] if len(A1[c]) <= k else A1[c] for c in PAIR]
    n = sum(1 for c in PAIR if len(A1[c]) <= k)
    o.append("| %d | %d | %.4f |" % (k, n, statistics.mean([f1(s, G[c]) for s, c in zip(sel, PAIR)])))
o.append("")
o.append("### G3：U 与 F 的 Jaccard 低于阈值则回退")
o.append("")
o.append("| θ | 回退案数 | F1 |")
o.append("|---|---|---|")
for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    sel = [A2[c] if jac(A1[c], A2[c]) < th else A1[c] for c in PAIR]
    n = sum(1 for c in PAIR if jac(A1[c], A2[c]) < th)
    o.append("| %.1f | %d | %.4f |" % (th, n, statistics.mean([f1(s, G[c]) for s, c in zip(sel, PAIR)])))
o.append("")
o.append("### G4：F 对 U 的覆盖率低于阈值则回退（|U∩F|/|U| < θ）")
o.append("")
o.append("| θ | 回退案数 | F1 |")
o.append("|---|---|---|")
for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    sel = [A2[c] if cov(A1[c], A2[c]) < th else A1[c] for c in PAIR]
    n = sum(1 for c in PAIR if cov(A1[c], A2[c]) < th)
    o.append("| %.1f | %d | %.4f |" % (th, n, statistics.mean([f1(s, G[c]) for s, c in zip(sel, PAIR)])))
o.append("")
o.append("### 留一链交叉检验（LOCO，5 折）")
o.append("")
o.append("| 留出链 | G2 训练 k | G2 留出 | G4 训练 θ | G4 留出 | G0 | G1 |")
o.append("|---|---|---|---|---|---|---|")
g2h, g4h = [], []
GRID = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
for hg in sorted(set(CHAIN[c] for c in PAIR)):
    tr = [c for c in PAIR if CHAIN[c] != hg]
    te = [c for c in PAIR if CHAIN[c] == hg]
    bk = max(range(0, 9), key=lambda k: statistics.mean(
        [f1(A2[c] if len(A1[c]) <= k else A1[c], G[c]) for c in tr]))
    bt = max(GRID, key=lambda th: statistics.mean(
        [f1(A2[c] if cov(A1[c], A2[c]) < th else A1[c], G[c]) for c in tr]))
    v2 = statistics.mean([f1(A2[c] if len(A1[c]) <= bk else A1[c], G[c]) for c in te])
    v4 = statistics.mean([f1(A2[c] if cov(A1[c], A2[c]) < bt else A1[c], G[c]) for c in te])
    g2h.append(v2)
    g4h.append(v4)
    o.append("| %s (n=%d) | %d | %.4f | %.1f | %.4f | %.4f | %.4f |"
             % (hg, len(te), bk, v2, bt, v4,
                statistics.mean([f1(A1[c], G[c]) for c in te]),
                statistics.mean([f1(A2[c], G[c]) for c in te])))
o.append("")
o.append("**LOCO 平均：G2 `%.4f` / G4 `%.4f` / G0 `%.4f` / G1 `%.4f`**"
         % (statistics.mean(g2h), statistics.mean(g4h), base_u, base_f))
o.append("")
o.append("→ 两种闸门**在留出链上都不如「恒用上游」**。全量最优 `k=4`（0.8648）由 `156_05`（|U|=2）单点驱动，"
         "属事后阈值。**C8 结论：不推进。**")
o.append("")

o.append("## B. C9 候选：单诊 56 案失分结构")
o.append("")
o.append("- 单诊 n=%d，F1 = **%.4f**"
         % (len(SINGLE), statistics.mean([f1(A1[c], G[c]) for c in SINGLE])))
tp = sum(len(A1[c] & G[c]) for c in SINGLE)
fp = sum(len(A1[c] - G[c]) for c in SINGLE)
fn = sum(len(G[c] - A1[c]) for c in SINGLE)
o.append("- TP/FP/FN = **%d/%d/%d**，FN/FP = **%.2f**（漏取约为误取的 1.3 倍）" % (tp, fp, fn, fn / float(fp)))
o.append("- 平均 |P| = %.2f，平均 |G| = %.2f"
         % (statistics.mean([len(A1[c]) for c in SINGLE]),
            statistics.mean([len(G[c]) for c in SINGLE])))
o.append("- F1 < 0.2 的案：%d / %d" % (sum(1 for c in SINGLE if f1(A1[c], G[c]) < 0.2), len(SINGLE)))
o.append("")
o.append("### B1. 逐案「可回收空间」（逐案取最优，**不可实现**，仅判方向）")
o.append("")
o.append("| 操作 | 单诊 F1 | 相对现状 |")
o.append("|---|---|---|")
base = statistics.mean([f1(A1[c], G[c]) for c in SINGLE])
o.append("| 现状 | %.4f | — |" % base)
for k in (1, 2, 3):
    vals = []
    for c in SINGLE:
        p_ = set(A1[c])
        for _ in range(k):
            extra = p_ - G[c]
            if not extra:
                break
            p_ = p_ - {sorted(extra)[0]}
        vals.append(f1(p_, G[c]))
    o.append("| 去掉 %d 个误取穴 | %.4f | %+.4f |" % (k, statistics.mean(vals), statistics.mean(vals) - base))
for k in (1, 2, 3):
    vals = []
    for c in SINGLE:
        p_ = set(A1[c])
        for _ in range(k):
            miss = G[c] - p_
            if not miss:
                break
            p_ = p_ | {sorted(miss)[0]}
        vals.append(f1(p_, G[c]))
    o.append("| 补上 %d 个漏取穴 | %.4f | %+.4f |" % (k, statistics.mean(vals), statistics.mean(vals) - base))
o.append("")
o.append("→ **补穴每点值 `+0.114`，去穴每点值 `+0.030`**（约 3.8 倍）。召回是瓶颈，不是精度。")
o.append("")
o.append("### B2. 穴级对照（Top 18，按 gold 出现次数）")
o.append("")
gc, pc, hc = Counter(), Counter(), Counter()
for c in SINGLE:
    gc.update(G[c])
    pc.update(A1[c])
    hc.update(A1[c] & G[c])
o.append("| 穴 | gold | 盲法给出 | 命中 | 命中率 | 误取 |")
o.append("|---|---|---|---|---|---|")
for u, n in gc.most_common(18):
    o.append("| %s | %d | %d | %d | %.0f%% | %d |" % (u, n, pc[u], hc[u], 100.0 * hc[u] / n, pc[u] - hc[u]))
o.append("")
o.append("### B3. 系统性过度泛化（给出次数远高于 gold 次数）")
o.append("")
o.append("| 穴 | 盲法给出 | gold | 净误取 |")
o.append("|---|---|---|---|")
for u in ("太冲", "阳陵泉", "大陵", "太渊", "神门"):
    o.append("| %s | %d | %d | %d |" % (u, pc[u], gc[u], pc[u] - hc[u]))
o.append("")
o.append("### B4. 系统性漏取（gold 有、盲法几乎不给）")
o.append("")
o.append("| 穴 | gold | 盲法给出 | 命中率 |")
o.append("|---|---|---|---|")
for u in ("太阳", "外关", "阴谷", "睛明", "天突", "侠溪", "心俞", "肺俞", "肩井"):
    o.append("| %s | %d | %d | %.0f%% |"
             % (u, gc[u], pc[u], 100.0 * hc[u] / gc[u] if gc[u] else 0))
o.append("")

o.append("### B5. 这些漏取穴在技能自身资料中是否有记载")
o.append("")
docs = []
for r, _, fs in os.walk(SKILL):
    for f in fs:
        if f.lower().endswith((".md", ".json")):
            docs.append(os.path.join(r, f))
txt = {}
for p in docs:
    try:
        txt[p] = io.open(p, encoding="utf-8", errors="ignore").read()
    except Exception:
        pass
o.append("检索范围：`doubao-acupuncture-diagnosis/` 下 %d 个 `.md`/`.json`。" % len(docs))
o.append("")
o.append("| 穴 | 命中文件数 | 总出现次数 |")
o.append("|---|---|---|")
for u in ("太阳", "外关", "阴谷", "睛明", "天突", "侠溪", "心俞", "肺俞", "肩井", "内膝眼", "外膝眼"):
    hits = [t.count(u) for t in txt.values() if u in t]
    o.append("| %s | %d | %d |" % (u, len(hits), sum(hits)))
o.append("")
o.append("→ 除 **内膝眼（0 次）/ 外膝眼（2 次）** 外，其余漏取穴在资料中出现 18–109 次。"
         "**单诊召回失败不是知识缺口，是检索/选穴纪律缺口。**")
o.append("")

io.open(os.path.join(HERE, "PC8_结果.txt"), "w", encoding="utf-8", newline="\n").write(
    "\n".join(o) + "\n")
print("ok -> PC8_结果.txt")
