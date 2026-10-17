#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-C 受控 patch：把候选规则（C2+C3=M2-06/R2 病程分期）应用到 v14r5 的**触发案**，
产出隔离副本预测集。不写正式基线、不改任何规则文件。

范式：沿用 `sf10_阶段M5/G_验收/patch_v14r1.py`（M10-1）——以冻结预测为基准，
仅对触发案重定主穴，其余案原样保留；输出到本目录。

产出两套（用于对照）：
  1) `_blind93_pcC23_results.json`        —— 分期按 **C_残余归因登记的原案对照**（金标准侧）
  2) `_blind93_pcC23_indep_results.json`  —— 分期按 **独立盲法执行的判定**（仅凭输入+规则文本）
两套的差别即"闸门可判定性"的直接证据。
"""
import hashlib
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def find_experiment_root(root):
    for name in sorted(os.listdir(root)):
        cand = os.path.join(root, name)
        if os.path.isfile(os.path.join(cand, "benchmark_v2", "canonical_scorer.py")):
            return cand
    return None


EXP = find_experiment_root(ROOT)
BASE = os.path.join(EXP, "sf10_阶段M5", "G_验收", "盲法v14r5", "_blind93v14r5_results.json")

# 分期方案 A：按 C_残余归因登记的原案对照（急性=140/142）
RECOVERY_A = ["141_01", "143_01", "144_01", "145_01", "146_01", "148_01", "149_01"]
# 分期方案 B：独立盲法执行（新会话、仅凭输入+规则文本）判定为"恢复期"者
RECOVERY_B = ["142_01", "144_01", "145_01", "148_01"]

NEW_RECORD = {
    "穴": "足三里",
    "层": "对症",
    "依据": "胃经本穴属土，灸之强土；利水后转补脾胃（P-C·R2/M2-06恢复期转折）",
    "出处": "教程_utf8 第4065/4529行",
    "备注": "P-C候选·未合入",
}
NOTE = ("【P-C 受控 patch·M2-06/R2 病程分期】恢复期（利水后水退/下肢肿退/心阳回头）："
        "去太冲（冲逆已平，不宜再引下），改取足三里补脾胃（土制水）；主穴总量维持 8 穴。")


def build(recovery, tag):
    data = json.load(io.open(BASE, encoding="utf-8"))
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

        rec["主穴记录"] = [e for e in (rec.get("主穴记录") or [])
                          if str(e.get("穴", "")).strip() != "太冲"]
        if not any(str(e.get("穴", "")).strip() == "足三里" for e in rec["主穴记录"]):
            rec["主穴记录"].append(dict(NEW_RECORD))

        rec["推理要点"] = str(rec.get("推理要点", "")) + "\n" + NOTE

        cre = rec.get("临床参考建议")
        if isinstance(cre, list):
            cre.append("太冲（急性水势上泛期引水下冲；恢复期让位）")
        elif isinstance(cre, str):
            rec["临床参考建议"] = cre + "\n太冲（急性水势上泛期引水下冲；恢复期让位）"
        else:
            rec["临床参考建议"] = ["太冲（急性水势上泛期引水下冲；恢复期让位）"]
        changed[cid] = {"old": before, "new": list(pts)}

    out = os.path.join(HERE, "_blind93_pcC23%s_results.json" % tag)
    json.dump(data, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    return out, h, changed


o1, h1, c1 = build(RECOVERY_A, "")
o2, h2, c2 = build(RECOVERY_B, "_indep")

print("base :", os.path.relpath(BASE, ROOT))
print("A(登记分期) :", os.path.relpath(o1, ROOT), "changed", len(c1), "sha256", h1)
print("B(独立判定) :", os.path.relpath(o2, ROOT), "changed", len(c2), "sha256", h2)
print("A 恢复期:", RECOVERY_A)
print("B 恢复期:", RECOVERY_B)
for c, d in c1.items():
    print("  A %s %s -> %s" % (c, d["old"], d["new"]))
for c, d in c2.items():
    print("  B %s %s -> %s" % (c, d["old"], d["new"]))
