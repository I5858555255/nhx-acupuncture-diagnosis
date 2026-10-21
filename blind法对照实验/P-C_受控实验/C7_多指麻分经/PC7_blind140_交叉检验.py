#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C7′ 的**独立预测集交叉检验**（P-C 已授权；LLM 盲法重跑在本环境不可执行时的降级证据）。

为什么要这一步：
  C7′ 在 v14r5/sf10 链上只触发 2 案、增益集中（`318_01` 占 +0.3462），
  审稿视角的合理质疑是「这是否是对该预测链/该两案的过拟合」。

本脚本做两件事（均**只读**、唯一评分器口径 `canonical_scorer.normalize_units`）：
  A. **闸门原始触发审计**（不做去重）：全 86 案中闸门命中的所有案，逐案给出
     指征手指名 / 映射穴 / 该穴在 canonical gold 中是 TP 还是 FP。
     —— 这一步回答「闸门本身是否精准」，与预测链无关。
  B. **独立预测集交叉检验**：把 C7′ 施加到 **`盲法140/_blind140_results.json`**（真盲法140，
     与 sf10/v14r5 完全不同的一次生成过程）的主穴上，测 ΔF1 与副作用。
     —— 这一步回答「换一套预测流，增益是否复现、是否引入副作用」。

口径声明（必须随数字一起引用）：
  - 真盲法140 自身报告用的是**另一套 gold 口径**（gold 穴数合计 702）；本脚本为可比性
    统一到 **canonical gold（86 案 693）**，因此本脚本的绝对 F1 **不等于**其报告数字，
    只有 **Δ（前后差）** 可比。
  - 本脚本任何数字都是**离线预测级**，不是盲法结论。

