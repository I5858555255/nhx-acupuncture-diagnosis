#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-final-5 验证（v19 版）：C7′ 合入的**转写保真**与**复算达标**。

1) 转写保真度：SKILL.md 须含 v19 三处改动（版本基线行 / M2-03 ★ 闸门条文 / v19 附录），
   且闸门正则、邻近字数、指段→加穴映射、诚实披露项（ΔFP +2）全部在册。
2) 复算达标（**以 `候选规则_C7_条文.json` 为唯一真相源**，就地解释执行，不 import PC7 脚本）：
   —— v14r5 `362/316/331/0.5185`
   —— v17    `362/299/331/0.5233`
   —— v18    `420/263/273/0.5949`
   —— **v19（v18 + C7′）`424/265/269/0.5991`**，且与条文 JSON 的「预期_全86」逐项一致。
3) 逐案核对：触发案必须恰为 `318_01`、`194_01`；副作用案必须为 0。

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
PN = os.path.join(ROOT, "blind法对照实验", "P-N_开放重提炼")
C7DIR = os.path.join(PC, "C7_多指麻分经")
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
warns = []

# ---- 1) 转写保真度 ----
skill = io.open(SKILL, encoding="utf-8").read()
spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
add_kw = spec["已登记规则追加关键词"]
book = json.load(io.open(os.path.join(PM, "PM_原书词表_v17.json"), encoding="utf-8"))
json_kw = book["单元证候关键词"]
fu = json.load(io.open(os.path.join(PN, "PN_followup_rule.json"), encoding="utf-8"))
c7 = json.load(io.open(os.path.join(C7DIR, "候选规则_C7_条文.json"), encoding="utf-8"))

for probe in ["**v19 变更基线**", "## 附录·v19 候选合入条文",
              "★ v19·M2-03 触发闸门精化（C7′", "≤14 字",
              "前三指", "後三指", "第[一二三四五]指",
              "小指→`大陵`+`外关`", "ΔFP +2",
              "P-C_受控实验/C7_多指麻分经/"]:
    if probe not in skill:
        fails.append("缺少插入片段: %s" % probe)

# 旧版本线索仍在（不得回退）
for probe in ["**v18 变更基线**", "## 附录·v18 候选合入条文", "R-FU", "PN_followup_rule.json"]:
    if probe not in skill:
        fails.append("v18 线索丢失: %s" % probe)

# 八脉词表转写（沿用 v18 校验，防回归）
line = ""
matched = [l for l in skill.splitlines() if "八脉交会无对应证候者降临床参考建议（v16·候选A·原书源词表）" in l]
if not matched:
    fails.append("无法定位 SKILL.md 候选A 主条")
    skill_map = {}
else:
    line = matched[0]
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
    miss = [k for k in kws if k not in skill_map[unit]]
    if miss:
        fails.append("单元 %s 关键词未转写: %s" % (unit, miss))
for cond, kws in add_kw.items():
    for k in kws:
        if k not in line:
            fails.append("追加关键词未转写: %s (%s)" % (k, cond))

# ---- 2) 复算达标 ----
gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}
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

V17 = json.loads(json.dumps(PRED))
for c in SC:
    d = set()
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
            d |= set(normalize_units([u]))
    V17[c]["主穴"] = [p for p in V17[c].get("主穴", [])
                     if not (normalize_units([p]) and next(iter(normalize_units([p]))) in d)]

MARK = re.compile(fu["延续标记正则"])
V18 = json.loads(json.dumps(V17))
FIRE_FU = []
for g, ids in fu["患者分组(仅多案组)"].items():
    ids = sorted(ids, key=lambda x: (int(x.split("_")[1]), x))
    for i in range(1, len(ids)):
        c, p = ids[i], ids[i - 1]
        if MARK.search(SYM[c]):
            V18[c]["主穴"] = list(V18[p]["主穴"])
            FIRE_FU.append(c)

# ---- v19 = v18 + C7′，规则完全由条文 JSON 解释 ----
GATE = c7["触发闸门"]
MAP = c7["加穴映射"]
FPAT = re.compile(GATE["手指名正则"])
NPAT = re.compile(GATE["麻感正则"])
WIN = int(GATE["邻近约束_字"])


def c7_points(c):
    t = SYM[c]
    fingers = [(m.group(0), m.start(), m.end()) for m in FPAT.finditer(t)]
    if not fingers:
        return set(), []
    numbs = [m.start() for m in NPAT.finditer(t)]
    if not numbs:
        return set(), []
    hits = []
    for name, s, e in fingers:
        if any(min(abs(n - s), abs(n - e)) <= WIN for n in numbs):
            hits.append(name)
    hits = sorted(set(hits))
    add = set()
    for key, pts in MAP.items():
        for alias in key.split("/"):
            if alias and alias in hits:
                add |= set(pts)
    return add, hits


