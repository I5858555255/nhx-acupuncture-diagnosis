# -*- coding: utf-8 -*-
"""SF10 阶段D D1: 组装 history-aware 盲法输入。"""
import json, os, pickle, csv, sys

BASE = r"D:\projectAGI\nhx\盲法对照实验"
SRC = os.path.join(BASE, "sf10_阶段C", "symptoms_v2")
OUT = os.path.join(BASE, "sf10_阶段D", "inputs_hist")
PKL = os.path.join(BASE, "benchmark_v2", "_gold_results93v2.pkl")

with open(PKL, "rb") as f:
    gold = pickle.load(f)
chain_map = gold["summary"]["chain_map"]

FIELDS = ["來診日期", "病程", "來診原因", "主诉变化", "問診",
          "望诊", "舌象", "脉象", "触诊压痛", "耳穴", "西醫診斷", "備註"]

def frag(v):
    """字段值: {片段,定位} dict / 纯字符串 / list[{片段,定位}]。"""
    if isinstance(v, dict):
        s = v.get("片段", "原文未记录")
        return s if isinstance(s, str) else "原文未记录"
    if isinstance(v, list):
        parts = []
        for it in v:
            s = it.get("片段", "") if isinstance(it, dict) else str(it)
            if s and s != "原文未记录":
                parts.append(s)
        return "\n".join(parts) if parts else "原文未记录"
    if isinstance(v, str):
        return v
    return "原文未记录"

def loc(v):
    if isinstance(v, dict):
        return v.get("定位") or ""
    if isinstance(v, list):
        return "；".join(it.get("定位") or "" for it in v if isinstance(it, dict))
    return ""

rows = []
files = sorted(os.listdir(SRC))
assert len(files) == 93, f"symptoms_v2 数量={len(files)} != 93"

for fn in files:
    cid = fn.replace("_symptoms_v2.json", "")
    with open(os.path.join(SRC, fn), encoding="utf-8") as f:
        d = json.load(f)
    doc = d["doc"]; blk = d["block"]
    vtype = d.get("visit_type", "")
    vtype_short = "复诊" if vtype.startswith("复诊") else ("首诊" if vtype.startswith("首诊") else vtype)
    chain = chain_map.get(cid, "UNKNOWN")

    lines = []
    lines.append(f"案号：{cid}")
    lines.append(f"doc({doc}) 第{blk}块")
    lines.append(f"visit_type：{vtype_short}")
    lines.append(f"chain：{chain}")
    lines.append("")
    lines.append("【本次就診】")
    non_missing = 0
    for fld in FIELDS:
        s = frag(d.get(fld))
        if s != "原文未记录":
            non_missing += 1
        lines.append(f"{fld}：{s}")
    lines.append("")

    hist_raw = d.get("既往就诊及治疗反馈")
    hist = frag(hist_raw)
    # 泄漏剔除：216_01 的既往片段尾部误含当前目标块(doc216第1块, 5/15)自身的
    # 針灸處方穴串+解說，按任务规则剔除（備註同文已在本次節備註字段保留）。
    leak_fixed = ""
    if cid == "216_01" and "本次(5/15)針灸處方穴：" in hist:
        hist = hist.split("本次(5/15)針灸處方穴：")[0].rstrip("。；; ") + "。"
        leak_fixed = "FIXED"
    if hist == "原文未记录" or not hist.strip():
        has_hist = "N"
        lines.append("【既往就診（早于本次）】")
        lines.append("无既往就诊记录（首诊/原文未记录）")
        hist_src = ""
    else:
        has_hist = "Y"
        lines.append("【既往就診（早于本次）】")
        lines.append(hist)
        hist_src = loc(hist_raw)
    lines.append("")
    lines.append("【本次處方排除确认】本次就診的診斷/針灸處方/中藥處方未包含于本输入。")

    txt = "\n".join(lines) + "\n"
    outp = os.path.join(OUT, f"{cid}_hist.txt")
    with open(outp, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)

    rows.append({
        "case_id": cid, "doc": doc, "block": blk,
        "visit_type": vtype, "chain": chain,
        "有既往(Y/N)": has_hist, "既往来源块说明": hist_src,
        "本次字段数(非原文未记录)": non_missing,
        "leak": leak_fixed or "PASS",
    })

# 组装清单.csv (utf-8-sig)
csv_path = os.path.join(BASE, "sf10_阶段D", "组装清单.csv")
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_id", "doc", "block", "visit_type", "chain",
                "有既往(Y/N)", "既往来源块说明", "本次字段数(非原文未记录)", "复核泄漏"])
    for r in rows:
        w.writerow([r["case_id"], r["doc"], r["block"], r["visit_type"], r["chain"],
                    r["有既往(Y/N)"], r["既往来源块说明"], r["本次字段数(非原文未记录)"], r["leak"]])

print("done", len(rows))
