#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-C‴ 规则级复核引擎。

直接读取 `候选规则_条文化.json`（唯一真相源）并执行，用于：
  1) 规则级重跑：候选A（八脉分流）／候选B（R2 分期）／A+B → 与 P-C′/P-C″ 的预测级 patch 结果对照；
  2) 全 86 案误触发扫描：不预设适用案集，扫出所有会被闸门命中的案（检验过度触发）；
  3) 候选B 的稳健性矩阵：(非假设句过滤 开/关) × (弱正向信号 可/不可单独触发)。

唯一正式评分器；只读输入；输出只写本目录。
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
BENCH = os.path.join(EXP, "benchmark_v2")
M5 = os.path.join(EXP, "sf10_阶段M5")
G = os.path.join(M5, "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")

sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

SPEC = json.load(io.open(os.path.join(HERE, "候选规则_条文化.json"), encoding="utf-8"))
A_SPEC = SPEC["候选A_八脉交会分流"]
B_SPEC = SPEC["候选B_R2病程分期"]

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
CHAIN = {}
for r in csv.DictReader(io.open(os.path.join(M5, "E_分组验证", "分组交叉验证表.csv"), encoding="utf-8-sig")):
    for x in (r["案号"] or "").split(";"):
        if x:
            CHAIN[x] = r["患者链"]

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


# ================= 候选A：八脉交会分流（规则级） =================
EXTRA_COND = {
    "条件_依据含_M2-04_或_腋": lambda dep: ("M2-04" in dep or "腋" in dep),
    "条件_依据含_R2_或_M2-05_或_心脏条": lambda dep: ("R2" in dep or "M2-05" in dep or "心脏条" in dep),
}


def ruleA_dels(c):
    dels = set()
    hits = {}
    for u in UNIT_OF[c]:
        if LAYER[c].get(u, "") != A_SPEC["作用层"] or u in A_SPEC["排除单元"]:
            continue
        keys = A_SPEC["单元证候关键词"].get(u)
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
            hits[u] = "命中" + "、".join(matched[:3])
    return dels, hits


# ================= 候选B：R2 病程分期（规则级） =================
DELIM = "。；;，,、（）()：:\n"


def clause_of(text, kw):
    i = text.find(kw)
    if i < 0:
        return ""
    l = i
    while l > 0 and text[l - 1] not in DELIM:
        l -= 1
    r = i + len(kw)
    while r < len(text) and text[r] not in DELIM:
        r += 1
    return text[l:r]


def ruleB_neg(c, use_filter=True):
    t = SYM[c]
    out = []
    for kw in B_SPEC["负向关键词"]:
        if kw not in t:
            continue
        claw = clause_of(t, kw)
        if use_filter and any(m in claw for m in B_SPEC["非假设句标记"]):
            continue
        out.append(kw)
    return out


def ruleB_pos(c, allow_weak=False):
    t = SYM[c]
    strong = [kw for kw in B_SPEC["强正向关键词"] if kw in t]
    weak = [kw for kw in B_SPEC["弱正向关键词_不单独触发"] if kw in t]
    if strong:
        return strong, weak, True
    if allow_weak and weak:
        return strong, weak, True
    return strong, weak, False


def ruleB_stage(c, use_filter=True, allow_weak=False):
    neg = ruleB_neg(c, use_filter)
    if neg:
        return "急性期", neg, [], ""
    strong, weak, ok = ruleB_pos(c, allow_weak)
    if ok:
        return "恢复期", [], strong or weak, ""
    return "无法判定", [], [], "维持基线"


