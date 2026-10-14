# -*- coding: utf-8 -*-
"""生成140首诊口径交付：移动6个残留覆诊块文件、剔除盲法结果与判分明细、追加报告口径修正节。"""
import io, os, json, glob, csv, shutil

OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
R140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"
RESID = ["136_02", "136_03", "287_01", "346_02", "354_01", "3_01"]

# 1) 移动残留覆诊块文件（我的脚本产物，从首诊目录移出）
resdir = os.path.join(OUT, "_非首诊残留覆诊块")
for sub in ("full", "symptoms", "prescriptions"):
    d = os.path.join(resdir, sub)
    os.makedirs(d, exist_ok=True)
    for k in RESID:
        for pat in (f"{k}_full.txt", f"{k}_symptoms.txt", f"{k}_prescription.txt"):
            src = os.path.join(OUT, sub, pat)
            if os.path.exists(src):
                shutil.move(src, os.path.join(d, pat))
    print("moved", sub, "->", len(os.listdir(d)))
print("symptoms now:", len(glob.glob(os.path.join(OUT, "symptoms", "*_symptoms.txt"))))

# 2) 盲法结果剔除6案
res = json.load(io.open(os.path.join(R140, "_blind140_results.json"), encoding="utf-8"))
res140 = {k: v for k, v in res.items() if k not in RESID}
json.dump(res140, io.open(os.path.join(R140, "_blind140_results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("blind results 140:", len(res140))

# 3) 判分明细剔除6案
rows = []
with io.open(os.path.join(R140, "判分明细.csv"), encoding="utf-8-sig", newline="") as f:
    rd = csv.DictReader(f)
    rows = [r for r in rd if r["case_id"] not in RESID]
with io.open(os.path.join(R140, "判分明细.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("明细140:", len(rows))

# 4) 汇总 json 更新（用 _recheck140.json 的结果）
agg = json.load(io.open(os.path.join(R140, "_recheck140.json"), encoding="utf-8"))
json.dump(agg, io.open(os.path.join(R140, "判分汇总.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("汇总已更新")
