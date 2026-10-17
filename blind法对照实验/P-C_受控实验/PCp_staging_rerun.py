#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-C′：显式分期信号清单的分期 → 受控 patch 重跑（三口径对照）。

变体：
  L（literal）        负向优先的字面应用 → 恢复期 {144,145,148}
  C（context）        142「腫上去」属假设句不计 → 恢复期 {142,144,145,148}（= 独立盲法判定口径）
  A（登记分期，对照）  P-C 的 C_残余归因原案对照 → 恢复期 {141,143,144,145,146,148,149}
范式同 M10-1/M11-1/M12-1/M12-2；唯一正式评分器；只读输入，输出只写本目录。
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

# ---------- 显式信号清单 ----------
NEG = ["仍水腫", "仍有水腫", "仍腫", "未退", "水腫未退",
       "腫向上", "腫更大", "腫上去", "向上且腫",
       "須坐起", "須要坐起", "坐起睡",
       "仍有積水", "肺中仍有積水"]
POS = ["水開始退", "水退", "水腫好轉", "好轉中",
       "持續往下退", "往下退", "向下退",
       "可平躺", "能平躺", "可以平躺",
       "雙足溫", "足溫", "比以前溫", "較溫",
       "心陽回頭"]
FLW = ["140_01", "141_01", "142_01", "143_01", "144_01", "145_01", "146_01", "148_01", "149_01"]
# 142 的「腫上去」出现在假设/警示句（非当前症情直述）→ context 口径将其排除
NEG_CONTEXT_EXEMPT = {"142_01": ["腫上去"]}


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


def staging(c, context=False):
    t = SYM.get(c, "")
    neg = [w for w in NEG if w in t]
    if context and c in NEG_CONTEXT_EXEMPT:
        neg = [w for w in neg if w not in NEG_CONTEXT_EXEMPT[c]]
    pos = [w for w in POS if w in t]
    if neg:
        return "急性", neg, pos
    if pos:
        return "恢复", neg, pos
    return "无法判定", neg, pos


RECOVERY = {
    "L·literal（负向优先字面应用）": [c for c in FLW if staging(c)[0] == "恢复"],
    "C·context（142 假设句豁免）": [c for c in FLW if staging(c, context=True)[0] == "恢复"],
    "A·登记分期（对照，原案对照）": ["141_01", "143_01", "144_01", "145_01", "146_01", "148_01", "149_01"],
}

NEW_RECORD = {
    "穴": "足三里", "层": "对症",
    "依据": "胃经本穴属土，灸之强土；利水后转补脾胃（P-C′·R2/M2-06恢复期转折）",
    "出处": "教程_utf8 第4065/4529行", "备注": "P-C′候选·未合入",
}
NOTE = ("【P-C′ 受控 patch·显式分期信号】恢复期（命中正向水退信号且无负向水停信号）："
        "去太冲、改取足三里补脾胃（土制水）；主穴总量维持 8 穴。")


def build(recovery, tag):
    data = json.loads(json.dumps(PRED))
    changed = {}
    for cid in recovery:
        rec = data[cid]
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
            rec["主穴记录"].append(dict(NEW_RECORD))
        rec["推理要点"] = str(rec.get("推理要点", "")) + "\n" + NOTE
        cre = rec.get("临床参考建议")
        note = "太冲（急性水势上泛期引水下冲；恢复期让位）"
        if isinstance(cre, list):
            cre.append(note)
        elif isinstance(cre, str):
            rec["临床参考建议"] = cre + "\n" + note
        else:
            rec["临床参考建议"] = [note]
        changed[cid] = {"old": before, "new": pts}
    out = os.path.join(HERE, "_blind93_pcP%s_results.json" % tag)
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

summary = {"selfcheck": selfcheck, "staging": {}, "variants": {}}
lines = ["# P-C′ 显式分期信号清单 · 受控重跑（三口径对照）", "",
         "- 自检（基线 vs 官方 `判分汇总v14r5.json`）：**%s**" % ("PASS" if selfcheck else "FAIL"),
         "- 评分：`benchmark_v2/canonical_scorer.py`（唯一正式实现，未改指标/分母）", "",
         "## 1. 清单对 9 案的分期（确定性复算）", "",
         "| 案号 | 负向命中 | 正向命中 | L·字面判定 | C·语境判定 |", "|---|---|---|---|---|"]