def build(delsets=None, recovery=None, tag=""):
    data = json.loads(json.dumps(PRED))
    changed = {}
    for c, dels in (delsets or {}).items():
        if not dels:
            continue
        rec = data[c]
        before = list(rec.get("主穴", []))
        pts = [p for p in before if not (normalize_units([p]) and next(iter(normalize_units([p]))) in dels)]
        if pts == before:
            continue
        rec["主穴"] = pts
        lay = rec.get("主穴分层") or {}
        for k in list(lay.keys()):
            lay[k] = [x for x in lay[k] if not (normalize_units([x]) and next(iter(normalize_units([x]))) in dels)]
        rec["主穴分层"] = lay
        rec["主穴记录"] = [e for e in (rec.get("主穴记录") or []) if str(e.get("穴", "")).strip() not in dels]
        rec["推理要点"] = str(rec.get("推理要点", "")) + "\n【候选A·八脉分流】无对应证候者降备选：%s。" % "、".join(sorted(dels))
        changed.setdefault(c, {})["候选A删"] = sorted(dels)
    for c in (recovery or []):
        rec = data[c]
        before = list(rec.get("主穴", []))
        pts = [p for p in before if p != "太冲"]
        if "足三里" not in pts:
            idx = before.index("太冲") if "太冲" in before else len(pts)
            pts.insert(min(idx, len(pts)), "足三里")
        rec["主穴"] = pts
        lay = rec.get("主穴分层") or {}
        for k in list(lay.keys()):
            lay[k] = [x for x in lay[k] if x != "太冲"]
        lay.setdefault("对症", [])
        if "足三里" not in lay["对症"]:
            lay["对症"].append("足三里")
        rec["主穴分层"] = lay
        rec["主穴记录"] = [e for e in (rec.get("主穴记录") or []) if str(e.get("穴", "")).strip() != "太冲"]
        if not any(str(e.get("穴", "")).strip() == "足三里" for e in rec["主穴记录"]):
            rec["主穴记录"].append({"穴": "足三里", "层": "对症",
                                    "依据": "利水后转补脾胃（候选B·R2 恢复期）", "出处": "教程_utf8 第4065/4529行",
                                    "备注": "候选·未合入"})
        rec["推理要点"] = str(rec.get("推理要点", "")) + "\n【候选B·分期】恢复期：去太冲、补足三里（维持 8 穴）。"
        changed.setdefault(c, {})["候选B恢复期"] = True
    out = os.path.join(HERE, "_blind93_pcZ%s_results.json" % tag)
    json.dump(data, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out, hashlib.sha256(open(out, "rb").read()).hexdigest(), changed


def evalset(pred):
    per = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        G2 = GOLD[c]
        t = len(P & G2)
        rc = t / len(G2) if G2 else 0.0
        pr = t / len(P) if P else 0.0
        per[c] = dict(P=P, tp=t, fp=len(P - G2), fn=len(G2 - P),
                      f1=(2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0),
                      jac=(t / len(P | G2) if (P | G2) else 0.0))
    return per


def blk(per, cids):
    return dict(TP=sum(per[c]["tp"] for c in cids), FP=sum(per[c]["fp"] for c in cids),
                FN=sum(per[c]["fn"] for c in cids),
                F1=round(statistics.mean([per[c]["f1"] for c in cids]), 4),
                Jac=round(statistics.mean([per[c]["jac"] for c in cids]), 4))


PER_BASE = evalset(PRED)
ref = json.load(io.open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))["全量86"]["v14r5"]
b86 = blk(PER_BASE, SC)
selfcheck = b86["TP"] == ref["TP"] and b86["FP"] == ref["FP"] and b86["FN"] == ref["FN"] and abs(b86["F1"] - ref["F1"]) < 1e-9

# ---------- 规则级执行 ----------
A_dels, A_hits = {}, {}
for c in SC:
    d, h = ruleA_dels(c)
    if d:
        A_dels[c] = d
        A_hits[c] = h

# 全 86 案扫描（不预设适用案集）
B_scan = {c: ruleB_stage(c) for c in SC}
B_recovery = [c for c in SC if B_scan[c][0] == "恢复期"]
B_acute = [c for c in SC if B_scan[c][0] == "急性期"]
FLW = set(B_SPEC["适用案集"])
B_over = [c for c in B_recovery if c not in FLW]

# 稳健性矩阵
ROBUST = {}
for filt in (True, False):
    for weak in (False, True):
        rec = [c for c in SC if ruleB_stage(c, filt, weak)[0] == "恢复期"]
        ROBUST["filter=%s,weak=%s" % (filt, weak)] = rec

