# -*- coding: utf-8 -*-
# M10-1: v14r1 受控 patch —— 以 v14r7 合并产物为基准，仅对 R1 触发案（208/221）应用 M2-16·R1 调整
# 触发=足跟痛/腳跟痛 → 水泉+对侧大陵（已有水泉则仅补大陵；仆参备选非必出）
import json, hashlib

BASE = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收\盲法v14r7\_blind93v14r7_results.json"
OUT  = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收\盲法v14r1\_blind93v14r1_results.json"

data = json.load(open(BASE, encoding="utf-8"))  # {case_id: {...93案...}}
n = len(data)

def norm_point(p):
    return p.replace(" ", "").replace("＋", "+")

CHANGED = {}
for cid, rec in data.items():
    mz = rec["主穴"]
    pts = [norm_point(p) for p in mz]
    if cid in ("208_01", "221_01"):
        added = []
        if "水泉" not in pts:
            pts.append("水泉"); added.append("水泉")
        if "大陵" not in pts:
            pts.append("大陵"); added.append("大陵")
        if added:
            CHANGED[cid] = {"old": list(mz), "new": list(pts), "added": added}
            rec["主穴"] = list(pts)
        rec["推理要点"] = rec.get("推理要点", "") + "\nM10-1 R1应用: 足跟痛→M2-16·R1 水泉+对侧大陵(仆参备选非必出)"

json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

h = hashlib.sha256(open(OUT, "rb").read()).hexdigest()
print("cases:", n, "| changed:", len(CHANGED))
for c, d in CHANGED.items():
    print(" ", c, "old:", d["old"], "-> new:", d["new"], "| added:", d["added"])
print("sha256:", h)
