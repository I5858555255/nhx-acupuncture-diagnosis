#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-final 验证：候选A 合入 SKILL.md 后的三重校验。

1) 转写保真度：SKILL.md 新插入条文中的"本单元证候关键词"须与 `候选规则_条文化.json` 完全一致；
2) 复算达标：`_blind93_pcZ_A_results.json`（候选A 预测集）用唯一正式评分器复算，须达到 362→362 / 316→303；
3) 基线变更范围：SKILL.md 之外不得有其它技能文件改动（由 git 命令另行核验，本脚本只读）。

只读；不修改任何文件。
"""
import io
import json
import os
import pickle
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL = os.path.join(ROOT, "doubao-acupuncture-diagnosis", "SKILL.md")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
assert EXP, "未找到含 benchmark_v2/canonical_scorer.py 的实验根目录"
BENCH = os.path.join(EXP, "benchmark_v2")
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

fails = []

# ---- 1) 转写保真度 ----
skill = io.open(SKILL, encoding="utf-8").read()
spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))
json_kw = spec["候选A_八脉交会分流"]["单元证候关键词"]
add_kw = spec["候选A_八脉交会分流"]["已登记规则追加关键词"]

for probe in ["八脉交会无对应证候者降临床参考建议（v15·候选A）", "**v15 变更基线**",
              "## 附录·v15 候选合入条文（候选A）"]:
    if probe not in skill:
        fails.append("缺少插入片段: %s" % probe)

line = [l for l in skill.splitlines() if "八脉交会无对应证候者降临床参考建议（v15·候选A）" in l][0]
m = re.search(r"\*\*本单元证候关键词[^：]*：(.*?)。\*\*已登记规则适应症追加\*\*", line)
if not m:
    fails.append("无法定位 SKILL.md 证候关键词区段")
    skill_map = {}
else:
    skill_map = {}
    for seg in m.group(1).split("；"):
        if "→" not in seg:
            continue
        left, right = seg.split("→", 1)
        kws = set(x.replace("*", "").strip() for x in right.split("/") if x.replace("*", "").strip())
        for alias in re.split(r"[、/]", left):
            alias = alias.replace("*", "").strip()
            if alias:
                skill_map[alias] = kws

for unit, kws in json_kw.items():
    if unit not in skill_map:
        fails.append("SKILL.md 缺单元别名: %s" % unit)
        continue
    missing = [k for k in kws if k not in skill_map[unit]]
    if missing:
        fails.append("单元 %s 关键词未转写: %s" % (unit, missing))

for cond, kws in add_kw.items():
    for k in kws:
        if k not in line:
            fails.append("追加关键词未转写: %s (条件 %s)" % (k, cond))

# ---- 2) 复算达标 ----
gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}


def blk(path):
    d = json.load(io.open(path, encoding="utf-8"))
    tp = fp = fn = 0
    f1s = []
    for c in SC:
        P = set(normalize_units(d[c].get("主穴", [])))
        g = GOLD[c]
        t = len(P & g)
        tp += t
        fp += len(P - g)
        fn += len(g - P)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        f1s.append(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0)
    return tp, fp, fn, round(statistics.mean(f1s), 4)


base = blk(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"))
run = blk(os.path.join(PC, "_blind93_pcZ_A_results.json"))
if base != (362, 316, 331, 0.5185):
    fails.append("基线复算异常（期望 362/316/331/0.5185）: %s" % (base,))
if run != (362, 303, 331, 0.5223):
    fails.append("候选A 复算异常（期望 362/303/331/0.5223）: %s" % (run,))

print("== P-final 验证 ==")
print("1) 转写保真度：JSON 单元 %d 个、追加条件 %d 组；转写问题 %d 项"
      % (len(json_kw), len(add_kw), sum(1 for f in fails if ("转写" in f or "缺单元" in f))))
print("2) 基线复算：TP/FP/FN/F1 = %s" % (base,))
print("   候选A 复算：TP/FP/FN/F1 = %s  →  ΔTP %+d / ΔFP %+d / ΔF1 %+.4f"
      % (run, run[0] - base[0], run[1] - base[1], run[3] - base[3]))
if fails:
    print("3) 结果：**FAIL** —— %d 项" % len(fails))
    for f in fails:
        print("   - %s" % f)
    sys.exit(1)
print("3) 结果：**PASS**（转写一致 + 复算达标）")
sys.exit(0)