# ---- 候选B-v2：精简强正向词表（移除过泛词 足溫 / 雙足溫）----
B2_STRONG = [k for k in B_SPEC["强正向关键词"] if k not in ("足溫", "雙足溫")]


def ruleB2_stage(c, use_filter=True):
    if ruleB_neg(c, use_filter):
        return "急性期"
    if [k for k in B2_STRONG if k in SYM[c]]:
        return "恢复期"
    return "无法判定"


B2_all = [c for c in SC if ruleB2_stage(c) == "恢复期"]
B2_over = [c for c in B2_all if c not in FLW]
B2_flw = [c for c in B_SPEC["适用案集"] if ruleB2_stage(c) == "恢复期"]

RUNS = [("候选A·八脉分流（规则级）", A_dels, []),
        ("候选B·R2分期（规则级，含非假设句过滤+强正向）", {}, [c for c in B_SPEC["适用案集"] if ruleB_stage(c)[0] == "恢复期"]),
        ("候选B-v2·R2分期（精简词表：删 足溫/雙足溫）", {}, B2_flw),
        ("候选A+候选B-v2（规则级组合）", A_dels, B2_flw)]

summary = {"selfcheck": selfcheck, "base": b86,
           "ruleA_trigger_cases": sorted(A_dels), "ruleA_hits": {k: v for k, v in A_hits.items()},
           "ruleB_scan_recovery": B_recovery, "ruleB_scan_acute": B_acute, "ruleB_over_trigger": B_over,
           "ruleB2_chain_recovery": B2_flw, "ruleB2_over_trigger": B2_over,
           "robustness": ROBUST, "runs": {}}

lines = ["# P-C‴ 规则级复核（读取 `候选规则_条文化.json` 执行，唯一真相源）", "",
         "- 自检（基线 vs 官方 `判分汇总v14r5.json`）：**%s**" % ("PASS" if selfcheck else "FAIL"),
         "- 评分：`benchmark_v2/canonical_scorer.py`", "",
         "## 1. 候选A（八脉交会分流）规则级触发（全 86 案扫描）", "",
         "- 触发案 %d 个，共删 %d 穴" % (len(A_dels), sum(len(v) for v in A_dels.values())), "",
         "| 案号 | 链 | 删穴 |", "|---|---|---|"]
for c in sorted(A_dels):
    lines.append("| %s | %s | %s |" % (c, CHAIN.get(c, ""), "、".join(sorted(A_dels[c]))))
lines += ["", "## 2. 候选B（R2 分期）规则级扫描（**不预设适用案集**）", "",
          "- 全 86 案中判定『恢复期』：%s" % ("、".join(B_recovery) if B_recovery else "—"),
          "- 全 86 案中判定『急性期』：%s" % ("、".join(B_acute) if B_acute else "—"),
          "- **超出适用案集（140 链 9 案）的误触发案**：%s" % ("、".join(B_over) if B_over else "**0（无）**"), "",
          "| 案号 | 链 | 判定 | 负向命中 | 正向命中 |", "|---|---|---|---|---|"]
for c in SC:
    st, neg, pos, _ = B_scan[c]
    if st == "无法判定" and c not in FLW:
        continue
    lines.append("| %s | %s | %s | %s | %s |" % (c, CHAIN.get(c, ""), st, "、".join(neg) or "—", "、".join(pos) or "—"))
lines += ["", "## 3. 稳健性矩阵（候选B 恢复期案集）", "",
          "| 口径 | 恢复期案 |", "|---|---|"]
for k, v in ROBUST.items():
    lines.append("| %s | %s |" % (k, "、".join(v) if v else "—"))
lines += ["", "## 3b. 词表精简对照（候选B-v2：删 足溫/雙足溫）", "",
          "- 候选B（含 足溫/雙足溫）——全 86 案『恢复期』%d 案，其中**超出 140 链的误触发 %d 案**" % (len(B_recovery), len(B_over)),
          "- 候选B-v2（删 足溫/雙足溫）——全 86 案『恢复期』%d 案，其中**超出 140 链的误触发 %d 案**" % (len(B2_all), len(B2_over)),
          "- 140 链内恢复期：B=%s；B-v2=%s" % ("、".join([c for c in B_SPEC["适用案集"] if ruleB_stage(c)[0] == "恢复期"]), "、".join(B2_flw)),
          "- 误触发案（B-v2 残留）：%s" % ("、".join(B2_over) if B2_over else "**0（无）**"), ""]
