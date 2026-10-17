#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-A 只读诊断：把 C_残余归因（322 错 / 82 案）归入 WS-1..5 并量化。

纪律：
- 只读 `sf10_阶段M5/C_残余归因/残余归因表_分片*.csv`；
- 输出仅写本脚本所在目录；
- 归并为**显式规则**（类别基准 + 关键词覆盖），并在产物中保留"归并依据"列，
  供人工复核；不作为最终判定。
"""
import collections
import csv
import json
import os
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
C_DIR = os.path.join(EXP, "sf10_阶段M5", "C_残余归因")
SHARDS = ["残余归因表_分片1.csv", "残余归因表_分片2.csv"]

CAT_BASE = {
    "RULE-MISSING": "WS-4缺组补齐",
    "RULE-APPLICATION": "WS-1执行彻底化",
    "RULE-TRIGGER": "WS-2触发收窄降FP",
    "FALSE-POSITIVE": "WS-2触发收窄降FP",
    "HISTORY-LOSS": "WS-3随访延续",
    "INFORMATION-CEILING": "WS-0天花板/输入",
    "INPUT-LOSS": "WS-0天花板/输入",
    "INPUT-LOSS/RULE-MISSING": "WS-0天花板/输入",
    "NORMALIZATION-ISSUE": "WS-5口径议题",
    "GOLD-AMBIGUOUS": "WS-5口径议题",
    "无有效错误": "WS-5口径议题",
}
WS_ORDER = ["WS-1执行彻底化", "WS-2触发收窄降FP", "WS-3随访延续", "WS-4缺组补齐",
            "WS-5口径议题", "WS-0天花板/输入"]


def classify(cat, reason, action):
    blob = "%s %s" % (reason or "", action or "")
    base = CAT_BASE.get(cat, "未分类")
    # 覆盖规则（顺序即优先级）
    # 1) 技能侧 FP 被历史归入评分口径桶者，先纠正
    if "八脉凑数" in blob:
        return base, "WS-2触发收窄降FP", "八脉凑数（技能侧 FP，非评分口径）"
    # 2) 评分口径类（gold 解析/歧义）
    if base == "WS-5口径议题":
        return base, "WS-5口径议题", "口径类类别（gold 解析/歧义）"
    # 3) 输入缺失 / 信息天花板
    if "输入缺" in blob or "盲法输入" in blob or "输入未提" in blob or "无切诊" in blob:
        return base, "WS-0天花板/输入", "输入缺失"
    # 4) 随访延续
    if "随访" in blob or "同前" in blob or "复诊" in blob:
        return base, "WS-3随访延续", "随访/同前"
    # 5) 压痛二分 / 背俞反推
    if "耳穴" in blob or "耳胆" in blob or "耳肝" in blob or "耳肾" in blob or "耳心" in blob \
            or "反推背俞" in blob or "背俞定位" in blob or "误当背俞" in blob or "误定位" in blob:
        return base, "WS-2触发收窄降FP", "压痛二分/背俞反推"
    return base, base, "类别基准"


rows = []
for shard in SHARDS:
    with open(os.path.join(C_DIR, shard), "r", encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            r["_shard"] = shard
            rows.append(r)

out = []
for r in rows:
    cat = (r.get("类别") or "").strip()
    base, ws, why = classify(cat, r.get("技能原因"), r.get("建议操作"))
    out.append({
        "WS": ws, "归并依据": why, "类别基准": base,
        "方向": (r.get("方向") or "").strip(), "类别": cat,
        "案号": (r.get("案号") or "").strip(), "穴名": (r.get("穴名") or "").strip(),
        "证据强度": (r.get("证据强度") or "").strip(),
        "副作用案": (r.get("副作用案") or "").strip().replace("\n", " "),
        "潜在FP": (r.get("潜在FP") or "").strip().replace("\n", " "),
        "M2覆盖": (r.get("M2覆盖") or "").strip().replace("\n", " "),
        "技能原因": (r.get("技能原因") or "").strip().replace("\n", " "),
        "建议操作": (r.get("建议操作") or "").strip().replace("\n", " "),
        "分片": r["_shard"],
    })

by_ws = collections.Counter(x["WS"] for x in out)
by_ws_dir = collections.Counter((x["WS"], x["方向"]) for x in out)
cases = collections.defaultdict(set)
for x in out:
    cases[x["WS"]].add(x["案号"])
by_why = collections.Counter(x["归并依据"] for x in out)

with open(os.path.join(HERE, "残余归因_WS归并.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    for x in out:
        w.writerow(x)

lines = ["# 残余归因（322 错 / 82 案）WS 归并汇总（P-A 生成产物）", ""]
lines.append("- 来源：`C_残余归因/残余归因表_分片1.csv`、`分片2.csv`（v12 时代产物，只读）")
lines.append("- 总错误点：**%d**；涉及案：**%d**" % (len(out), len(set(x["案号"] for x in out))))
lines.append("")
lines.append("## 归并依据分布")
lines.append("")
for k, v in by_why.most_common():
    lines.append("- %s：%d" % (k, v))
lines.append("")
lines.append("## 按 WS")
lines.append("")
lines.append("| WS | 错误点 | FP | FN | 涉及案 |")
lines.append("|---|---:|---:|---:|---:|")
for ws in WS_ORDER:
    if by_ws.get(ws):
        lines.append("| %s | %d | %d | %d | %d |"
                     % (ws, by_ws[ws], by_ws_dir.get((ws, "FP"), 0),
                        by_ws_dir.get((ws, "FN"), 0), len(cases[ws])))
lines.append("")
lines.append("## 各 WS 涉及案号")
lines.append("")
for ws in WS_ORDER:
    if cases.get(ws):
        lines.append("- **%s**（%d 案）：%s" % (ws, len(cases[ws]), "、".join(sorted(cases[ws]))))
lines.append("")

with open(os.path.join(HERE, "残余归因_WS归并汇总.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

json.dump({"total_points": len(out), "by_ws": dict(by_ws),
           "by_ws_dir": {"%s|%s" % k: v for k, v in by_ws_dir.items()},
           "cases_by_ws": {k: sorted(v) for k, v in cases.items()}},
          open(os.path.join(HERE, "残余归因_WS归并汇总.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("points:", len(out), "cases:", len(set(x['案号'] for x in out)))
for ws in WS_ORDER:
    print(" ", ws, by_ws.get(ws, 0))
sys.exit(0)
