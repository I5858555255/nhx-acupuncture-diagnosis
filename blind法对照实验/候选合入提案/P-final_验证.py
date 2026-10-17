#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-final / P-final-2 / P-final-3 验证：候选A 合入 SKILL.md 后的三重校验（v17 版）。

1) 转写保真度：SKILL.md 条文中的"本单元证候关键词"须与**当前真相源**逐词一致
   —— v15＝`候选规则_条文化.json`；v16＝`PM_原书词表.json`；**v17＝`PM_原书词表_v17.json`**；
   "已登记规则追加关键词"始终取自 `候选规则_条文化.json`；
2) 复算达标：由**真相源 + 引擎**自算 v17 预测集（不依赖任何中间 JSON），用唯一正式评分器复算：
   —— 基线 v14r5 `362/316/331/0.5185`；
   —— **v17 候选A `362/299/331/0.5233`**（v16 历史值 `362/298/331/0.5240`；v15 `362/303/331/0.5223`）；
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
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
assert EXP, "未找到含 benchmark_v2/canonical_scorer.py 的实验根目录"
BENCH = os.path.join(EXP, "benchmark_v2")
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

fails = []

# ---- 1) 转写保真度 ----
skill = io.open(SKILL, encoding="utf-8").read()
spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
add_kw = spec["已登记规则追加关键词"]
book = json.load(io.open(os.path.join(PM, "PM_原书词表_v17.json"), encoding="utf-8"))
json_kw = book["单元证候关键词"]

for probe in ["八脉交会无对应证候者降临床参考建议（v16·候选A·原书源词表）",
              "**v17 变更基线**", "## 附录·v17 候选合入条文（R1 微修·`列缺` 增补「皮」）"]:
    if probe not in skill:
        fails.append("缺少插入片段: %s" % probe)

matched_lines = [l for l in skill.splitlines() if "八脉交会无对应证候者降临床参考建议（v16·候选A·原书源词表）" in l]
line = matched_lines[0] if matched_lines else ""
if not matched_lines:
    fails.append("无法定位 SKILL.md 候选A 主条")
    skill_map = {}
else:
    m = re.search(r"\*\*本单元证候关键词[^：]*：(.*?)。\*\*(?:词表口径|已登记规则适应症追加)", line)
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

# ---- 2) 复算达标（自算 v17 预测集）----
gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}
PRED = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
REC = {c: {str(e.get("穴", "")).strip(): e for e in (PRED[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: ln for ln, pts in (PRED[c].get("主穴分层") or {}).items() for u in pts} for c in SC}
COND = {"条件_依据含_M2-04_或_腋": lambda d: ("M2-04" in d or "腋" in d),
        "条件_依据含_R2_或_M2-05_或_心脏条": lambda d: ("R2" in d or "M2-05" in d or "心脏条" in d)}


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


def dels(c):
    out = set()
    for u in (PRED[c].get("主穴", []) or []):
        if LAYER[c].get(u, "") != spec["作用层"] or u in spec["排除单元"]:
            continue
        keys = json_kw.get(u)
        if keys is None:
            continue
        keys = list(keys)
        dep = str(REC[c].get(str(u).strip(), {}).get("依据", ""))
        for cond, ex in add_kw.items():
            if COND[cond](dep):
                keys += ex
        if not [k for k in keys if k in SYM[c]]:
            out |= set(normalize_units([u]))
    return out


RUN = json.loads(json.dumps(PRED))
TRIG = {}
for c in SC:
    d = dels(c)
    if d:
        TRIG[c] = sorted(d)
        RUN[c]["主穴"] = [p for p in RUN[c].get("主穴", [])
                          if not (normalize_units([p]) and next(iter(normalize_units([p]))) in d)]


def blk(d):
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


base = blk(PRED)
run = blk(RUN)
if base != (362, 316, 331, 0.5185):
    fails.append("基线复算异常（期望 362/316/331/0.5185）: %s" % (base,))
if run != (362, 299, 331, 0.5233):
    fails.append("候选A(v17) 复算异常（期望 362/299/331/0.5233）: %s" % (run,))

print("== P-final-3 验证（v17·R1 微修）==")
print("1) 转写保真度：真相源 PM_原书词表_v17.json 单元 %d 个、追加条件 %d 组；转写问题 %d 项"
      % (len(json_kw), len(add_kw), sum(1 for f in fails if ("转写" in f or "缺单元" in f))))
print("2) 基线复算：TP/FP/FN/F1 = %s" % (base,))
print("   候选A(v17) 复算：TP/FP/FN/F1 = %s  →  ΔTP %+d / ΔFP %+d / ΔF1 %+.4f"
      % (run, run[0] - base[0], run[1] - base[1], run[3] - base[3]))
print("   触发案 %d 个：%s" % (len(TRIG), "、".join(sorted(TRIG))))
if fails:
    print("3) 结果：**FAIL** —— %d 项" % len(fails))
    for f in fails:
        print("   - %s" % f)
    sys.exit(1)
print("3) 结果：**PASS**（转写一致 + 复算达标）")
sys.exit(0)