lines += ["", "## 4. 规则级重跑结果（Δ = 规则级 − v14r5 基线）", ""]

for tag, dels, rec in RUNS:
    out, h, changed = build(dels, rec, "_" + tag.split("·")[0].replace("候选", ""))
    PER = evalset(json.load(io.open(out, encoding="utf-8")))
    rows = []
    for name, cids in LAYERS:
        b, r = blk(PER_BASE, cids), blk(PER, cids)
        rows.append(dict(分层=name, 案数=len(cids), TP_b=b["TP"], TP_r=r["TP"], FP_b=b["FP"], FP_r=r["FP"],
                         FN_b=b["FN"], FN_r=r["FN"], F1_b=b["F1"], F1_r=r["F1"],
                         F1_d=round(r["F1"] - b["F1"], 4)))
    d = rows[0]
    side = []
    for c in changed:
        dtp = PER[c]["tp"] - PER_BASE[c]["tp"]
        dfp = PER[c]["fp"] - PER_BASE[c]["fp"]
        if dtp < 0 or dfp > 0:
            side.append("%s(TP%+d,FP%+d)" % (c, dtp, dfp))
    summary["runs"][tag] = {"sha256": h, "rows": rows, "side": side, "changed": changed,
                            "dTP": d["TP_r"] - d["TP_b"], "dFP": d["FP_r"] - d["FP_b"],
                            "dF1": d["F1_d"], "dF1_64": rows[1]["F1_d"]}
    lines += ["### %s" % tag, "", "- sha256: `%s`" % h,
              "- **ΔTP %+d / ΔFP %+d / ΔF1 %+.4f / ΔF1(64) %+.4f**；副作用案：%s"
              % (d["TP_r"] - d["TP_b"], d["FP_r"] - d["FP_b"], d["F1_d"], rows[1]["F1_d"],
                 "、".join(side) if side else "0"),
              "", "| 分层 | 案数 | TP | FP | FN | F1 (Δ) |", "|---|---:|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %d→%d | %d→%d | %d→%d | %.4f→%.4f (%+.4f) |"
                     % (r["分层"], r["案数"], r["TP_b"], r["TP_r"], r["FP_b"], r["FP_r"],
                        r["FN_b"], r["FN_r"], r["F1_b"], r["F1_r"], r["F1_d"]))
    lines.append("")

lines += ["## 5. 与预测级 patch 结果对照（一致性检验）", "",
          "| 候选 | 预测级 patch（P-C′/P-C″） | 规则级（本引擎） | 一致? |", "|---|---|---|---|",
          "| 八脉分流 C1b′ | ΔTP +0 / ΔFP −13 / ΔF1 +0.0038 | 见上『候选A』行 | — |",
          "| R2 分期（L 口径） | ΔTP +3 / ΔFP −3 / ΔF1 +0.0034 | 见上『候选B』行 | — |"]
lines.append("")

io.open(os.path.join(HERE, "PCz_规则级判分汇总.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=2))
io.open(os.path.join(HERE, "PCz_规则级复核.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

print("self-check:", "PASS" if selfcheck else "FAIL")
print("候选A 触发案 %d 删穴 %d" % (len(A_dels), sum(len(v) for v in A_dels.values())))
print("候选B 全86扫描: 恢复期 %s | 误触发 %s" % (B_recovery, B_over or "0"))
print("候选B 稳健性:", {k: v for k, v in ROBUST.items()})
for tag in summary["runs"]:
    s = summary["runs"][tag]
    print("%s | ΔTP %+d ΔFP %+d ΔF1 %+.4f ΔF1_64 %+.4f | 副作用 %s"
          % (tag, s["dTP"], s["dFP"], s["dF1"], s["dF1_64"], s["side"] or "0"))
sys.exit(0 if selfcheck else 1)
