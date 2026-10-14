# -*- coding: utf-8 -*-
"""失败模式分析：86 可判分案 gold/盲法/命中对照，输出分类表供人工归类。"""
import io, os, csv, json, re

D = r"D:\projectAGI\nhx\盲法对照实验\盲法93"
rows = list(csv.DictReader(io.open(os.path.join(D, "判分明细.csv"), encoding="utf-8-sig", newline="")))
blind = json.load(io.open(os.path.join(D, "_blind93_results.json"), encoding="utf-8"))
PRES = r"D:\projectAGI\nhx\盲法对照实验\盲法93\prescriptions"

def num(x):
    try: return float(x)
    except: return None

def gold_points(pres_path):
    """从处方文件提取穴名清单（简化：去空格、去编号）。"""
    try:
        t = io.open(pres_path, encoding="utf-8").read()
    except Exception:
        return []
    # 原案处方常见格式：编号+穴名+手法
    # 简单提取：分割行，去序号/剂量词
    pts = []
    for line in t.splitlines():
        line = line.strip()
        if not line or "處方" in line or "診斷" in line or "中藥" in line:
            continue
        # 去开头数字编号
        line = re.sub(r"^\d+[\.、]?\s*", "", line)
        if not line:
            continue
        pts.append(line[:20])
    return pts

out = []
scored = [r for r in rows if num(r["重合率主"]) is not None]
for r in sorted(scored, key=lambda x: num(x["重合率主"])):
    cid = r["case_id"]
    hit = (r["命中穴清单主"] or "").strip()
    gp = gold_points(os.path.join(PRES, cid + "_prescription.txt"))
    b = blind.get(cid, {})
    bz = b.get("辨证结论", {})
    if isinstance(bz, dict):
        bz_s = bz.get("病经/病位", "")
    else:
        bz_s = str(bz)[:40]
    out.append({
        "case_id": cid,
        "重合率主": r["重合率主"],
        "gold穴数": r["gold穴数"],
        "盲法主穴数": r["本轮盲法主穴数"],
        "命中": hit,
        "盲法辨证": bz_s[:34],
        "gold处方前80": " | ".join(gp)[:80],
        "140版重合率": r["140版重合率主"],
    })

with io.open(os.path.join(D, "失败模式分析表.tsv"), "w", encoding="utf-8", newline="") as f:
    f.write("\t".join(out[0].keys()) + "\n")
    for o in out:
        f.write("\t".join(str(o[k]).replace("\t", " ") for k in o) + "\n")

buckets = {}
for o in out:
    v = float(o["重合率主"])
    b = "<20%" if v < 0.2 else ("20-39%" if v < 0.4 else ("40-59%" if v < 0.6 else ">=60%"))
    buckets.setdefault(b, []).append(o["case_id"])
for k in ["<20%", "20-39%", "40-59%", ">=60%"]:
    print(k, len(buckets.get(k, [])), buckets.get(k, []))
print("已生成 失败模式分析表.tsv")