V19 = json.loads(json.dumps(V18))
FIRE_C7, HITS, ADDED = [], {}, {}
for c in SC:
    add, hits = c7_points(c)
    have = set(normalize_units(V18[c].get("主穴", [])))
    newpts = {p for p in add if p not in have}
    if not newpts:
        continue
    FIRE_C7.append(c)
    HITS[c] = hits
    ADDED[c] = sorted(newpts)
    V19[c]["主穴"] = list(V19[c].get("主穴", [])) + sorted(newpts)


def blk(d):
    tp = fp = fn = 0
    f1s = []
    per = {}
    for c in SC:
        P = set(normalize_units(d[c].get("主穴", [])))
        g = GOLD[c]
        t = len(P & g)
        tp += t
        fp += len(P - g)
        fn += len(g - P)
        rc = t / len(g) if g else 0.0
        pr = t / len(P) if P else 0.0
        f1 = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
        f1s.append(f1)
        per[c] = f1
    return (tp, fp, fn, round(statistics.mean(f1s), 4)), per


base, per14 = blk(PRED)
run17, _ = blk(V17)
run18, per18 = blk(V18)
run19, per19 = blk(V19)

if base != (362, 316, 331, 0.5185):
    fails.append("基线复算异常（期望 362/316/331/0.5185）: %s" % (base,))
if run17 != (362, 299, 331, 0.5233):
    fails.append("v17 复算异常（期望 362/299/331/0.5233）: %s" % (run17,))
if run18 != (420, 263, 273, 0.5949):
    fails.append("v18 复算异常（期望 420/263/273/0.5949）: %s" % (run18,))
if run19 != (424, 265, 269, 0.5991):
    fails.append("v19 复算异常（期望 424/265/269/0.5991）: %s" % (run19,))

exp = c7["预期_全86"]
for k, v in (("TP", run19[0]), ("FP", run19[1]), ("FN", run19[2]), ("F1", run19[3])):
    if abs(float(exp[k]) - float(v)) > 1e-9:
        fails.append("条文 JSON 预期_全86.%s=%s 与复算 %s 不符" % (k, exp[k], v))

if sorted(FIRE_C7) != ["194_01", "318_01"]:
    fails.append("触发案不符（期望 194_01、318_01）: %s" % (sorted(FIRE_C7),))
side = [c for c in FIRE_C7 if per19[c] < per18[c] - 1e-12]
if side:
    fails.append("出现副作用案（期望 0）: %s" % (side,))

for c in ("318_01", "194_01"):
    jt = c7.get("触发案", {}).get(c)
    if not jt:
        warns.append("条文 JSON 未登记触发案 %s" % c)
        continue
    if sorted(jt.get("加穴", [])) != ADDED.get(c):
        fails.append("%s 加穴不符：JSON=%s 复算=%s" % (c, jt.get("加穴"), ADDED.get(c)))
    if abs(float(jt.get("dF1", 0)) - (per19[c] - per18[c])) > 5e-5:
        warns.append("%s dF1 JSON=%s 复算 %+.4f" % (c, jt.get("dF1"), per19[c] - per18[c]))

print("== P-final-5 验证（v19·C7′ M2-03 闸门精化）==")
print("1) 转写保真度：v19 三处改动 + 闸门正则/邻近字数/映射/披露项；八脉词表 %d 单元 / 追加 %d 组；R-FU 真相源 %d 多案组；问题 %d 项"
      % (len(json_kw), len(add_kw), len(fu["患者分组(仅多案组)"]), len(fails)))
print("2) 基线 v14r5   : %s" % (base,))
print("   v17 候选A     : %s   →  ΔF1 %+.4f" % (run17, run17[3] - base[3]))
print("   v18 +R-FU     : %s   →  ΔF1 %+.4f（对 v17 %+.4f）；触发 %d 案"
      % (run18, run18[3] - base[3], run18[3] - run17[3], len(FIRE_FU)))
print("   v19 +C7′      : %s   →  ΔF1 %+.4f（对 v18 %+.4f）；触发 %d 案"
      % (run19, run19[3] - base[3], run19[3] - run18[3], len(FIRE_C7)))
print("3) 触发明细：")
for c in sorted(FIRE_C7):
    print("   %s  指征=%s  加穴=%s  逐案ΔF1 %+.4f"
          % (c, "/".join(HITS[c]), "/".join(ADDED[c]), per19[c] - per18[c]))
if warns:
    print("4) WARN：")
    for w in warns:
        print("   - %s" % w)
if fails:
    print("5) 结果：**FAIL** —— %d 项" % len(fails))
    for f in fails:
        print("   - %s" % f)
    sys.exit(1)
print("5) 结果：**PASS**（转写一致 + v14r5/v17/v18/v19 复算达标 + 触发案与副作用案符合条文）")
sys.exit(0)
