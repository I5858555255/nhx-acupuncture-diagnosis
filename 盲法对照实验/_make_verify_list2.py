# -*- coding: utf-8 -*-
"""基于人工全文核读（_acup_zones_all.txt），重新生成 140 首诊块核验清单。"""
import io, os, csv, re

OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
R140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

zones = io.open(r"D:\projectAGI\nhx\盲法对照实验\_acup_zones_all.txt", encoding="utf-8").read()
empty_set = set(re.findall(r"=== (\S+) \[区段为空\]", zones))
print("空块(针灸栏空)计数:", len(empty_set))

detail_path = os.path.join(R140, "判分明细.csv")
rows = []
with io.open(detail_path, encoding="utf-8-sig", newline="") as f:
    rd = csv.DictReader(f)
    for r in rd:
        rows.append(r)
print("判分明细行数:", len(rows))

def num(x):
    try:
        return float(x)
    except Exception:
        return None

# 摘要：从区段文件抽取每个非空块的首40字
summary = {}
for m in re.finditer(r"=== (\S+) 针灸处方区段原文 ===\n(.*?)(?=\n\n=== |\Z)", zones, re.S):
    summary[m.group(1)] = m.group(2).strip().replace("\n", " ")[:50]
print("非空块摘要数:", len(summary))

out_rows = []
n_scored = n_special = n_empty = 0
for r in sorted(rows, key=lambda x: x["case_id"]):
    key = r["case_id"]
    if key in empty_set:
        st = "针灸栏空(纯中药案)"
        n_empty += 1
        note = "原文'針灸處方：'标题下直接接'中藥處方：'"
    elif num(r["重合率主"]) is not None:
        st = "可判分"
        n_scored += 1
        note = r.get("无法解析/备注", "")
    else:
        st = "特殊标注(無/N-A/同前/左右)"
        n_special += 1
        note = r.get("无法解析/备注", "")
    out_rows.append({"case_id": key, "状态": st,
                     "区段摘要": summary.get(key, ""), "备注": note})

with io.open(os.path.join(OUT, "首诊针灸方案核验清单.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id", "状态", "区段摘要", "备注"])
    w.writeheader()
    w.writerows(out_rows)

print("总块:", len(out_rows), "| 可判分:", n_scored, "| 特殊标注:", n_special, "| 针灸栏空:", n_empty)
print("特殊标注案:", [r["case_id"] for r in out_rows if r["状态"] == "特殊标注(無/N-A/同前/左右)"])
print("已生成 首诊针灸方案核验清单.csv")
