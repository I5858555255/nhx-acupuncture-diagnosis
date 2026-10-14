# -*- coding: utf-8 -*-
"""从全集针灸首诊（140块）筛出 93 个"原文针灸栏非空"块，复制 symptoms+prescriptions 到 盲法93\。"""
import io, os, csv, shutil, json

SRC = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
DST = r"D:\projectAGI\nhx\盲法对照实验\盲法93"
os.makedirs(os.path.join(DST, "symptoms"), exist_ok=True)
os.makedirs(os.path.join(DST, "prescriptions"), exist_ok=True)

keep = []
with io.open(os.path.join(SRC, "首诊针灸方案核验清单.csv"), encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["状态"] != "针灸栏空(纯中药案)":
            keep.append(r["case_id"])
print("保留(原文针灸栏非空)块数:", len(keep))

missing = []
for k in keep:
    for sub, suf in (("symptoms", "_symptoms.txt"), ("prescriptions", "_prescription.txt")):
        s = os.path.join(SRC, sub, k + suf)
        d = os.path.join(DST, sub, k + suf)
        if os.path.exists(s):
            shutil.copy(s, d)
        else:
            missing.append((sub, k))
print("缺失:", missing if missing else "无")

with io.open(os.path.join(DST, "case_list.json"), "w", encoding="utf-8") as f:
    json.dump(keep, f, ensure_ascii=False, indent=1)

n_s = len(os.listdir(os.path.join(DST, "symptoms")))
n_p = len(os.listdir(os.path.join(DST, "prescriptions")))
print("symptoms:", n_s, " prescriptions:", n_p)
