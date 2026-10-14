# -*- coding: utf-8 -*-
"""基于人工全文核读，生成 140 首诊块的针灸方案核验清单（有方案/特殊标注/栏空）。"""
import io, os, json, csv, re, glob

OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
R140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

zones = io.open(r"D:\projectAGI\nhx\盲法对照实验\_acup_zones_all.txt", encoding="utf-8").read()

# 解析区段文件：块 -> (状态, 摘要)
blocks = re.split(r"=== (\S+) (\[.*?\] )?(.*?) ===\n", zones)
empty_set = set()
zone_summary = {}
i = 0
parts = re.findall(r"=== (\S+) (\[[^\]]*\] )?(.*?) ===\n(.*?)(?=\n\n=== |\Z)", zones, re.S)
for key, tag, rest, body in parts:
    body = body.strip()
    if tag and "区段为空" in tag:
        empty_set.add(key)
        zone_summary[key] = rest[:40]
    else:
        zone_summary[key] = body[:50].replace("\n", " ")

# 判分明细140：可判分案（重合率主非空）
rows = []
with io.open(os.path.join(R140, "判分明细.csv"), encoding="utf-8-sig", newline="") as f:
    rd = csv.DictReader(f)
    for r in rd:
        rows.append(r)
def num(x):
    try:
        return float(x)
    except Exception:
        return None
scored = {r["case_id"]: r for r in rows if num(r["重合率主"]) is not None}

# 93 非空块 = scored(86) + 特殊标注 7
specials = ["80_01", "178_01", "278_01", "284_01", "285_01", "268_01", "116_01"]
out_rows = []
for key in sorted(set(zone_summary) - empty_set):
    if key in scored:
        st = "可判分"
        note = scored[key].get("无法解析/备注", "")
    else:
        st = "特殊标注"
        note = ""
    out_rows.append({"case_id": key, "状态": st, "区段摘要": zone_summary.get(key, ""), "备注": note})
for key in sorted(empty_set):
    out_rows.append({"case_id": key, "状态": "针灸栏空(纯中药案)", "区段摘要": zone_summary.get(key, ""), "备注": "原文'針灸處方：'标题下直接接'中藥處方：'"})

out_rows.sort(key=lambda r: r["case_id"])
with io.open(os.path.join(OUT, "首诊针灸方案核验清单.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id", "状态", "区段摘要", "备注"])
    w.writeheader()
    w.writerows(out_rows)

n_s = sum(1 for r in out_rows if r["状态"] == "可判分")
n_t = sum(1 for r in out_rows if r["状态"] == "特殊标注")
n_e = sum(1 for r in out_rows if r["状态"] == "针灸栏空(纯中药案)")
print("总块:", len(out_rows), "| 可判分:", n_s, "| 特殊标注:", n_t, "| 针灸栏空:", n_e)
print("特殊标注案:", [r["case_id"] for r in out_rows if r["状态"] == "特殊标注"])
print("已生成 首诊针灸方案核验清单.csv")
