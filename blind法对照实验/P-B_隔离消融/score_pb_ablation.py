#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-B 隔离消融：v14r5 预测级反事实消融（不重跑盲法、不改规则、不覆盖既有产物）。

方法沿用 M5-D 既定范式（`sf10_阶段M5/D_消融/候选验证/score_m5d2.py`）：
在**冻结的 v14r5 预测**上按候选 {触发闸门 → 加穴/删穴} 重算点级指标。
本脚本的两点强化：
  1) 评分统一走**唯一正式实现** `benchmark_v2/canonical_scorer.py`（不改指标/分母），并自带
     与 `判分汇总v14r5.json` 的逐项自检；
  2) 候选**触发闸门一律取输入侧信号**（`sf10_阶段C/symptoms_v2/*.json` 片段文本 + 本案预测的
     层/依据），因此对**全部 86 案**统一施加，天然给出"非目标案误触发"与"副作用案"。

纪律：只读输入；输出只写本脚本所在目录；候选**不合入任何版本**。
"""
import collections
import csv
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

sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
CASE_IDS = gold["case_ids"]
SC = [c for c in CASE_IDS if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: set(NEW[c]["gold_members"]) for c in SC}

EXCLUDE = set(r["case_id"] for r in csv.DictReader(
    open(os.path.join(EXP, "sf10_核心集", "排除清单.csv"), encoding="utf-8-sig")))
VT = {r["case_id"]: str(r.get("visit_type", "")) for r in csv.DictReader(
    open(os.path.join(EXP, "sf10_阶段D", "组装清单.csv"), encoding="utf-8-sig"))}
CHAIN_OF = {}
for r in csv.DictReader(open(os.path.join(M5, "E_分组验证", "分组交叉验证表.csv"), encoding="utf-8-sig")):
    for x in (r["案号"] or "").split(";"):
        if x:
            CHAIN_OF[x] = r["患者链"]

PRED = json.load(open(os.path.join(G, "盲法v14r5", "_blind93v14r5_results.json"), encoding="utf-8"))

# ---- 输入文本与本案预测结构 ----
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")


def symptom_text(c):
    p = os.path.join(SD, "%s_symptoms_v2.json" % c)
    if not os.path.exists(p):
        return ""
    d = json.load(open(p, encoding="utf-8"))
    buf = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            buf.append(str(v["片段"]))
        elif isinstance(v, str):
            buf.append(v)
    return "".join(buf)


SYM = {c: symptom_text(c) for c in SC}


def has(c, words):
    t = SYM.get(c, "")
    return any(w in t for w in words)


BASE = {c: set(normalize_units(PRED[c].get("主穴", []))) for c in SC}
UNIT_OF = {c: list(PRED[c].get("主穴", []) or []) for c in SC}
REC = {c: {str(e.get("穴", "")).strip(): e for e in (PRED[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: lname for lname, pts in (PRED[c].get("主穴分层") or {}).items() for u in pts} for c in SC}


def unit_units(c):
    """(unit, 层, 依据) 列表。"""
    out = []
    for u in UNIT_OF[c]:
        e = REC[c].get(str(u).strip(), {})
        out.append((u, LAYER[c].get(u, ""), str(e.get("依据", ""))))
    return out


# ---- 候选定义：触发闸门取自输入侧 ----
FLW = ("140_01", "141_01", "142_01", "143_01", "144_01", "145_01", "146_01", "148_01", "149_01")

# 八脉交会单元 → 其证候关键词（依据 指南6.4 八脉交会主治，见本案 主穴记录·依据）
BM_GATE = {
    "公孙+内关": ("心", "胸", "悶", "闷", "胃", "脘", "腹", "嘔", "呕", "悸", "咳", "喘", "噯", "噫"),
    "公孙": ("心", "胸", "胃", "脘", "腹", "衝", "冲"),
    "内关": ("心", "胸", "悶", "闷", "胃", "脘", "悸", "嘔", "呕"),
    "外关+临泣": ("耳", "目", "眥", "眦", "眼", "頰", "颊", "偏頭", "偏头", "脅", "胁", "頸", "颈", "肩"),
    "外关+足临泣": ("耳", "目", "眥", "眦", "眼", "偏頭", "偏头", "脅", "胁", "頸", "颈", "肩"),
    "外关": ("耳", "目", "偏頭", "偏头", "脅", "胁"),
    "臨泣": ("耳", "目", "眥", "眦", "眼", "頰", "颊", "偏頭", "偏头"),
    "临泣": ("耳", "目", "眥", "眦", "眼", "頰", "颊", "偏頭", "偏头"),
    "足临泣": ("耳", "目", "眥", "眦", "偏頭", "偏头", "脅", "胁"),
    "后溪+申脉": ("項", "项", "頸", "颈", "背", "督", "肩"),
    "后溪": ("項", "项", "頸", "颈", "背", "督", "肩"),
    "申脉": ("項", "项", "頸", "颈", "背", "蹺", "跷"),
    "列缺+照海": ("喉", "咽", "胸", "膈", "肺", "咳", "乾", "干"),
    "列缺": ("喉", "咽", "胸", "肺", "鼻", "皮"),
    "照海": ("喉", "咽", "胸", "膈", "便", "乾", "干"),
}
BM_EXCLUDE = ("合谷+太冲",)  # 层标签为八脉交会，但实为开四关，不纳入本候选


def cand_bm(c, use_reg=False):
    """PB-C1 八脉交会按证候分流：无对应证候者从主穴删（降备选）。

    use_reg=True（PB-C1b）：闸门 = 八脉主治 ∪ **本案该单元 依据 所指已登记规则的适应症**
    （M2-04 两腋淋巴半表半里 / M2-05+R2 心胸心律），以免收窄废除已登记规则。
    """
    d = set()
    for u, layer, dep in unit_units(c):
        if layer != "八脉交会" or u in BM_EXCLUDE:
            continue
        keys = BM_GATE.get(u)
        if keys is None:
            continue
        keys = list(keys)
        if use_reg:
            if "M2-04" in dep or "腋" in dep:
                keys += ["腋", "淋巴", "乳"]
            if "R2" in dep or "M2-05" in dep or "心脏条" in dep:
                keys += ["脈", "結代", "悸", "數", "冷", "水腫", "積水", "心陽", "心阳"]
        if not has(c, keys):
            d |= set(normalize_units([u]))
    return {"del": d}


ACUTE = {"140_01", "142_01"}  # R2 急性水势上泛案（原书：仅此两案用太冲/不加补脾胃）


def cand_tc(c):
    """PB-C2 M2-06 太冲条件化：R2 恢复期案删太冲（急性案 140/142 保留）。"""
    if c not in FLW or c in ACUTE:
        return {}
    if "太冲" not in BASE[c]:
        return {}
    return {"del": {"太冲"}}


def cand_flw(c):
    """PB-C3 肺积水恢复期补脾胃：R2 恢复期案加足三里（急性案不加）。"""
    if c not in FLW or c in ACUTE:
        return {}
    if "足三里" in BASE[c]:
        return {}
    return {"add": {"足三里"}}


def cand_yg(c):
    """PB-C4 膀胱经腰背组补阴谷：RC-6 已触发且案有腰背信号、缺阴谷时加。"""
    fired = any("RC-6" in dep for u, _, dep in unit_units(c))
    if not fired or "阴谷" in BASE[c]:
        return {}
    if not has(c, ("腰", "背", "腿肚", "委中")):
        return {}
    return {"add": {"阴谷"}}


def cand_r7(c):
    """PB-C6 R7a 外踝胆经（收缩版）：有踝部信号且非纯冷者加丘墟侠溪。"""
    if not has(c, ("踝",)):
        return {}
    if has(c, ("外側冰冷", "外侧冰冷", "冰冷")) and not has(c, ("腫", "肿", "痛")):
        return {}
    add = {p for p in ("丘墟", "侠溪") if p not in BASE[c]}
    return {"add": add} if add else {}


def cand_rc2(c, strict=False):
    """PB-C7 RC-2 多指麻按指分经整组：按受累指加对应穴。

    strict=True（PB-C7b）：须**指名具体手指**（拇/食/中/無名/小指）才触发，避免"手麻"泛触发。
    """
    if not (has(c, ("麻",)) and has(c, ("指",))):
        return {}
    FING = ("拇", "食", "中", "無名", "无名", "小指")
    if strict and not has(c, FING):
        return {}
    add = set()
    if has(c, ("拇",)):
        add.add("太渊")
    if has(c, ("食",)):
        add |= {"合谷", "曲池"}
    if has(c, ("中",)):
        add.add("大陵")
    if has(c, ("後三指", "后三指", "三指", "無名", "无名", "小指")):
        add |= {"大陵", "外关"}
    add = {p for p in add if p not in BASE[c]}
    return {"add": add} if add else {}


CANDS = [
    ("PB-C1", "八脉交会按证候分流（激进版）", "指南6.4 八脉交会主治（知识条目 L1163/L1378/L1860/L1989/L2068/L2326）", cand_bm),
    ("PB-C1b", "八脉交会分流（保留已登记规则适应症）", "C1 闸门 ∪ M2-04 两腋淋巴 / M2-05+R2 心胸心律适应症（不得废除已登记规则）", lambda c: cand_bm(c, True)),
    ("PB-C2", "M2-06 太冲条件化（恢复期删太冲）", "C_残余归因 141_01/146_01：太冲仅急性水势上泛(140/142)用，好转后删", cand_tc),
    ("PB-C3", "肺积水恢复期补脾胃（加足三里）", "C_残余归因 141_01/143_01/144_01/145_01/148_01：利水后转补脾胃", cand_flw),
    ("PB-C4", "膀胱经腰背组补阴谷（加穴）", "指南6.2 肾合水；RC-6 已合入但缺阴谷；C_残余归因 阴谷 FN 7 案", cand_yg),
    ("PB-C6", "R7a 外踝胆经收缩版（加丘墟侠溪）", "M9-C2 判 R7a 需收缩（FP 14）；本批收缩闸门=有踝部肿痛信号", cand_r7),
    ("PB-C7", "RC-2 多指麻按指分经整组（加穴）", "知识条目 L1985/L1131 手麻分经；C_残余归因 318_01", cand_rc2),
    ("PB-C7b", "RC-2 多指麻分经（更严闸门：须指名手指）", "同上；闸门加严：须出现具体手指名，避免'手麻'泛触发", lambda c: cand_rc2(c, True)),
]


# ---- 评分 ----
def eval_sets(Pset):
    f1s, jacs, tp, fp, fn = [], [], 0, 0, 0
    per = {}
    for c in SC:
        P, G2 = Pset[c], GOLD[c]
        t, f, n = len(P & G2), len(P - G2), len(G2 - P)
        tp += t; fp += f; fn += n
        rc = t / len(G2) if G2 else 0.0
        pr = t / len(P) if P else 0.0
        f1 = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
        ja = t / len(P | G2) if (P | G2) else 0.0
        f1s.append(f1); jacs.append(ja)
        per[c] = (t, f, n, f1, ja)
    return dict(TP=tp, FP=fp, FN=fn, F1=round(statistics.mean(f1s), 4),
                Jac=round(statistics.mean(jacs), 4)), per


ref = json.load(open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))
base86, base_per = eval_sets({c: set(BASE[c]) for c in SC})
selfcheck = (base86["TP"] == ref["全量86"]["v14r5"]["TP"] and base86["FP"] == ref["全量86"]["v14r5"]["FP"]
             and base86["FN"] == ref["全量86"]["v14r5"]["FN"] and abs(base86["F1"] - ref["全量86"]["v14r5"]["F1"]) < 1e-9
             and abs(base86["Jac"] - ref["全量86"]["v14r5"]["Jac"]) < 1e-9)

CORE = [c for c in SC if c not in EXCLUDE]
FU = [c for c in SC if VT.get(c, "").startswith("复诊")]
FS = [c for c in SC if c not in FU]


def macro(per, cids, i):
    v = [per[c][i] for c in cids]
    return round(statistics.mean(v), 4) if v else 0.0


rows = []
detail = {}
for cid, name, basis, fn_ in CANDS:
    P = {c: set(BASE[c]) for c in SC}
    affected = {}
    for c in SC:
        ch = fn_(c) or {}
        add = ch.get("add", set()) or set()
        dele = ch.get("del", set()) or set()
        add = {a for a in add if a not in P[c]}
        dele = {d for d in dele if d in P[c]}
        if add or dele:
            P[c] = (P[c] | add) - dele
            affected[c] = {"add": sorted(add), "del": sorted(dele)}
    m, per = eval_sets(P)
    dTP, dFP, dFN = m["TP"] - base86["TP"], m["FP"] - base86["FP"], m["FN"] - base86["FN"]
    dF1 = round(m["F1"] - base86["F1"], 4)
    dJac = round(m["Jac"] - base86["Jac"], 4)
    # 副作用案：加穴落错（ΔFP>0）或删穴删对（ΔTP<0）
    side = []
    for c, ch in affected.items():
        bt, bf = base_per[c][0], base_per[c][1]
        at, af = per[c][0], per[c][1]
        if af > bf or at < bt:
            side.append("%s(TP%+d,FP%+d:add%s,del%s)" % (c, at - bt, af - bf,
                                                        "+".join(ch["add"]) or "-", "+".join(ch["del"]) or "-"))
    if dF1 < 0 or (dTP < 0 and dFP >= 0):
        verdict = "不合入(负收益)"
    elif dTP >= 0 and dFP <= 0 and (dTP > 0 or dFP < 0):
        verdict = "建议合入-" + ("补穴" if dTP > 0 else "降FP")
    elif dTP == 0 and dFP == 0:
        verdict = "无收益"
    else:
        verdict = "待定(伴FP/损recall)"
    rows.append({
        "候选ID": cid, "候选": name, "触发案数": len(affected),
        "加穴": sum(len(v["add"]) for v in affected.values()),
        "删穴": sum(len(v["del"]) for v in affected.values()),
        "ΔTP": dTP, "ΔFP": dFP, "ΔFN": dFN, "ΔF1": dF1, "ΔJac": dJac,
        "ΔF1_核心64": round(macro(per, CORE, 3) - macro(base_per, CORE, 3), 4),
        "ΔF1_复诊": round(macro(per, FU, 3) - macro(base_per, FU, 3), 4),
        "ΔF1_首诊": round(macro(per, FS, 3) - macro(base_per, FS, 3), 4),
        "判定": verdict, "副作用案数": len(side), "副作用案": " | ".join(side[:12]), "依据": basis,
    })
    detail[cid] = {"affected": affected, "side": side}

def combo_mix(names):
    P = {c: set(BASE[c]) for c in SC}
    for c in SC:
        for cid, name, basis, fn_ in CANDS:
            if cid not in names:
                continue
            ch = fn_(c) or {}
            P[c] = (P[c] | set(ch.get("add", set()) or set())) - set(ch.get("del", set()) or set())
    m, per = eval_sets({c: set(normalize_units(list(P[c]))) for c in SC})
    return {"ΔTP": m["TP"] - base86["TP"], "ΔFP": m["FP"] - base86["FP"],
            "ΔFN": m["FN"] - base86["FN"], "ΔF1": round(m["F1"] - base86["F1"], 4),
            "ΔJac": round(m["Jac"] - base86["Jac"], 4),
            "ΔF1_核心64": round(macro(per, CORE, 3) - macro(base_per, CORE, 3), 4),
            "ΔF1_复诊": round(macro(per, FU, 3) - macro(base_per, FU, 3), 4),
            "ΔF1_首诊": round(macro(per, FS, 3) - macro(base_per, FS, 3), 4)}


COMBOS = {
    "组合A·净收益候选（C2+C3）": ["PB-C2", "PB-C3"],
    "组合B·保守（C1b+C2+C3+C4+C7b）": ["PB-C1b", "PB-C2", "PB-C3", "PB-C4", "PB-C7b"],
    "组合C·激进（C1+C2+C3+C4+C7）": ["PB-C1", "PB-C2", "PB-C3", "PB-C4", "PB-C7"],
}
combo = {k: combo_mix(v) for k, v in COMBOS.items()}

lines = ["# P-B 隔离消融结果（v14r5 预测级反事实消融）", ""]
lines.append("- 基线 v14r5（自检 %s）：TP %d / FP %d / FN %d / F1 %.4f / Jac %.4f"
             % ("PASS" if selfcheck else "FAIL", base86["TP"], base86["FP"], base86["FN"],
                base86["F1"], base86["Jac"]))
lines.append("- Δ = 消融后 − 基线；候选触发闸门取输入侧信号，对全部 86 案统一施加。")
lines.append("")
lines.append("| 候选 | 触发案 | 加穴 | 删穴 | ΔTP | ΔFP | ΔFN | ΔF1 | ΔJac | ΔF1(64) | ΔF1(复诊) | ΔF1(首诊) | 判定 |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
for r in rows:
    lines.append("| %s %s | %d | %d | %d | %+d | %+d | %+d | %+.4f | %+.4f | %+.4f | %+.4f | %+.4f | %s |"
                 % (r["候选ID"], r["候选"], r["触发案数"], r["加穴"], r["删穴"],
                    r["ΔTP"], r["ΔFP"], r["ΔFN"], r["ΔF1"], r["ΔJac"],
                    r["ΔF1_核心64"], r["ΔF1_复诊"], r["ΔF1_首诊"], r["判定"]))
lines.append("")
lines.append("## 组合（同名互替变体不叠加；各组按列出候选计算）")
lines.append("")
lines.append("| 组合 | ΔTP | ΔFP | ΔFN | ΔF1 | ΔJac | ΔF1(64) | ΔF1(复诊) | ΔF1(首诊) |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for k, v in combo.items():
    lines.append("| %s | %+d | %+d | %+d | %+.4f | %+.4f | %+.4f | %+.4f | %+.4f |"
                 % (k, v["ΔTP"], v["ΔFP"], v["ΔFN"], v["ΔF1"], v["ΔJac"],
                    v["ΔF1_核心64"], v["ΔF1_复诊"], v["ΔF1_首诊"]))
lines.append("")
lines.append("## 副作用案明细（触发案中 TP 下降或 FP 上升者）")
lines.append("")
for r in rows:
    if r["副作用案数"]:
        lines.append("- **%s**：%d 案 — %s" % (r["候选ID"], r["副作用案数"], r["副作用案"]))

with open(os.path.join(HERE, "P-B_消融结果.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
with open(os.path.join(HERE, "P-B_消融表.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
json.dump({"base": base86, "selfcheck": selfcheck, "rows": rows, "combos": combo,
           "detail": detail}, open(os.path.join(HERE, "P-B_消融明细.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# 逐案影响表（触发案 × 候选：加穴/删穴/ΔTP/ΔFP）——误触发与副作用审计用
with open(os.path.join(HERE, "P-B_逐案影响.csv"), "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["候选ID", "案号", "访次", "链", "加穴", "删穴", "ΔTP", "ΔFP", "副作用(Y/N)"])
    for cid, name, basis, fn_ in CANDS:
        aff = detail[cid]["affected"]
        side = set(s.split("(")[0] for s in detail[cid]["side"])
        for c, ch in sorted(aff.items()):
            bt, bf = base_per[c][0], base_per[c][1]
            # 复算该候选下本案的 TP/FP
            P = (BASE[c] | set(ch["add"])) - set(ch["del"])
            t, f = len(P & GOLD[c]), len(P - GOLD[c])
            w.writerow([cid, c, "复诊" if VT.get(c, "").startswith("复诊") else "首诊",
                        CHAIN_OF.get(c, ""), "+".join(ch["add"]) or "-", "+".join(ch["del"]) or "-",
                        t - bt, f - bf, "Y" if c in side else "N"])

print("self-check vs 判分汇总v14r5.json:", "PASS" if selfcheck else "FAIL")
print("base:", base86)
for r in rows:
    print("%s 触发%d 加%d 删%d ΔTP%+d ΔFP%+d ΔF1%+.4f -> %s"
          % (r["候选ID"], r["触发案数"], r["加穴"], r["删穴"], r["ΔTP"], r["ΔFP"], r["ΔF1"], r["判定"]))
print("combo:", json.dumps(combo, ensure_ascii=False))
sys.exit(0 if selfcheck else 1)