输出：PC7_blind140_交叉检验.txt
"""
import ast
import io
import json
import os
import pickle
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
B140 = os.path.join(EXP, "盲法140")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

c7 = json.load(io.open(os.path.join(HERE, "候选规则_C7_条文.json"), encoding="utf-8"))
GATE, MAP = c7["触发闸门"], c7["加穴映射"]
FPAT = re.compile(GATE["手指名正则"])
NPAT = re.compile(GATE["麻感正则"])
WIN = int(GATE["邻近约束_字"])

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}


def sym(c):
    p = os.path.join(SD, "%s_symptoms_v2.json" % c)
    if not os.path.exists(p):
        return ""
    d = json.load(io.open(p, encoding="utf-8"))
    b = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            b.append(str(v["片段"]))
        elif isinstance(v, str):
            b.append(v)
    return "".join(b)


SYM = {c: sym(c) for c in SC}


def gate(c):
    t = SYM[c]
    fingers = [(m.group(0), m.start(), m.end()) for m in FPAT.finditer(t)]
    if not fingers:
        return [], set()
    numbs = [m.start() for m in NPAT.finditer(t)]
    if not numbs:
        return [], set()
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
    return hits, add


def f1(P, g):
    P = set(normalize_units(P))
    t = len(P & g)
    rc = t / len(g) if g else 0.0
    pr = t / len(P) if P else 0.0
    return (2 * pr * rc / (pr + rc)) if (pr + rc) > 0 else 0.0


OUT = []
OUT.append("== C7′ 独立预测集交叉检验（P-C 授权范围内；离线，非盲法结论）==")
OUT.append("")

# ---------- A. 闸门原始触发审计 ----------
OUT.append("--- A. 闸门原始触发审计（全 86 案，未做去重；穴名后的 + 表示 canonical gold 支持）---")
fires = []
for c in SC:
    hits, add = gate(c)
    if not add:
        continue
    fires.append(c)
    tp = sorted(add & GOLD[c])
    fp = sorted(add - GOLD[c])
    OUT.append("%-8s 指征=%-10s 映射=%-13s gold支持=%-14s 落空=%-12s 精确率 %d/%d"
               % (c, "/".join(hits), "/".join(sorted(add)),
                  "/".join(tp) or "-", "/".join(fp) or "-", len(tp), len(add)))
OUT.append("闸门原始触发 %d 案／%d 穴；其中 gold 支持 %d 穴、落空 %d 穴"
           % (len(fires), sum(len(gate(c)[1]) for c in fires),
              sum(len(gate(c)[1] & GOLD[c]) for c in fires),
              sum(len(gate(c)[1] - GOLD[c]) for c in fires)))
OUT.append("")

# ---------- B. 独立预测集（真盲法140）交叉检验 ----------
p140 = os.path.join(B140, "_blind140_results.json")
d140 = json.load(io.open(p140, encoding="utf-8"))


def parse_pts(v):
    if isinstance(v, list):
        return [str(x) for x in v]
    s = str(v or "").strip()
    if not s:
        return []
    try:
        x = ast.literal_eval(s)
        if isinstance(x, (list, tuple, set)):
            return [str(i) for i in x]
        return [str(x)]
    except Exception:
        return [t.strip() for t in re.split(r"[、,，;；/\s]+", s) if t.strip()]


K = [k for k in d140 if k in set(SC)]
OUT.append("--- B. 独立预测集：真盲法140（本脚本按 canonical gold 统一口径重算）---")
OUT.append("真盲法140 有输出的案中，与 86 可判分集交叠 = %d 案" % len(K))

P0 = {}
for c in K:
    P0[c] = parse_pts(d140[c].get("主穴"))
miss = [c for c in K if not P0[c]]
if miss:
    OUT.append("（%d 案主穴解析为空，已计为 0 穴：%s）" % (len(miss), "、".join(sorted(miss)[:10])))

IDS = [c for c in K if P0[c]]
base = round(statistics.mean([f1(P0[c], GOLD[c]) for c in IDS]), 4) if IDS else 0.0
tp = fp = fn = 0
for c in IDS:
    P = set(normalize_units(P0[c]))
    tp += len(P & GOLD[c])
    fp += len(P - GOLD[c])
    fn += len(GOLD[c] - P)

P1 = json.loads(json.dumps({c: P0[c] for c in IDS}))
fired, added = [], {}
for c in IDS:
    hits, add = gate(c)
    have = set(normalize_units(P1[c]))
    newpts = {p for p in add if p not in have}
    if not newpts:
        continue
    fired.append(c)
    added[c] = sorted(newpts)
    P1[c] = list(P1[c]) + sorted(newpts)

base_per = {c: f1(P0[c], GOLD[c]) for c in IDS}
new_per = {c: f1(P1[c], GOLD[c]) for c in IDS}
new = round(statistics.mean([new_per[c] for c in IDS]), 4) if IDS else 0.0
tp2 = fp2 = fn2 = 0
for c in IDS:
    P = set(normalize_units(P1[c]))
    tp2 += len(P & GOLD[c])
    fp2 += len(P - GOLD[c])
    fn2 += len(GOLD[c] - P)

OUT.append("真盲法140 主穴基线（canonical gold）：%d/%d/%d  F1 %.4f（%d 案）" % (tp, fp, fn, base, len(IDS)))
OUT.append("施加 C7′ 后                ：%d/%d/%d  F1 %.4f（ΔTP %+d / ΔFP %+d / ΔFN %+d / ΔF1 %+.4f）"
           % (tp2, fp2, fn2, new, tp2 - tp, fp2 - fp, fn2 - fn, new - base))
OUT.append("触发 %d 案／加 %d 穴" % (len(fired), sum(len(v) for v in added.values())))
for c in fired:
    t = sorted(set(added[c]) & GOLD[c])
    f_ = sorted(set(added[c]) - GOLD[c])
    OUT.append("  %-8s 加穴=%-22s TP=%-14s FP=%-12s 逐案ΔF1 %+.4f"
               % (c, "/".join(added[c]), "/".join(t) or "-", "/".join(f_) or "-", new_per[c] - base_per[c]))
side = [c for c in fired if new_per[c] < base_per[c] - 1e-12]
OUT.append("副作用案（ΔF1<0）：%s" % ("、".join(side) if side else "0"))
OUT.append("")

# 两案是否在同一集合内
for c in ("318_01", "194_01"):
    OUT.append("%s 在真盲法140 交叠集内：%s" % (c, "是" if c in set(IDS) else "否"))
OUT.append("")

OUT.append("--- C. 读法（务必连同本段引用）---")
OUT.append("1) A 段测的是**闸门精准度**：闸门给出的穴在 gold 中确有支持者，说明映射方向不是噪声；")
OUT.append("2) B 段测的是**跨预测流复现**：若 ΔF1 ≥ 0 且副作用 0，则 C7′ 未绑定于 sf10 链；")
OUT.append("3) 两段都**不能**替代 LLM 盲法重跑（本环境无可执行通道，已登记 BLOCKED）；")
OUT.append("4) B 段绝对 F1 与本仓库 `盲法140判分报告.md` 的数字**不可直接比较**（gold 口径不同），只有 Δ 可比。")

txt = "\n".join(OUT) + "\n"
io.open(os.path.join(HERE, "PC7_blind140_交叉检验.txt"), "w", encoding="utf-8", newline="\n").write(txt)
try:
    sys.stdout.buffer.write(txt.encode("utf-8"))
except Exception:
    pass
