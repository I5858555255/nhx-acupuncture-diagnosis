#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对外部回传的 `runs/` 做**唯一正式口径**评分（v19 盲法重跑）。

用法：
    python score_blind_runs.py --runs <runs目录> [--arm A-1]

硬闸门：
  - 86/86 案必须存在且 status=OK；缺一即**拒绝出 F1**（只报缺哪些案）；
  - `主穴` 必须是非空字符串数组。

输出：blind_v19_score.txt（同目录），含：
  1) 完整性 / 合法性
  2) TP/FP/FN + 宏平均 F1（`canonical_scorer.normalize_units` + `_gold_results93v2.pkl`）
  3) 与 v14r5 / v18 / v19 预测级并列
  4) **泄漏探测**：与 `_blind93v14r5_results.json` 逐案主穴完全一致率（>50% 告警）
  5) 逐案差异清单（相对 v19 预测级）

只读：除输出 txt 外不写任何文件。
"""
import argparse
import io
import json
import os
import pickle
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

REF = {"v14r5": (362, 316, 331, 0.5185),
       "v18": (420, 263, 273, 0.5949),
       "v19预测级": (424, 265, 269, 0.5991)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--arm", default="A-1")
    ap.add_argument("--out", default="blind_v19_score.txt")
    a = ap.parse_args()

    gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
    SC = [c for c in gold["case_ids"] if len(gold["results"][c]["gold_members"]) > 0]
    GOLD = {c: set(normalize_units(gold["results"][c]["gold_members"])) for c in SC}

    out = []
    out.append("== v19 盲法重跑评分（arm=%s）==" % a.arm)
    out.append("")

    # ---- 1) 完整性 / 合法性 ----
    missing, skipped, bad, P = [], [], [], {}
    for c in SC:
        p = os.path.join(a.runs, "%s.json" % c)
        if not os.path.exists(p):
            missing.append(c)
            continue
        try:
            d = json.load(io.open(p, encoding="utf-8"))
        except Exception as e:
            bad.append("%s: JSON 解析失败 (%s)" % (c, e))
            continue
        st = str(d.get("status", "OK"))
        if st.upper() != "OK":
            skipped.append("%s: %s" % (c, d.get("reason", "")))
            continue
        pts = d.get("主穴")
        if not isinstance(pts, list) or not pts or not all(isinstance(x, str) and x.strip() for x in pts):
            bad.append("%s: 主穴 缺失/非字符串数组/为空" % c)
            continue
        if d.get("case_id") and d["case_id"] != c:
            bad.append("%s: case_id 不符 (%s)" % (c, d["case_id"]))
            continue
        P[c] = pts

    out.append("1) 完整性：应 %d 案 / 实到 %d 案 / 缺失 %d / SKIPPED %d / 非法 %d"
               % (len(SC), len(P), len(missing), len(skipped), len(bad)))
    for lbl, arr in (("缺失", missing), ("SKIPPED", skipped), ("非法", bad)):
        if arr:
            out.append("   [%s] %s" % (lbl, "；".join(arr[:12]) + ("…" if len(arr) > 12 else "")))
    if missing or skipped or bad or len(P) != len(SC):
        out.append("")
        out.append("2) 结果：**REJECTED** —— 不满足 86/86，按协议拒绝出 F1。")
        txt = "\n".join(out) + "\n"
        io.open(os.path.join(HERE, a.out), "w", encoding="utf-8", newline="\n").write(txt)
        sys.stdout.buffer.write(txt.encode("utf-8"))
        sys.exit(2)

    # ---- 2) 指标 ----
    tp = fp = fn = 0
    f1s = {}
    for c in SC:
        p_ = set(normalize_units(P[c]))
        g = GOLD[c]
        t = len(p_ & g)
        tp += t
        fp += len(p_ - g)
        fn += len(g - p_)
        rc = t / len(g) if g else 0.0
        pr = t / len(p_) if p_ else 0.0
        f1s[c] = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
    f1 = round(statistics.mean([f1s[c] for c in SC]), 4)

    out.append("2) 盲法结果：`TP %d / FP %d / FN %d`　**F1 = %.4f**（86 案宏平均）" % (tp, fp, fn, f1))
    out.append("")
    out.append("   参照（均为预测级/历史口径，**不可与上格混算**）：")
    for k, v in REF.items():
        out.append("     %-9s %s  ΔF1 %+.4f" % (k, "%d/%d/%d / %.4f" % v, f1 - v[3]))
    out.append("")
    models = {}
    for c in SC:
        d = json.load(io.open(os.path.join(a.runs, "%s.json" % c), encoding="utf-8"))
        models[str(d.get("model", "未标注"))] = models.get(str(d.get("model", "未标注")), 0) + 1
    out.append("3) 执行者自报模型分布：%s" % "；".join("%s×%d" % (k, v) for k, v in sorted(models.items())))
    n_up = sum(1 for c in SC
               if json.load(io.open(os.path.join(a.runs, "%s.json" % c), encoding="utf-8")).get("上游是否被采用"))
    out.append("   上游采用案数（自报）：%d / %d" % (n_up, len(SC)))
    out.append("")

    # ---- 4a) 独立性审计：防"直接抄 gold"（4b 只查历史 as-run 抓不到这一类）----
    eq_gold = sum(1 for c in SC if set(normalize_units(P[c])) == GOLD[c])
    precs = [len(set(normalize_units(P[c])) & GOLD[c]) / float(len(set(normalize_units(P[c]))))
             for c in SC if P[c]]
    sizes = [len(set(normalize_units(P[c]))) for c in SC]
    out.append("4a) 独立性审计：与 gold **集合完全一致** %d/%d = %.1f%%（有效推断通常 <20%%；"
               "若偏高须人工复核是否接触 gold）" % (eq_gold, len(SC), 100.0 * eq_gold / len(SC)))
    out.append("    平均 |P| = %.2f（gold 平均 %.2f）；平均逐案 precision = %.4f"
               % (statistics.mean(sizes), statistics.mean([len(GOLD[c]) for c in SC]),
                  statistics.mean(precs)))
    out.append("")

    # ---- 4b) 泄漏探测：与历史 as-run 的逐案完全一致率 ----
    hist = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
    same = 0
    for c in SC:
        h = set(normalize_units(hist[c].get("主穴", [])))
        if h and h == set(normalize_units(P[c])):
            same += 1
    rate = same / float(len(SC))
    out.append("4b) 泄漏探测：与历史 as-run（`_blind93v14r5_results.json`）逐案主穴**完全一致** %d/%d = %.1f%%"
               % (same, len(SC), 100 * rate))
    if rate > 0.5:
        out.append("   **⚠ 告警**：一致率 >50%，该批很可能接触过仓库历史结果 → **不得作为盲法结论**，只能登记为「含协议泄漏的上界跑」。")
    else:
        out.append("   未触发告警阈值（50%）。")
    out.append("")

    # ---- 4c) 分层：复诊案（R-FU 链内） vs 单诊案 ----
    rule = json.load(io.open(os.path.join(ROOT, "blind法对照实验", "P-N_开放重提炼",
                                          "PN_followup_rule.json"), encoding="utf-8"))
    chain_ids = set(x for ids in rule["患者分组(仅多案组)"].values() for x in ids)
    for lbl, sub in (("链内复诊案", [c for c in SC if c in chain_ids]),
                     ("单诊案", [c for c in SC if c not in chain_ids])):
        if sub:
            out.append("4c) %s n=%d：F1 = %.4f　TP/FP/FN = %d/%d/%d"
                       % (lbl, len(sub), statistics.mean([f1s[c] for c in sub]),
                          sum(len(set(normalize_units(P[c])) & GOLD[c]) for c in sub),
                          sum(len(set(normalize_units(P[c])) - GOLD[c]) for c in sub),
                          sum(len(GOLD[c] - set(normalize_units(P[c]))) for c in sub)))
    out.append("")

    # ---- 4d) 链内 gold 自重合度：说明 R-FU 在 canonical 口径下被结构化放大 ----
    js = []
    for ids in rule["患者分组(仅多案组)"].values():
        ids = sorted(ids, key=lambda x: (int(x.split("_")[1]), x))
        for i in range(1, len(ids)):
            ga, gb = GOLD[ids[i]], GOLD[ids[i - 1]]
            if ga | gb:
                js.append(len(ga & gb) / float(len(ga | gb)))
    if js:
        out.append("4d) 链内相邻 gold Jaccard：均值 %.3f / 中位 %.3f（n=%d）"
                   "——复诊案 gold 高度重复，'沿用上一诊' 在该口径下天然高分，"
                   "故链内 F1 不可单独作为推理能力证据"
                   % (statistics.mean(js), statistics.median(js), len(js)))
    out.append("")

    # ---- 5) 逐案差异（相对 v19 预测级） ----
    out.append("5) 逐案差异 vs v19 预测级（仅列不一致者；P=盲法主穴数 G=gold 数）")
    n_diff = 0
    for c in SC:
        p_ = set(normalize_units(P[c]))
        g = GOLD[c]
        hit = len(p_ & g)
        rc = hit / len(g) if g else 0.0
        pr = hit / len(p_) if p_ else 0.0
        f = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
        if not hit and not p_:
            n_diff += 1
            out.append("   %-8s P=%d G=%d hit=%d F1=0.0000" % (c, len(p_), len(g), hit))
        elif len(p_ - g) or len(g - p_):
            n_diff += 1
            out.append("   %-8s P=%-3d G=%-3d hit=%-3d FP=%-2d FN=%-2d F1=%.4f"
                       % (c, len(p_), len(g), hit, len(p_ - g), len(g - p_), f))
    out.append("   （共 %d 案与 gold 不完全一致）" % n_diff)
    out.append("")
    out.append("6) 口径纪律：本文件为**盲法级**数字，可与预测级并列，但**不得**表述为临床复现率；")
    out.append("   预测级与盲法级的差值登记为「部署损失」，不得反向用于回调规则后重测同一批。")

    txt = "\n".join(out) + "\n"
    io.open(os.path.join(HERE, a.out), "w", encoding="utf-8", newline="\n").write(txt)
    sys.stdout.buffer.write(txt.encode("utf-8"))
    sys.exit(0)


if __name__ == "__main__":
    main()
