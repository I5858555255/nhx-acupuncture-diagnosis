# -*- coding: utf-8 -*-
import io, os, json, glob
OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
sym = sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "symptoms", "*_symptoms.txt")))
pres = sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "prescriptions", "*_prescription.txt")))
full = sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "full", "*_full.txt")))
print("symptoms:", len(sym), "prescriptions:", len(pres), "full:", len(full))
rows = json.load(io.open(os.path.join(OUT, "_scan_all.json"), encoding="utf-8"))
first = ["%03d_%02d" % (r["doc"], r["block"]) for r in rows if r.get("含針灸") and r.get("首诊")]
print("扫描清单首诊块:", len(first))
keys = [f.split("_symptoms")[0] for f in sym]
extra = sorted(set(keys) - set(first))
miss = sorted(set(first) - set(keys))
print("symptoms比扫描多出的(残留):", extra)
print("扫描有但无文件的:", miss)
sc = io.open(r"D:\projectAGI\nhx\盲法对照实验\盲法140\判分明细.csv", encoding="utf-8-sig").read().splitlines()
print("判分明细表头:", sc[0])
for k in extra:
    for line in sc[1:]:
        if line.startswith(k + ","):
            print("残留案判分:", line[:130])
