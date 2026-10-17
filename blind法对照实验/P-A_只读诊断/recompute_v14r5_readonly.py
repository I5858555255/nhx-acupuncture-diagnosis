#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-A 只读诊断：v14r5 逐案/逐链复算（fill the documented gap）。

背景：`E_分组验证/66_chain_status_inventory.md` §5 记录"不存在按链 v14r5 结果"。
本脚本用**唯一正式评分实现** `benchmark_v2/canonical_scorer.py`（原样、不改指标定义与分母），
对**冻结的** v14r5 盲法预测做逐案/逐链复算，产出本目录下的新文件。

纪律：
- 只读 gold / 预测 / 排除清单 / 链分组表；**不覆盖任何既有产物**；
- 输出仅写入本脚本所在目录；退出码 0/1 表示自检通过/失败；
- 自带自检：宏观指标须与既有 `G_验收/判分汇总v14r5.json` 逐项一致，否则报错退出。
"""
import csv
import json
import os
import pickle
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # 仓库根


def find_experiment_root(root):
    for name in sorted(os.listdir(root)):
        cand = os.path.join(root, name)
        if os.path.isfile(os.path.join(cand, "benchmark_v2", "canonical_scorer.py")):
            return cand
    return None


EXP = find_experiment_root(ROOT)
if EXP is None:
    print("[FAIL] 未定位到含 canonical_scorer.py 的实验目录")
    sys.exit(1)
BENCH = os.path.join(EXP, "benchmark_v2")
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")

sys.path.insert(0, BENCH)
from canonical_scorer import per_case_metrics, normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
CASE_IDS = gold["case_ids"]

EXCLUDE = set(r["case_id"] for r in csv.DictReader(
    open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
M1 = set(r["case_id"] for r in csv.DictReader(
    open(os.path.join(M5, "A_迁移核验", "迁移核验逐案表.csv"), encoding="utf-8-sig"))
    if r["M1审计案"] == "Y")
VT = {r["case_id"]: str(r.get("visit_type", "")) for r in csv.DictReader(
    open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig"))}
CHAIN = []
for r in csv.DictReader(open(os.path.join(M5, "E_分组验证", "分组交叉验证表.csv"), encoding="utf-8-sig")):
    CHAIN.append((r["患者链"], [x for x in (r["案号"] or "").split(";") if x]))
CHAIN_OF = {c: name for name, cases in CHAIN for c in cases}

PRED = json.load(open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))

per_case = {}
for c in CASE_IDS:
    if len(NEW[c]["gold_members"]) == 0:
        continue
    Gset = set(NEW[c]["gold_members"])
    Pset = set(normalize_units(PRED[c].get("主穴", [])))
    m = per_case_metrics(Gset, Pset)
    per_case[c] = {
        "tp": m["tp"], "fp": m["fp"], "fn": m["fn"],
        "recall": m["recall"], "prec": m["prec"], "f1": m["f1"], "jac": m["jac"],
        "gold_n": len(Gset), "pred_n": len(Pset),
        "fp_points": sorted(Pset - Gset), "fn_points": sorted(Gset - Pset),
    }

SC = list(per_case)
CORE = [c for c in SC if c not in EXCLUDE]
fu = [c for c in SC if VT.get(c, "").startswith("复诊")]
fs = [c for c in SC if c not in fu]


def macro(m, cids):
    if m in ("tp", "fp", "fn"):
        return sum(per_case[c][m] for c in cids)
    v = [per_case[c][m] for c in cids if per_case[c][m] is not None]
    return round(statistics.mean(v), 4)


def blk(cids):
    return dict(TP=macro("tp", cids), FP=macro("fp", cids), FN=macro("fn", cids),
                R=macro("recall", cids), P=macro("prec", cids),
                F1=macro("f1", cids), Jac=macro("jac", cids))


blocks = {
    "全量86": blk(SC), "核心集64": blk(CORE),
    "M1_28": blk([c for c in SC if c in M1]),
    "未M1_58": blk([c for c in SC if c not in M1]),
    "复诊": blk(fu), "首诊": blk(fs),
}

# 自检
ref = json.load(open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))
mismatch = []
for name, b in blocks.items():
    r = ref[name]["v14r5"]
    for k in ("TP", "FP", "FN", "R", "P", "F1", "Jac"):
        if abs(b[k] - r[k]) > 1e-9:
            mismatch.append("%s.%s: 复算=%s 官方=%s" % (name, k, b[k], r[k]))
ok = not mismatch

# 逐链
per_chain = []
for name, cases in CHAIN:
    cs = [c for c in cases if c in per_case]
    per_chain.append((name, len(cases), len(cs), blk(cs) if cs else None))

# ---- 输出（仅本目录）----
lines = ["# v14r5 逐案/逐链只读复算（P-A 生成产物）", ""]
lines.append("- 预测源：`G_验收/盲法v14r5/_blind93v14r5_results.json`（冻结，只读）")
lines.append("- 评分：`benchmark_v2/canonical_scorer.py` 原样（唯一正式实现，未改指标/分母）")
lines.append("- 自检（与 `判分汇总v14r5.json` 逐项比对）：**%s**" % ("一致 PASS" if ok else "不一致 FAIL"))
for m in mismatch:
    lines.append("  - %s" % m)
lines.append("")
lines.append("## 分层指标")
lines.append("")
lines.append("| 分层 | TP | FP | FN | R | P | F1 | Jac |")
lines.append("|---|---|---|---|---|---|---|---|")
for name in ("全量86", "核心集64", "M1_28", "未M1_58", "复诊", "首诊"):
    b = blocks[name]
    lines.append("| %s | %d | %d | %d | %.4f | %.4f | %.4f | %.4f |"
                 % (name, b["TP"], b["FP"], b["FN"], b["R"], b["P"], b["F1"], b["Jac"]))
lines.append("")
lines.append("## 逐链")
lines.append("")
lines.append("| 链 | 案数 | 计入 | TP | FP | FN | F1 |")
lines.append("|---|---:|---:|---:|---:|---:|---:|")
for name, n_all, n_sc, b in per_chain:
    if b:
        lines.append("| %s | %d | %d | %d | %d | %d | %.4f |"
                     % (name, n_all, n_sc, b["TP"], b["FP"], b["FN"], b["F1"]))
    else:
        lines.append("| %s | %d | 0 | - | - | - | - |" % (name, n_all))
lines.append("")

with open(os.path.join(HERE, "v14r5_分层与逐链.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

with open(os.path.join(HERE, "v14r5_逐案明细.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["case_id", "visit", "chain", "gold_n", "pred_n", "TP", "FP", "FN",
                "R", "P", "F1", "Jac", "FP点", "FN点"])
    for c in SC:
        d = per_case[c]
        w.writerow([c, VT.get(c, ""), CHAIN_OF.get(c, ""), d["gold_n"], d["pred_n"],
                    d["tp"], d["fp"], d["fn"], d["recall"], d["prec"], d["f1"], d["jac"],
                    ";".join(d["fp_points"]), ";".join(d["fn_points"])])

with open(os.path.join(HERE, "v14r5_逐链明细.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["chain", "案数", "计入", "TP", "FP", "FN", "F1"])
    for name, n_all, n_sc, b in per_chain:
        if b:
            w.writerow([name, n_all, n_sc, b["TP"], b["FP"], b["FN"], b["F1"]])
        else:
            w.writerow([name, n_all, 0, "", "", "", ""])

print("self-check vs 判分汇总v14r5.json:", "PASS" if ok else "FAIL")
for m in mismatch:
    print("  mismatch:", m)
print("scored cases:", len(SC), "| FP points:", sum(len(per_case[c]['fp_points']) for c in SC),
      "| FN points:", sum(len(per_case[c]['fn_points']) for c in SC))
sys.exit(0 if ok else 1)
