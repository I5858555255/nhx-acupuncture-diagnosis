# -*- coding: utf-8 -*-
"""归一化核对：找出 symptoms 目录中非首诊的残留覆诊块文件，并按 140 首诊口径重算判分汇总。"""
import io, os, json, glob, csv, statistics, re

OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
R140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

def norm(k):
    # 1_01 -> 001_01 ; 136_02 -> 136_02
    m = re.match(r"(\d+)_(\d+)", k)
    return "%03d_%02d" % (int(m.group(1)), int(m.group(2)))

# 1) scan.json -> is_first per block
rows = json.load(io.open(os.path.join(OUT, "_scan_all.json"), encoding="utf-8"))
flag = {}
for r in rows:
    if r.get("error"):
        continue
    flag[norm("%d_%d" % (r["doc"], r["block"]))] = (r.get("首诊"), r.get("含針灸"))

# 2) symptoms files
sym = [os.path.basename(f).split("_symptoms")[0] for f in glob.glob(os.path.join(OUT, "symptoms", "*_symptoms.txt"))]
resid = []
ok = []
for k in sym:
    nk = norm(k)
    first, acup = flag.get(nk, (None, None))
    if first is False:
        resid.append(k)
    else:
        ok.append(nk)
print("symptoms文件数:", len(sym))
print("非首诊残留覆诊块:", sorted(resid))
print("应为首诊块:", len(ok))

# 3) 判分明细.csv
rows_csv = []
with io.open(os.path.join(R140, "判分明细.csv"), encoding="utf-8-sig", newline="") as f:
    rd = csv.DictReader(f)
    for r in rd:
        rows_csv.append(r)
print("判分明细行数:", len(rows_csv))

def num(x):
    try:
        return float(x)
    except Exception:
        return None

# 146口径汇总（全量，复算校验）
def agg(sel):
    n = len(sel)
    vals_main = [num(r["重合率主"]) for r in sel if num(r["重合率主"]) is not None]
    vals_mz = [num(r["重合率主佐"]) for r in sel if num(r["重合率主佐"]) is not None]
    vals_p = [num(r["精确率"]) for r in sel if num(r["精确率"]) is not None]
    hits = [num(r["命中数主"]) for r in sel if num(r["命中数主"]) is not None]
    return {
        "n": n, "n_scored": len(vals_main),
        "重合率主_均值": round(statistics.mean(vals_main), 4) if vals_main else None,
        "重合率主_中位": round(statistics.median(vals_main), 4) if vals_main else None,
        "主佐_均值": round(statistics.mean(vals_mz), 4) if vals_mz else None,
        "主佐_中位": round(statistics.median(vals_mz), 4) if vals_mz else None,
        "精确率_均值": round(statistics.mean(vals_p), 4) if vals_p else None,
        "每案命中均值": round(statistics.mean(hits), 4) if hits else None,
    }

all146 = agg(rows_csv)
print("146口径(全量复算):", all146)

# 140口径：剔除残留覆诊块
sel140 = [r for r in rows_csv if norm(r["case_id"]) not in {norm(k) for k in resid}]
a140 = agg(sel140)
print("140口径(剔除%s个残留覆诊块):" % len(resid), a140)

# 分布
def dist(sel):
    d = {"100": 0, "80-99": 0, "60-79": 0, "40-59": 0, "<40": 0, "NA": 0}
    for r in sel:
        v = num(r["重合率主"])
        if v is None:
            d["NA"] += 1
        elif v >= 1.0:
            d["100"] += 1
        elif v >= 0.8:
            d["80-99"] += 1
        elif v >= 0.6:
            d["60-79"] += 1
        elif v >= 0.4:
            d["40-59"] += 1
        else:
            d["<40"] += 1
    return d
print("140口径分布:", dist(sel140))

# 不可判分明细（140口径内）
noscore140 = [r for r in sel140 if num(r["重合率主"]) is None]
print("140口径不可判分:", len(noscore140))
reasons = {}
for r in noscore140:
    note = r.get("无法解析/备注", "")
    if "空" in note:
        reasons.setdefault("处方文件为空", []).append(r["case_id"])
    elif "無" in note or "N/A" in note:
        reasons.setdefault("原文标注無/N/A", []).append(r["case_id"])
    elif "同前" in note:
        reasons.setdefault("同前", []).append(r["case_id"])
    else:
        reasons.setdefault("其他", []).append((r["case_id"], note))
for k, v in reasons.items():
    print(" -", k, len(v), v[:8])

# 保存140口径汇总
out = {"146口径_全量复算": all146, "140口径": a140, "140口径_分布": dist(sel140),
       "残留覆诊块": sorted(resid), "不可判分140": len(noscore140)}
json.dump(out, io.open(os.path.join(R140, "_recheck140.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已保存 _recheck140.json")
