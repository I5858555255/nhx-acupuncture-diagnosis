# -*- coding: utf-8 -*-
"""M7-B: 86 案 R7 症状信号扫描（修正分类）"""
import os, io, csv, pickle
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
SYMP_DIR = os.path.join(ROOT, "盲法93", "symptoms")
OUT = os.path.join(ROOT, "sf10_阶段M5", "G_验收", "86案R7触发表.csv")

g = pickle.load(open(os.path.join(ROOT, "benchmark_v2", "_gold_results93v2.pkl"), "rb"))
SC = [c for c in g["case_ids"] if len(g["results"][c]["gold_members"]) > 0]
R7_TARGETS = {"207_01", "236_01", "118_01", "194_01"}

def scan(text):
    cats = []
    if "外踝" in text: cats.append("外踝痛/外踝部")
    if "扭傷" in text or "扭伤" in text: cats.append("扭伤史")
    if "踝" in text:
        if "腫" in text or "肿" in text: cats.append("踝肿")
        if "緊" in text or "紧" in text: cats.append("踝紧")
        if "不舒服" in text: cats.append("踝不适")
        if "痛" in text and "外踝" not in text and "踝肿" not in cats and "踝紧" not in cats and "踝不适" not in cats:
            cats.append("单踝痛")
    if "足外側" in text or "足外侧" in text: cats.append("足外侧冷")
    if "足跟" in text or "腳跟" in text or "脚跟" in text: cats.append("内侧足跟痛(R1域)")
    if "膝" in text: cats.append("膝相关")
    if "手腕" in text or "媽媽手" in text or "妈妈手" in text: cats.append("手腕/妈妈手(R7分流排除)")
    if not cats: cats.append("无踝相关信号")
    return cats

rows = []
for cid in SC:
    p = os.path.join(SYMP_DIR, cid + "_symptoms.txt")
    text = io.open(p, encoding="utf-8").read()
    cats = scan(text)
    ankle_kw = ["踝", "足外側", "足外侧", "足跟", "腳跟", "脚跟"]
    ankle_signal = any(k in text for k in ankle_kw)
    lines = [l.strip() for l in text.split("\n") if any(k in l for k in ankle_kw)]
    sig = " | ".join(lines)[:140]
    # R7 触发判定：仅踝/足外侧信号；足跟属R1域；膝/手腕不计
    r7_trig = any(k in text for k in ["踝", "足外側", "足外侧"])
    if r7_trig:
        # 双侧踝水肿 → M2-06 域，非R7
        if ("雙腳踝" in text or "双脚踝" in text) and ("水腫" in text or "水肿" in text):
            trig = "不触发(双侧踝水肿=M2-06域)"
        else:
            trig = "可触发(待两条线细分)"
    else:
        trig = "不触发"
    rows.append({
        "case_id": cid, "信号类别": "/".join(cats), "触发与否": trig,
        "信号原文": sig, "R7目标案": "是" if cid in R7_TARGETS else "",
    })

with io.open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id", "信号类别", "触发与否", "信号原文", "R7目标案"])
    w.writeheader(); w.writerows(rows)

trig_rows = [r for r in rows if r["触发与否"].startswith("可触发")]
print("总案数:", len(rows), "| R7可触发:", len(trig_rows))
for r in trig_rows:
    print(r["case_id"], "|", r["信号类别"], "|", r["R7目标案"], "|", r["信号原文"][:70])
print("---含足跟/R1域---")
for r in rows:
    if "足跟" in r["信号类别"]:
        print(r["case_id"], "|", r["信号原文"][:70])
