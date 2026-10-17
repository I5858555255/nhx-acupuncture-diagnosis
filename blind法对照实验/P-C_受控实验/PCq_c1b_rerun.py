#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-C″：八脉交会分流候选（C1b）的受控 patch 重跑 + 221_01 核定后的修正版（C1b′）。

- C1b   ：P-B 原样闸门（自检须复现 P-B：ΔTP -1 / ΔFP -17 / ΔF1 +0.0054）
- C1b′  ：闸门关键词修正（后溪/申脉 增"腰/脊"；申脉 增"跟/踝/膀胱/阳跷/太阳/下肢/足外"）
范式同 M10-1/M11-1/M12-1/M12-2：冻结 v14r5 预测上仅改触发案，唯一正式评分器复算。
只读输入；输出只写本目录。
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
CASE_IDS = gold["case_ids"]
SC = [c for c in CASE_IDS if len(NEW[c]["gold_members"]) > 0]
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
BASE = {c: set(normalize_units(PRED[c].get("主穴", []))) for c in SC}
UNIT_OF = {c: list(PRED[c].get("主穴", []) or []) for c in SC}
REC = {c: {str(e.get("穴", "")).strip(): e for e in (PRED[c].get("主穴记录", []) or [])} for c in SC}
LAYER = {c: {u: lname for lname, pts in (PRED[c].get("主穴分层") or {}).items() for u in pts} for c in SC}

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


def has(c, words):
    t = SYM.get(c, "")
    return any(w in t for w in words)


def unit_units(c):
    out = []
    for u in UNIT_OF[c]:
        e = REC[c].get(str(u).strip(), {})
        out.append((u, LAYER[c].get(u, ""), str(e.get("依据", ""))))
    return out


# ---------- 闸门表 ----------
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
BM_EXCLUDE = ("合谷+太冲",)

# 221_01 核定后的关键词修正（原书：督脉/膀胱经/阳跷循行腰背；阳跷起于跟中）
FIX = {
    "后溪+申脉": ("腰", "脊"),
    "后溪": ("腰", "脊"),
    "申脉": ("腰", "脊", "跟", "踝", "陽蹻", "阳蹻", "太陽", "太阳", "膀胱", "下肢", "足外"),
}
BM_GATE_FIX = {k: tuple(list(v) + list(FIX.get(k, ()))) for k, v in BM_GATE.items()}


def cand_bm(c, gate, use_reg=True):
    d = set()
    for u, layer, dep in unit_units(c):
        if layer != "八脉交会" or u in BM_EXCLUDE:
            continue
        keys = gate.get(u)
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
    return d


