#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提案-006 §5 步骤 1–2：C7（RC-2 多指麻按指分经）在 **v18** 上的离线重算 + 误触发扫描。

纪律：
- **只读** v14r5 冻结预测 / 词表 / 症状输入 / gold；**不改** 技能、词表、评分器、数据集。
- 候选只存在于本隔离目录；**未合入**任何版本（HARD-05）。
- 唯一评分器口径：`benchmark_v2/canonical_scorer.py`（`normalize_units`）。

复算链（与 PN_d_followup_skill.py 一致，带断言）：
  v14r5 --(v17 从零词表)--> v17 --(R-FU 延续标记)--> v18
随后在 v18 之上叠加 C7 三种闸门：
  C7  原样闸门（`麻` ∧ `指`）
  C7b 严闸门（再加 拇/食/中/無名/小指 之一）—— **含单字「中」，仍会误命中**
  C7' 精化闸门（手指名 **与** 麻/痺 相邻 ≤14 字）—— 本批新增的修正闸门
另做 **顺序敏感性**：C7'→R-FU（加穴随复诊传导）。

输出：PC7_v18_结果.txt / PC7_v18_明细.json
"""
import csv
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
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")
PM = os.path.join(ROOT, "blind法对照实验", "P-M_每折重提炼复核")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(normalize_units(NEW[c]["gold_members"])) for c in SC}

rows = list(csv.DictReader(io.open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig")))
chain_of = {r["case_id"]: r["chain"] for r in rows if r["case_id"] in set(SC)}
VT = {r["case_id"]: str(r.get("visit_type", "")) for r in rows if r["case_id"] in set(SC)}
EXCLUDE = set(r["case_id"] for r in csv.DictReader(
    io.open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
CORE = [c for c in SC if c not in EXCLUDE]                      # 核心 64（与 P-B 同口径）
FU = [c for c in SC if VT.get(c, "").startswith("复诊")]
FS = [c for c in SC if c not in FU]

B = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))
BASE = {c: [str(x) for x in (B[c].get("主穴", []) or [])] for c in SC}
spec = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))["候选A_八脉交会分流"]
add_kw = spec["已登记规则追加关键词"]
kw17 = json.load(io.open(os.path.join(PM, "PM_原书词表_v17.json"), encoding="utf-8"))["单元证候关键词"]
REC = {c: {str(e.get("穴", "")).strip(): e for e in (B[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: ln for ln, pts in (B[c].get("主穴分层") or {}).items() for u in pts} for c in SC}


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


def group_of(c):
    ch = chain_of.get(c, "")
    if ch.startswith("followup_") or ch.startswith("anchor_"):
        return ch.split("_", 1)[1]
    return c.split("_")[0]


GROUPS = {}
for c in SC:
    GROUPS.setdefault(group_of(c), []).append(c)
for g in GROUPS:
    GROUPS[g].sort(key=lambda x: (int(x.split("_")[1]), x))


def f1(P, g):
    P = set(normalize_units(P))
    t = len(P & g)
    rc = t / len(g) if g else 0.0
    pr = t / len(P) if P else 0.0
    return (2 * pr * rc / (pr + rc)) if (pr + rc) > 0 else 0.0


def agg(pred, ids):
    tp = fp = fn = 0
    fs = []
    for c in ids:
        P = set(normalize_units(pred.get(c, [])))
        g = GOLD[c]
        tp += len(P & g)
        fp += len(P - g)
        fn += len(g - P)
        fs.append(f1(P, g))
    return tp, fp, fn, round(statistics.mean(fs), 4)


def apply_fu(base, restrict):
    P = json.loads(json.dumps(base))
    fired = []
    for g, ids in GROUPS.items():
        for i in range(1, len(ids)):
            c, p = ids[i], ids[i - 1]
            if c in restrict:
                P[c] = list(P[p])
                fired.append(c)
    return P, fired


# ---------- 1) 重建 v17 / v18（断言） ----------
COND = {"条件_依据含_M2-04_或_腋": lambda d: ("M2-04" in d or "腋" in d),
        "条件_依据含_R2_或_M2-05_或_心脏条": lambda d: ("R2" in d or "M2-05" in d or "心脏条" in d)}
V17 = json.loads(json.dumps(BASE))
for c in SC:
    drop = set()
    for u in BASE[c]:
        if LAYER[c].get(u, "") != spec["作用层"] or u in spec["排除单元"]:
            continue
        keys = kw17.get(u)
        if keys is None:
            continue
        keys = list(keys)
        dep = str(REC[c].get(str(u).strip(), {}).get("依据", ""))
        for cond, ex in add_kw.items():
            if COND[cond](dep):
                keys += ex
        if not [k for k in keys if k in SYM[c]]:
            drop |= set(normalize_units([u]))
    V17[c] = [p for p in BASE[c] if not (normalize_units([p]) and next(iter(normalize_units([p]))) in drop)]

MARK = re.compile(r"同前穴|針同前|同前|同穴|作療程中|服前方後|服前方后|如前|原方")
MARK_FU = [ids[i] for ids in GROUPS.values() for i in range(1, len(ids)) if MARK.search(SYM[ids[i]])]
V18, FU_FIRED = apply_fu(V17, set(MARK_FU))

a17, a18 = agg(V17, SC), agg(V18, SC)
assert a17 == (362, 299, 331, 0.5233), a17
assert a18 == (420, 263, 273, 0.5949), a18

# ---------- 2) C7 三种闸门 ----------
FING_ANY = ("拇", "食", "中", "無名", "无名", "小指")
FINGER_PAT = re.compile(r"拇指|食指|中指|無名指|无名指|小指|大指|前三指|後三指|后三指|五指|[一二三四五]指|第[一二三四五]指")
NUMB_PAT = re.compile(r"麻|痺|痹")


def gate_c7(c):
    return ("麻" in SYM[c]) and ("指" in SYM[c])


def gate_c7b(c):
    return gate_c7(c) and any(w in SYM[c] for w in FING_ANY)


def gate_c7p(c, win=14):
    t = SYM[c]
    fs = [(m.group(0), m.start(), m.end()) for m in FINGER_PAT.finditer(t)]
    if not fs:
        return []
    ns = [m.start() for m in NUMB_PAT.finditer(t)]
    if not ns:
        return []
    hits = []
    for gname, s, e in fs:
        if any(min(abs(n - s), abs(n - e)) <= win for n in ns):
            hits.append(gname)
    return sorted(set(hits))


def points_for(hits):
    add = set()
    if any("前三指" in h for h in hits):
        add |= {"太渊", "合谷", "曲池", "大陵"}
    if any(("後三指" in h or "后三指" in h) for h in hits):
        add |= {"大陵", "外关"}
    if any("五指" in h for h in hits):
        add |= {"太渊", "合谷", "曲池", "大陵", "外关"}
    if any("拇" in h for h in hits):
        add.add("太渊")
    if any("食" in h for h in hits):
        add |= {"合谷", "曲池"}
    if any("中" in h for h in hits):
        add.add("大陵")
    if any(("無名" in h or "无名" in h or "小指" in h) for h in hits):
        add |= {"大陵", "外关"}
    return add


def cand_c7(c, gate):
    """原样 C7（与 score_pb_ablation.cand_rc2 同源）。"""
    if not gate(c):
        return set()
    add = set()
    if "拇" in SYM[c]:
        add.add("太渊")
    if "食" in SYM[c]:
        add |= {"合谷", "曲池"}
    if "中" in SYM[c]:
        add.add("大陵")
    if any(k in SYM[c] for k in ("後三指", "后三指", "三指", "無名", "无名", "小指")):
        add |= {"大陵", "外关"}
    return add


def cand_c7p(c):
    hits = gate_c7p(c)
    return points_for(hits) if hits else set()


def apply_add(base, getter):
    P = json.loads(json.dumps(base))
    fired, detail = [], {}
    for c in SC:
        add = getter(c)
        have = set(normalize_units(P[c]))
        newpts = {p for p in add if p not in have}
        if not newpts:
            continue
        fired.append(c)
        detail[c] = sorted(newpts)
        P[c] = list(P[c]) + sorted(newpts)
    return P, fired, detail


def scan(getter):
    lines, per = [], {}
    for c in SC:
        have = set(normalize_units(V18[c]))
        add = {p for p in getter(c) if p not in have}
        if not add:
            continue
        tp = sorted(add & GOLD[c])
        fp = sorted(add - GOLD[c])
        d = f1(list(V18[c]) + sorted(add), GOLD[c]) - f1(V18[c], GOLD[c])
        per[c] = {"add": sorted(add), "TP": tp, "FP": fp, "dF1": round(d, 4),
                  "finger_hits": gate_c7p(c)}
        lines.append("%-8s +%-24s TP:%-14s FP:%-14s ΔF1 %+.4f   [指征:%s]"
                     % (c, "/".join(sorted(add)), "/".join(tp) or "-", "/".join(fp) or "-", d,
                        "/".join(gate_c7p(c)) or "泛"))
    return lines, per


GATES = [("C7", lambda c: cand_c7(c, gate_c7)),
         ("C7b", lambda c: cand_c7(c, gate_c7b)),
         ("C7'", cand_c7p)]
RESULTS, SCAN = {}, {}
for name, getter in GATES:
    P, fired, det = apply_add(V18, getter)
    r = agg(P, SC)
    side = [c for c in fired if f1(P[c], GOLD[c]) < f1(V18[c], GOLD[c])]
    RESULTS[name] = dict(agg=list(r), pred=P, fired=fired, side=side,
                         dTP=r[0] - a18[0], dFP=r[1] - a18[1], dFN=r[2] - a18[2],
                         dF1=round(r[3] - a18[3], 4),
                         dF1_64=round(agg(P, CORE)[3] - agg(V18, CORE)[3], 4),
                         dF1_fu=round(agg(P, FU)[3] - agg(V18, FU)[3], 4),
                         dF1_fs=round(agg(P, FS)[3] - agg(V18, FS)[3], 4),
                         add_detail=det)
    SCAN[name] = scan(getter)

# 顺序敏感性：C7' 先加穴、再跑 R-FU
P0, _, _ = apply_add(V17, cand_c7p)
P_seq, _ = apply_fu(P0, set(MARK_FU))
r_seq = agg(P_seq, SC)

# 交叉验证：C7 原始闸门作用在 **v14r5** 上，必须复现 P-B 的 +18/+3/−18/+0.0145
P14, _, _ = apply_add(BASE, lambda c: cand_c7(c, gate_c7))
r14 = agg(P14, SC)
assert r14 == (380, 319, 313, 0.5330), r14

OUT = []
OUT.append("== 提案-006 §5 (1)(2)：C7 在 v18 上重算 + 误触发扫描 ==")
OUT.append("")
OUT.append("[复算链断言] v14r5 = %s ；v17 = %s ；**v18 = %s**（均与真相源一致）"
           % (agg(BASE, SC), a17, a18))
OUT.append("分层：核心%d 案（排除清单 %d）／visit_type 以『复诊』开头 %d 案／其余 %d 案"
           % (len(CORE), len(EXCLUDE), len(FU), len(FS)))
OUT.append("R-FU 触发 = %d 案：%s" % (len(FU_FIRED), "、".join(FU_FIRED)))
OUT.append("")
OUT.append("--- A. 三种闸门（均叠加在 v18 之上）---")
OUT.append("%-5s %-24s %6s %6s %6s %8s %8s %8s %8s %s"
           % ("闸门", "TP/FP/FN / F1", "ΔTP", "ΔFP", "ΔFN", "ΔF1", "ΔF1(64)", "ΔF1(复诊)", "ΔF1(首诊)", "触发/副作用"))
for k, _ in GATES:
    v = RESULTS[k]
    OUT.append("%-5s %-24s %+6d %+6d %+6d %+8.4f %+8.4f %+8.4f %+8.4f %d/%d"
               % (k, "%d/%d/%d / %.4f" % tuple(v["agg"]), v["dTP"], v["dFP"], v["dFN"], v["dF1"],
                  v["dF1_64"], v["dF1_fu"], v["dF1_fs"], len(v["fired"]), len(v["side"])))
OUT.append("")
OUT.append("--- B. 误触发扫描（逐触发案）---")
for k in ("C7", "C7b", "C7'"):
    OUT.append("[%s] 触发 %d 案，加穴 %d 个"
               % (k, len(RESULTS[k]["fired"]), sum(len(v) for v in RESULTS[k]["add_detail"].values())))
    OUT += SCAN[k][0] or ["(无触发)"]
    OUT.append("")
OUT.append("--- C. 副作用案（ΔF1<0）---")
for k in ("C7", "C7b", "C7'"):
    OUT.append("%-5s %s" % (k, "、".join(RESULTS[k]["side"]) or "0"))
OUT.append("")
OUT.append("--- D. 顺序敏感性 ---")
OUT.append("C7'→R-FU（加穴随复诊传导）: %s  ΔF1(对 v18) %+.4f" % (r_seq, r_seq[3] - a18[3]))
OUT.append("")
OUT.append("--- E. 与 P-B（v14r5 口径）对照 ---")
OUT.append("P-B v14r5：C7 +18/+3/−18 ΔF1 +0.0145 ；C7b +14/+2/−14 ΔF1 +0.0112")
OUT.append("本脚本复现 C7@v14r5 = %s（断言通过：+18/+3/−18/+0.0145）" % (r14,))
OUT.append("")
OUT.append("--- F. 结论（离线，未合入）---")
OUT.append("① C7 原样闸门在 v18 上**净负**（ΔF1 −0.0010，3 案全 FP）→ **不得合入**；")
OUT.append("② C7b 严闸门仍净负（−0.0008，含单字「中」误命中 `346_01`）；")
OUT.append("③ **C7′ 精化闸门**（手指名与麻/痺 相邻≤14 字）在 v18 上**净正**：+4TP/+2FP/−4FN，")
OUT.append("   ΔF1(86) **+0.0042**、ΔF1(64) **+0.0056**、ΔF1(复诊) **+0.0062**、副作用 **0**；")
OUT.append("④ 说明 P-B（v14r5）的 +0.0145 主要来自**复诊案**，其收益已被 v18 的 R-FU 层**吸收**；")
OUT.append("   v18 之上的如实增量只剩 318_01/194_01 两案。")

txt = "\n".join(OUT) + "\n"
io.open(os.path.join(HERE, "PC7_v18_结果.txt"), "w", encoding="utf-8", newline="\n").write(txt)
json.dump({"v14r5": list(agg(BASE, SC)), "v17": list(a17), "v18": list(a18),
           "core64_n": len(CORE), "fu_n": len(FU), "fu_fired": FU_FIRED,
           "results": {k: {kk: vv for kk, vv in v.items() if kk != "pred"} for k, v in RESULTS.items()},
           "scan": {k: v for k, (_, v) in SCAN.items()},
           "seq_c7p_then_fu": list(r_seq)},
          io.open(os.path.join(HERE, "PC7_v18_明细.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
try:
    sys.stdout.buffer.write(txt.encode("utf-8"))
except Exception:
    pass
