#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-M：M9 式『每折重新提炼规则』盲法重跑 —— 候选A（八脉分流）与候选B-v2（R2 分期）。

沿袭既有 M9 漏斗（`fold_ruleselect.py` + `score_m9c1.py`）：
  - 折 = 患者链（66 链，源自 `M9-链分组表.csv`）；
  - 每折只用**训练链**重提炼/复核规则，再作用于留出链；
  - 聚合用唯一正式评分器 canonical（宏平均 F1）。

本批新增（相对 M9 固定池 = 逐折『选择』）：
  1) **参数级重导出**：候选A 的词表改为**纯原书源重导出**（PM_原书词表.json，逐条附出处行号），
     完全不含 gold/观察 → 检验 P-L 登记的 R1（221_01 观察驱动修正）在『原书源』下是否结构性消解；
  2) **逐折成立性 + 逐折留出聚合**：每折用训练链算 删穴净额，判定 启用/收缩/关闭，
     仅『启用』折才把规则作用到留出链 → 得到真正的 leave-one-chain-out 聚合 F1；
  3) **信号支撑表**：每个触发关键词被多少**其它链**支撑 → 检出单链支撑（不可跨链外推）的规则；
  4) **候选B-v2 逐折词表重导出**：留出某链后，若其触发信号在其它链无支撑，则该案在重导出下不再触发。

