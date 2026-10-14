# -*- coding: utf-8 -*-
"""Self-check + build CSV verification table and MD report."""
import io, os, json, csv, glob

OUTDIR = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C"
V2 = os.path.join(OUTDIR, "symptoms_v2")

FIELDS = ["初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象","脉象","触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註"]
EXPECTED_KEYS = {"case_id","doc","block","visit_type","visit_type_basis"} | set(FIELDS) | {"缺失字段清单","当前处方排除确认"}

# current-block prescription substrings that must NOT appear in any symptoms_v2 output
# (these belong to the CURRENT visit's 針灸處方/中藥處方/診斷 and are blinded)
FORBIDDEN = {
 "216_03": ["針穴同前加廉泉","舌強不語"],
 "216_04": ["左合谷、左外關（三焦經是氣＠經）","左解谿右攢竹、雙地倉透頬車、右陽白透魚腰、廉泉"],
 "216_05": ["左合谷、左外關、左解谿右攢竹、雙地倉透頬車、右陽白透魚腰、廉泉"],
 "221_01": ["大陵﹐水泉﹐俠溪","山茱萸3錢","六味地黃丸治足跟痛"],
 "223_01": ["左：曲池,三里","漢唐35號","紫金丹"],
 "225_01": ["後谿 + 申脈","HT-100"],
 "22_01": ["三陰交，血海","炮附子四錢","當歸四逆湯"],
 "234_01": ["眼四針、足臨泣","HT-88","炙甘草湯5"],
 "236_01": ["右丘墟、右足臨泣","桂枝四錢、白芍三錢","桂枝芍藥知母湯"],
 "23_01": ["三陰交，血海","炮附子四錢","當歸四逆湯"],
 "249_01": ["委中,陰谷","承山放血","漢唐36號"],
 "268_01": ["麻黃 三錢 杏仁","白虎湯","石膏 三兩"],
 "270_01": ["雙陰谷、委中、雙環跳","桂枝麻黃各半湯","防己五錢、茯苓五錢"],
 "274_01": ["合谷(欲下頭面針先下合谷)","瀉南補北","黃連 3錢","何首烏3錢"],
 "278_01": ["石膏 3兩，知母5錢","烏藥5錢","共10付"],
 "284_01": ["HT-2 漢唐2號","四物湯","共2付"],
 "285_01": ["同5月14","再3付"],
 "298_01": ["公孫 內關 巨闕","黃耆八錢","真武湯"],
 "303_01": ["合谷，曲池，血海","石膏 3兩，知母5錢","漢唐40號"],
}

MY_CASES = ["216_03","216_04","216_05","221_01","223_01","225_01","22_01","234_01",
         "236_01","23_01","249_01","268_01","270_01","274_01","278_01",
         "284_01","285_01","298_01","303_01"]
rows = []
problems = []
files = [os.path.join(V2, f"{c}_symptoms_v2.json") for c in MY_CASES]
files = [f for f in files if os.path.exists(f)]
print("json count:", len(files))

for fp in files:
    txt = io.open(fp, encoding="utf-8").read()
    d = json.loads(txt)
    cid = d["case_id"]
    # key check
    missing_keys = EXPECTED_KEYS - set(d.keys())
    extra_keys = set(d.keys()) - EXPECTED_KEYS
    if missing_keys: problems.append(f"{cid}: missing keys {missing_keys}")
    if extra_keys: problems.append(f"{cid}: extra keys {extra_keys}")
    if d.get("当前处方排除确认") is not True:
        problems.append(f"{cid}: 当前处方排除确认 != true")
    # field check
    miss = d["缺失字段清单"]
    for f in FIELDS:
        v = d.get(f)
        if v == "原文未记录":
            if f not in miss:
                problems.append(f"{cid}: field {f} is NA but not in 缺失字段清单")
        else:
            # should be dict or list of dict
            items = v if isinstance(v, list) else [v]
            for it in items:
                if not (isinstance(it, dict) and "片段" in it and "定位" in it):
                    problems.append(f"{cid}: field {f} non-missing lacks 片段/定位")
    if len(miss) != sum(1 for f in FIELDS if d.get(f)=="原文未记录"):
        problems.append(f"{cid}: 缺失字段清单 inconsistent")
    # forbidden prescription leak check
    for bad in FORBIDDEN.get(cid, []):
        if bad in txt:
            problems.append(f"{cid}: LEAK current-prescription text -> {bad}")
    rows.append(d)

# global forbidden scan across all files (any current acup point line leaking)
for fp in files:
    txt = io.open(fp, encoding="utf-8").read()

print("PROBLEMS:" if problems else "ALL CHECKS PASSED")
for p in problems:
    print("  -", p)

# ---- CSV ----
csv_path = os.path.join(OUTDIR, "核验表_分片3.csv")
with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_id","visit_type","缺失字段数","字段清单","当前处方排除","备注"])
    for d in rows:
        note = d.get("visit_type_basis","")
        w.writerow([d["case_id"], d["visit_type"], len(d["缺失字段清单"]),
                    "、".join(d["缺失字段清单"]), "true", note[:80]])
print("csv written:", csv_path)

# missing field frequency
from collections import Counter
cnt = Counter()
for d in rows:
    for m in d["缺失字段清单"]:
        cnt[m]+=1
print("MISSING FIELD FREQ:")
for k,v in cnt.most_common():
    print(f"  {k}: {v}")