def build(delsets, tag):
    data = json.loads(json.dumps(PRED))
    changed = {}
    for c, dels in delsets.items():
        if not dels:
            continue
        rec = data[c]
        before = list(rec.get("主穴", []))
        pts = [p for p in before if normalize_units([p]) and next(iter(normalize_units([p]))) not in dels]
        if pts == before:
            continue
        rec["主穴"] = pts
        lay = rec.get("主穴分层") or {}
        for k in list(lay.keys()):
            lay[k] = [x for x in lay[k] if not (normalize_units([x]) and next(iter(normalize_units([x]))) in dels)]
        rec["主穴分层"] = lay
        rec["主穴记录"] = [e for e in (rec.get("主穴记录") or [])
                          if str(e.get("穴", "")).strip() not in dels]
        rec["推理要点"] = (str(rec.get("推理要点", ""))
                          + "\n【P-C″ 八脉交会分流】无对应证候者降备选：%s。" % "、".join(sorted(dels)))
        cre = rec.get("临床参考建议")
        note = "、".join(sorted(dels)) + "（八脉交会无对应证候，降临床参考建议）"
        if isinstance(cre, list):
            cre.append(note)
        elif isinstance(cre, str):
            rec["临床参考建议"] = cre + "\n" + note
        else:
            rec["临床参考建议"] = [note]
        changed[c] = {"del": sorted(dels), "old": before, "new": pts}
    out = os.path.join(HERE, "_blind93_pcC1b%s_results.json" % tag)
    json.dump(data, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    return out, h, changed


D_A = {c: cand_bm(c, BM_GATE) for c in SC}
D_B = {c: cand_bm(c, BM_GATE_FIX) for c in SC}

oA, hA, chA = build(D_A, "")
oB, hB, chB = build(D_B, "_fix")


def evalset(pred):
    per = {}
    for c in SC:
        P = set(normalize_units(pred[c].get("主穴", [])))
        G2 = GOLD[c]
        t, f = len(P & G2), len(P - G2)
        rc = t / len(G2) if G2 else 0.0
        pr = t / len(P) if P else 0.0
        f1 = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
        ja = t / len(P | G2) if (P | G2) else 0.0
        per[c] = dict(P=P, tp=t, fp=f, fn=len(G2 - P), recall=rc, prec=pr, f1=f1, jac=ja)
    return per


def blk(per, cids):
    return dict(TP=sum(per[c]["tp"] for c in cids), FP=sum(per[c]["fp"] for c in cids),
                FN=sum(per[c]["fn"] for c in cids),
                R=round(statistics.mean([per[c]["recall"] for c in cids]), 4),
                P=round(statistics.mean([per[c]["prec"] for c in cids]), 4),
                F1=round(statistics.mean([per[c]["f1"] for c in cids]), 4),
                Jac=round(statistics.mean([per[c]["jac"] for c in cids]), 4))


PER_BASE = evalset(PRED)
ref = json.load(io.open(os.path.join(G, "判分汇总v14r5.json"), encoding="utf-8"))["全量86"]["v14r5"]
base86 = blk(PER_BASE, SC)
selfcheck = (base86["TP"] == ref["TP"] and base86["FP"] == ref["FP"] and base86["FN"] == ref["FN"]
             and abs(base86["F1"] - ref["F1"]) < 1e-9)

VARIANTS = [("C1b（P-B 原样闸门）", PRED_ish := json.load(io.open(oA, encoding="utf-8")), chA, hA),
            ("C1b′（221_01 核定后修正闸门）", json.load(io.open(oB, encoding="utf-8")), chB, hB)]

summary = {"selfcheck": selfcheck, "base": base86, "variants": {}}
lines = ["# P-C″ 八脉交会分流 · 受控重跑（C1b vs C1b′）", "",
         "- 自检（基线 vs 官方 `判分汇总v14r5.json`）：**%s**" % ("PASS" if selfcheck else "FAIL"),
         "- 评分：`benchmark_v2/canonical_scorer.py`（唯一正式实现，未改指标/分母）", ""]

for tag, run, changed, h in VARIANTS:
    PER = evalset(run)
    rows = []
    for name, cids in LAYERS:
        b, r = blk(PER_BASE, cids), blk(PER, cids)
        rows.append(dict(分层=name, 案数=len(cids), TP_b=b["TP"], TP_r=r["TP"], FP_b=b["FP"], FP_r=r["FP"],
                         FN_b=b["FN"], FN_r=r["FN"], F1_b=b["F1"], F1_r=r["F1"],
                         F1_d=round(r["F1"] - b["F1"], 4), Jac_d=round(r["Jac"] - b["Jac"], 4)))
    del86 = rows[0]
    summary["variants"][tag] = {"sha256": h, "rows": rows,
                                "changed": changed,
                                "dTP": del86["TP_r"] - del86["TP_b"], "dFP": del86["FP_r"] - del86["FP_b"],
                                "dF1": del86["F1_d"], "dF1_64": rows[1]["F1_d"]}
    lines += ["## %s" % tag, "", "- sha256: `%s`" % h,
              "- ΔTP %+d / ΔFP %+d / ΔF1 %+.4f / ΔF1(64) %+.4f / 触发案 %d / 删穴 %d"
              % (del86["TP_r"] - del86["TP_b"], del86["FP_r"] - del86["FP_b"], del86["F1_d"],
                 rows[1]["F1_d"], len(changed), sum(len(v["del"]) for v in changed.values())), "",
              "| 分层 | 案数 | TP | FP | FN | F1 (Δ) |", "|---|---:|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %d | %d→%d | %d→%d | %d→%d | %.4f→%.4f (%+.4f) |"
                     % (r["分层"], r["案数"], r["TP_b"], r["TP_r"], r["FP_b"], r["FP_r"],
                        r["FN_b"], r["FN_r"], r["F1_b"], r["F1_r"], r["F1_d"]))
    lines += ["", "| 案号 | 删穴 | 该案 TP 基线→重跑 | 该案 FP 基线→重跑 |", "|---|---|---|---|"]
    for c in sorted(changed):
        lines.append("| %s | %s | %d→%d | %d→%d |"
                     % (c, "、".join(changed[c]["del"]), PER_BASE[c]["tp"], PER[c]["tp"],
                        PER_BASE[c]["fp"], PER[c]["fp"]))
    lines.append("")

# 闸门关键词命中对照（4 个潜在受影响案）
lines += ["## 关键词命中对照（后溪/申脉 相关案）", "",
          "| 案号 | 输入含「腰」 | 输入含「跟」 | 输入含「踝」 | C1b 删 | C1b′ 删 |", "|---|---|---|---|---|---|"]
for c in ["107_01", "221_01", "249_01", "318_01"]:
    lines.append("| %s | %s | %s | %s | %s | %s |"
                 % (c, "是" if "腰" in SYM[c] else "否", "是" if "跟" in SYM[c] else "否",
                    "是" if "踝" in SYM[c] else "否",
                    "、".join(sorted(D_A[c])) or "—", "、".join(sorted(D_B[c])) or "—"))
lines.append("")

io.open(os.path.join(HERE, "PCq_C1b_判分汇总.json"), "w", encoding="utf-8").write(
    json.dumps(summary, ensure_ascii=False, indent=2))
io.open(os.path.join(HERE, "PCq_C1b_复算结果.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

print("self-check:", "PASS" if selfcheck else "FAIL")
for tag, _, _, _ in [(v[0], v[1], v[2], v[3]) for v in VARIANTS]:
    s = summary["variants"][tag]
    print("%s | ΔTP %+d ΔFP %+d ΔF1 %+.4f ΔF1_64 %+.4f | cases %d dels %d"
          % (tag, s["dTP"], s["dFP"], s["dF1"], s["dF1_64"], len(s["changed"]),
             sum(len(v["del"]) for v in s["changed"].values())))
sys.exit(0 if selfcheck else 1)