只读输入；只写本目录；唯一正式评分器。
"""
import csv
import hashlib
import io
import json
import os
import pickle
import statistics
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
assert EXP, "未找到 benchmark_v2/canonical_scorer.py"
BENCH = os.path.join(EXP, "benchmark_v2")
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
PC = os.path.join(ROOT, "blind法对照实验", "P-C_受控实验")

sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

SPEC = json.load(io.open(os.path.join(PC, "候选规则_条文化.json"), encoding="utf-8"))
A_SPEC = SPEC["候选A_八脉交会分流"]
B_SPEC = SPEC["候选B_R2病程分期"]
KW_OLD = A_SPEC["单元证候关键词"]
KW_BOOK = json.load(io.open(os.path.join(HERE, "PM_原书词表.json"), encoding="utf-8"))["单元证候关键词"]

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}

EXCLUDE = set(r["case_id"] for r in csv.DictReader(
    io.open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
M1 = set(r["case_id"] for r in csv.DictReader(
    io.open(os.path.join(M5, "A_迁移核验", "迁移核验逐案表.csv"), encoding="utf-8-sig")) if r["M1审计案"] == "Y")
VT = {r["case_id"]: str(r.get("visit_type", "")) for r in csv.DictReader(
    io.open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig"))}

CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    v = str(r.get("在86判分", "")).strip()
    if not v.isdigit() or int(v) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in set(SC)]
    if ids:
        CHAINS[r["链ID"]] = ids
CH_OF = {c: k for k, v in CHAINS.items() for c in v}
assert len(CH_OF) == len(SC), "链映射未全覆盖: %d vs %d" % (len(CH_OF), len(SC))

PRED = json.load(io.open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))

CORE = [c for c in SC if c not in EXCLUDE]
FU = [c for c in SC if VT.get(c, "").startswith("复诊")]
FS = [c for c in SC if c not in FU]
LAYERS = [("全量86", SC), ("核心集64", CORE), ("M1_28", [c for c in SC if c in M1]),
          ("未M1_58", [c for c in SC if c not in M1]), ("复诊", FU), ("首诊", FS)]


def symptom_text(c):
    p = os.path.join(SD, "%s_symptoms_v2.json" % c)
    if not os.path.exists(p):
        return ""
    d = json.load(io.open(p, encoding="utf-8"))
    buf = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            buf.append(str(v["片段"]))
        elif isinstance(v, str):
            buf.append(v)
    return "".join(buf)


SYM = {c: symptom_text(c) for c in SC}
UNIT_OF = {c: list(PRED[c].get("主穴", []) or []) for c in SC}
REC = {c: {str(e.get("穴", "")).strip(): e for e in (PRED[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: lname for lname, pts in (PRED[c].get("主穴分层") or {}).items() for u in pts} for c in SC}
EXTRA_COND = {
    "条件_依据含_M2-04_或_腋": lambda dep: ("M2-04" in dep or "腋" in dep),
    "条件_依据含_R2_或_M2-05_或_心脏条": lambda dep: ("R2" in dep or "M2-05" in dep or "心脏条" in dep),
}


def ruleA_dels(c, kwtab):
    dels, hits = set(), {}
    for u in UNIT_OF[c]:
        if LAYER[c].get(u, "") != A_SPEC["作用层"] or u in A_SPEC["排除单元"]:
            continue
        keys = kwtab.get(u)
        if keys is None:
            hits[u] = "无词表条目→不删"
            continue
        keys = list(keys)
        dep = str(REC[c].get(str(u).strip(), {}).get("依据", ""))
        for cond, extra in A_SPEC["已登记规则追加关键词"].items():
            if EXTRA_COND[cond](dep):
                keys += extra
        matched = [k for k in keys if k in SYM[c]]
        if not matched:
            dels |= set(normalize_units([u]))
            hits[u] = "无命中→删"
        else:
            hits[u] = "命中" + "、".join(matched[:4])
    return dels, hits


def evalset(pred):
    per = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        G2 = GOLD[c]
        t = len(P & G2)
        rc = t / len(G2) if G2 else 0.0
        pr = t / len(P) if P else 0.0
        per[c] = dict(P=P, tp=t, fp=len(P - G2), fn=len(G2 - P),
                      f1=(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0))
    return per


def blk(per, cids):
    return dict(TP=sum(per[c]["tp"] for c in cids), FP=sum(per[c]["fp"] for c in cids),
                FN=sum(per[c]["fn"] for c in cids),
                F1=round(statistics.mean([per[c]["f1"] for c in cids]), 4))


BASE = json.loads(json.dumps(PRED))
PER_BASE = evalset(BASE)
LAY_BASE = {n: blk(PER_BASE, ids) for n, ids in LAYERS}


def applyA(dels, apply_map, tag):
    data = json.loads(json.dumps(BASE))
    for c, d in dels.items():
        if not d or not apply_map.get(c, False):
            continue
        rec = data[c]
        rec["主穴"] = [p for p in rec.get("主穴", [])
                       if not (normalize_units([p]) and next(iter(normalize_units([p]))) in d)]
        lay = rec.get("主穴分层") or {}
        for k in list(lay.keys()):
            lay[k] = [x for x in lay[k] if not (normalize_units([x]) and next(iter(normalize_units([x]))) in d)]
        rec["主穴分层"] = lay
    out = os.path.join(HERE, "_pm_%s_results.json" % tag)
    json.dump(data, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, hashlib.sha256(open(out, "rb").read()).hexdigest()


def applyB(recovery, tag):
    data = json.loads(json.dumps(BASE))
    for c in recovery:
        rec = data[c]
        before = list(rec.get("主穴", []))
        pts = [p for p in before if p != "太冲"]
        if "足三里" not in pts:
            idx = before.index("太冲") if "太冲" in before else len(pts)
            pts.insert(min(idx, len(pts)), "足三里")
        rec["主穴"] = pts
    out = os.path.join(HERE, "_pm_%s_results.json" % tag)
    json.dump(data, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, hashlib.sha256(open(out, "rb").read()).hexdigest()


def side_of(PER):
    s = []
    for c in SC:
        dtp = PER[c]["tp"] - PER_BASE[c]["tp"]
        dfp = PER[c]["fp"] - PER_BASE[c]["fp"]
        if dtp < 0 or dfp > 0:
            s.append("%s(TP%+d,FP%+d)" % (c, dtp, dfp))
    return s


def diff_rows(PER, cids):
    b, r = blk(PER_BASE, cids), blk(PER, cids)
    return dict(TP_b=b["TP"], TP_r=r["TP"], FP_b=b["FP"], FP_r=r["FP"],
                FN_b=b["FN"], FN_r=r["FN"], F1_b=b["F1"], F1_r=r["F1"], dF1=round(r["F1"] - b["F1"], 4))


def selfcheck():
    ref = json.load(io.open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))["全量86"]["v14r5"]
    b = LAY_BASE["全量86"]
    return b["TP"] == ref["TP"] and b["FP"] == ref["FP"] and b["FN"] == ref["FN"] and abs(b["F1"] - ref["F1"]) < 1e-9


SUMMARY = {"selfcheck": selfcheck(), "base": LAY_BASE, "variants": {}, "loco": {}, "signals": [],
           "B2": {}}
OUT_CSV_CHAIN, OUT_CSV_FOLD, OUT_CSV_SIG = [], [], []

# ---------------- 候选A：两版词表 ----------------
D_OLD = {c: ruleA_dels(c, KW_OLD)[0] for c in SC}
D_OLD = {c: v for c, v in D_OLD.items() if v}
D_BOOK = {c: ruleA_dels(c, KW_BOOK)[0] for c in SC}
D_BOOK = {c: v for c, v in D_BOOK.items() if v}

KW_SUPER = {}
for u in set(list(KW_OLD.keys()) + list(KW_BOOK.keys())):
    KW_SUPER[u] = list(dict.fromkeys(list(KW_OLD.get(u, [])) + list(KW_BOOK.get(u, []))))
D_SUPER = {c: ruleA_dels(c, KW_SUPER)[0] for c in SC}
D_SUPER = {c: v for c, v in D_SUPER.items() if v}

for tag, D, kwtab in [("A_v15表(出厂)", D_OLD, KW_OLD), ("A_原书超集", D_SUPER, KW_SUPER),
                      ("A_原书从零重建", D_BOOK, KW_BOOK)]:
    out, h = applyA(D, {c: True for c in D}, tag)
    PER = evalset(json.load(io.open(out, encoding="utf-8")))
    rows = {n: diff_rows(PER, ids) for n, ids in LAYERS}
    SUMMARY["variants"][tag] = {"sha256": h, "trigger_cases": sorted(D),
                                "deleted_units": sum(len(v) for v in D.values()),
                                "rows": rows, "side": side_of(PER),
                                "dTP": rows["全量86"]["TP_r"] - rows["全量86"]["TP_b"],
                                "dFP": rows["全量86"]["FP_r"] - rows["全量86"]["FP_b"],
                                "dF1": rows["全量86"]["dF1"], "dF1_64": rows["核心集64"]["dF1"]}
    print("[%s] 触发 %d 案 / 删 %d 穴 | ΔTP %+d ΔFP %+d ΔF1 %+.4f (64 %+.4f) | 副作用 %s"
          % (tag, len(D), sum(len(v) for v in D.values()),
             rows["全量86"]["TP_r"] - rows["全量86"]["TP_b"], rows["全量86"]["FP_r"] - rows["全量86"]["FP_b"],
             rows["全量86"]["dF1"], rows["核心集64"]["dF1"], "、".join(side_of(PER)) or "0"))
    for c in sorted(D):
        OUT_CSV_CHAIN.append([tag, CH_OF.get(c), c, len(D[c]), "、".join(sorted(D[c]))])

# ---------------- 逐折 LOCO（候选A：出厂 v15 表 / 原书从零重建表）----------------
for lo_tag, D, safe in [("A_v15表(出厂)", D_OLD, "A_v15_LOCO"), ("A_原书从零重建", D_BOOK, "A_book_LOCO")]:
    verdicts = {}
    loco_apply = {}
    for cid, cases in CHAINS.items():
        train = [c for c in SC if c not in set(cases)]
        tp_del = fp_del = 0
        trig_train = 0
        for c in train:
            if c in D:
                trig_train += 1
                tp_del += len(D[c] & GOLD[c])
                fp_del += len(D[c] - GOLD[c])
        net = fp_del - tp_del
        if trig_train == 0:
            v = "关闭(无触发)"
        elif net >= 0:
            v = "启用(净%+d)" % net
        else:
            v = "收缩(净%+d)" % net
        verdicts[cid] = {"verdict": v, "train_trig": trig_train, "del_TP": tp_del, "del_FP": fp_del, "net": net}
        for c in cases:
            loco_apply[c] = v.startswith("启用")
    out, h = applyA(D, loco_apply, safe)
    PER_LOCO = evalset(json.load(io.open(out, encoding="utf-8")))
    loco_rows = {n: diff_rows(PER_LOCO, ids) for n, ids in LAYERS}
    vc = {"启用": 0, "收缩": 0, "关闭": 0}
    for v in verdicts.values():
        if v["verdict"].startswith("启用"):
            vc["启用"] += 1
        elif v["verdict"].startswith("收缩"):
            vc["收缩"] += 1
        else:
            vc["关闭"] += 1
    SUMMARY["loco"][lo_tag] = {"sha256": h, "verdict_counts": vc, "rows": loco_rows,
                               "verdicts": verdicts,
                               "dTP": loco_rows["全量86"]["TP_r"] - loco_rows["全量86"]["TP_b"],
                               "dFP": loco_rows["全量86"]["FP_r"] - loco_rows["全量86"]["FP_b"],
                               "dF1": loco_rows["全量86"]["dF1"], "dF1_64": loco_rows["核心集64"]["dF1"],
                               "side": side_of(PER_LOCO),
                               "changed_cases": [c for c in D if loco_apply.get(c)]}
    print("[%s LOCO] 折判定 启用%d/收缩%d/关闭%d | ΔTP %+d ΔFP %+d ΔF1 %+.4f (64 %+.4f) | 副作用 %s"
          % (lo_tag, vc["启用"], vc["收缩"], vc["关闭"],
             loco_rows["全量86"]["TP_r"] - loco_rows["全量86"]["TP_b"],
             loco_rows["全量86"]["FP_r"] - loco_rows["全量86"]["FP_b"],
             loco_rows["全量86"]["dF1"], loco_rows["核心集64"]["dF1"], "、".join(side_of(PER_LOCO)) or "0"))
    for cid in CHAINS:
        v = verdicts[cid]
        OUT_CSV_FOLD.append([lo_tag, cid, " ".join(CHAINS[cid]), v["train_trig"], v["del_TP"], v["del_FP"],
                             v["net"], v["verdict"]])

# ---------------- 关键词 × 链支撑（检出"单链支撑"＝不可跨链外推的判别词）----------------
chain_of = {c: CH_OF.get(c) for c in SC}
ALL_KW = {}
for u in set(list(KW_OLD.keys()) + list(KW_BOOK.keys())):
    for k in list(KW_OLD.get(u, [])) + list(KW_BOOK.get(u, [])):
        ALL_KW.setdefault(k, set()).add(u)
for k in sorted(ALL_KW, key=lambda x: (len([c for c in SC if x in SYM[c]]), x)):
    chains_k = sorted(set(chain_of[c] for c in SC if k in SYM[c]))
    single = len(chains_k) <= 1
    OUT_CSV_SIG.append([k, "、".join(sorted(ALL_KW[k])), len(chains_k), "、".join(chains_k),
                        "单链支撑" if single else ""])
    SUMMARY["signals"].append({"kw": k, "units": sorted(ALL_KW[k]), "chain_n": len(chains_k),
                               "chains": chains_k, "single_chain": single})

# ---------------- 候选B-v2：逐折词表重导出 ----------------
B2_STRONG = [k for k in B_SPEC["强正向关键词"] if k not in ("足溫", "雙足溫")]
FLW = set(B_SPEC["适用案集"])


def b_neg(c):
    return [k for k in B_SPEC["负向关键词"] if k in SYM[c]]


def sig_chain_support(k):
    return sorted(set(chain_of[c] for c in SC if k in SYM[c]))


B2_support = {}
for k in B2_STRONG:
    ch = sig_chain_support(k)
    if ch:
        B2_support[k] = ch

B2_fixed = {c: ("恢复期" if (not b_neg(c) and [k for k in B2_STRONG if k in SYM[c]]) else
                ("急性期" if b_neg(c) else "无法判定")) for c in SC}
B2_fixed_rec = [c for c in SC if B2_fixed[c] == "恢复期" and c in FLW]

# 逐折重导出：留出某链后，其触发信号必须在**其它链**仍有支撑，否则该案不再触发
B2_loco_rec = []
B2_loco_reason = {}
for c in SC:
    if c not in FLW:
        continue
    ch = chain_of[c]
    if b_neg(c):
        B2_loco_reason[c] = "急性期（负向命中）"
        continue
    trig = [k for k in B2_STRONG if k in SYM[c]]
    if not trig:
        B2_loco_reason[c] = "无强正向命中"
        continue
    kept = [k for k in trig if any(x != ch for x in B2_support.get(k, []))]
    B2_loco_reason[c] = {"触发信号": trig, "留出后仍被其它链支撑的信号": kept,
                         "各信号所属链": {k: B2_support.get(k, []) for k in trig}}
    if kept:
        B2_loco_rec.append(c)

out_f, h_f = applyB(B2_fixed_rec, "B2_固定词表")
PER_BF = evalset(json.load(io.open(out_f, encoding="utf-8")))
out_l, h_l = applyB(B2_loco_rec, "B2_逐折重导出")
PER_BL = evalset(json.load(io.open(out_l, encoding="utf-8")))
for tag, PER, h in [("B2_固定词表", PER_BF, h_f), ("B2_逐折重导出", PER_BL, h_l)]:
    rows = {n: diff_rows(PER, ids) for n, ids in LAYERS}
    SUMMARY["B2"][tag] = {"sha256": h, "recovery_cases": B2_fixed_rec if "固定" in tag else B2_loco_rec,
                          "rows": rows, "side": side_of(PER),
                          "dTP": rows["全量86"]["TP_r"] - rows["全量86"]["TP_b"],
                          "dFP": rows["全量86"]["FP_r"] - rows["全量86"]["FP_b"],
                          "dF1": rows["全量86"]["dF1"], "dF1_64": rows["核心集64"]["dF1"]}
    print("[%s] 恢复期 %d 案 | ΔTP %+d ΔFP %+d ΔF1 %+.4f (64 %+.4f) | 副作用 %s"
          % (tag, len(SUMMARY["B2"][tag]["recovery_cases"]),
             rows["全量86"]["TP_r"] - rows["全量86"]["TP_b"], rows["全量86"]["FP_r"] - rows["全量86"]["FP_b"],
             rows["全量86"]["dF1"], rows["核心集64"]["dF1"], "、".join(side_of(PER)) or "0"))
SUMMARY["B2"]["signal_support"] = {k: B2_support[k] for k in B2_STRONG if k in B2_support}
SUMMARY["B2"]["loco_reason"] = B2_loco_reason

with io.open(os.path.join(HERE, "PM_判分汇总.json"), "w", encoding="utf-8") as f:
    json.dump(SUMMARY, f, ensure_ascii=False, indent=2)
with io.open(os.path.join(HERE, "PM_逐案删穴表.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["词表版本", "链", "案号", "删穴数", "删穴"]); w.writerows(OUT_CSV_CHAIN)
with io.open(os.path.join(HERE, "PM_每折判定表.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["词表版本", "链", "案号", "训练触发案数", "删中TP", "删中FP", "净", "判定"]); w.writerows(OUT_CSV_FOLD)
with io.open(os.path.join(HERE, "PM_信号支撑表.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(["关键词", "所属单元", "支撑链数", "支撑链", "单链支撑"]); w.writerows(OUT_CSV_SIG)
print("wrote PM_判分汇总.json / PM_逐案删穴表.csv / PM_每折判定表.csv / PM_信号支撑表.csv")
sys.exit(0 if SUMMARY["selfcheck"] else 1)