for c in FLW:
    sL, negL, posL = staging(c)
    sC, _, _ = staging(c, context=True)
    summary["staging"][c] = {"literal": sL, "context": sC, "neg": negL, "pos": posL}
    lines.append("| %s | %s | %s | %s | %s |" % (c, "、".join(negL) or "—", "、".join(posL) or "—", sL, sC))
lines.append("")

for tag, rec in RECOVERY.items():
    out, h, changed = build(rec, "_" + tag.split("·")[0])
    PER = evalset(json.load(io.open(out, encoding="utf-8")))
    rows = []
    for name, cids in LAYERS:
        b, r = blk(PER_BASE, cids), blk(PER, cids)
        rows.append(dict(分层=name, 案数=len(cids), TP_b=b["TP"], TP_r=r["TP"], FP_b=b["FP"], FP_r=r["FP"],
                         FN_b=b["FN"], FN_r=r["FN"], F1_b=b["F1"], F1_r=r["F1"],
                         F1_d=round(r["F1"] - b["F1"], 4), Jac_d=round(r["Jac"] - b["Jac"], 4)))
    d = rows[0]
    side = []
    for c in sorted(changed):
        dtp = PER[c]["tp"] - PER_BASE[c]["tp"]
        dfp = PER[c]["fp"] - PER_BASE[c]["fp"]
        if dtp < 0 or dfp > 0:
            side.append("%s(TP%+d,FP%+d)" % (c, dtp, dfp))
    summary["variants"][tag] = {"sha256": h, "recovery": rec, "rows": rows, "side": side,
                                "dTP": d["TP_r"] - d["TP_b"], "dFP": d["FP_r"] - d["FP_b"],
                                "dF1": d["F1_d"], "dF1_64": rows[1]["F1_d"]}
    lines += ["## 2. %s" % tag, "", "- 恢复期案：%s" % "、".join(rec),
              "- sha256: `%s`" % h,
              "- **ΔTP %+d / ΔFP %+d / ΔF1 %+.4f / ΔF1(64) %+.4f**；副作用案：%s"
              % (d["TP_r"] - d["TP_b"], d["FP_r"] - d["FP_b"], d["F1_d"], rows[1]["F1_d"],
                 "、".join(side) if side else "0"),
              "", "| 分层 | 案数 | TP | FP | FN | F1 (Δ) |", "|---|---:|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %d→%d | %d→%d | %d→%d | %.4f→%.4f (%+.4f) |"
                     % (r["分层"], r["案数"], r["TP_b"], r["TP_r"], r["FP_b"], r["FP_r"],
                        r["FN_b"], r["FN_r"], r["F1_b"], r["F1_r"], r["F1_d"]))
    lines += ["", "| 案号 | 主穴 基线→重跑 | 该案 ΔTP | 该案 ΔFP |", "|---|---|---:|---:|"]
    for c in sorted(changed):
        lines.append("| %s | %s → %s | %+d | %+d |"
                     % (c, "、".join(changed[c]["old"]), "、".join(changed[c]["new"]),
                        PER[c]["tp"] - PER_BASE[c]["tp"], PER[c]["fp"] - PER_BASE[c]["fp"]))
    lines.append("")

io.open(os.path.join(HERE, "PCp_判分汇总.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=2))
io.open(os.path.join(HERE, "PCp_复算结果.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

print("self-check:", "PASS" if selfcheck else "FAIL")
for c in FLW:
    print("  %s  L=%s C=%s | neg=%s" % (c, summary["staging"][c]["literal"], summary["staging"][c]["context"],
                                        summary["staging"][c]["neg"]))
for tag in RECOVERY:
    s = summary["variants"][tag]
    print("%s | 恢复期 %d 案 | ΔTP %+d ΔFP %+d ΔF1 %+.4f ΔF1_64 %+.4f | 副作用 %s"
          % (tag, len(s["recovery"]), s["dTP"], s["dFP"], s["dF1"], s["dF1_64"], s["side"] or "0"))
sys.exit(0 if selfcheck else 1)
