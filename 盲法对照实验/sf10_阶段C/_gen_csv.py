# -*- coding: utf-8 -*-
"""Generate verification CSV from symptoms_v2 JSONs."""
import io, os, json, csv

V2 = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
OUT_CSV = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\核验表_分片2.csv"

cases_order = ["156_06","160_01","178_01","194_01","195_01","198_01","199_01","1_01",
               "200_01","201_01","202_01","207_01","208_01","209_01","212_01",
               "213_01","214_01","216_01","216_02"]

rows = []
for cid in cases_order:
    p = os.path.join(V2, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(p, encoding="utf-8"))
    missing = obj.get("缺失字段清单", [])
    vtype = obj.get("visit_type", "")
    # short visit type
    if vtype.startswith("首诊"):
        vt = "首诊"
    else:
        vt = "复诊"
    note_parts = []
    if cid == "156_06":
        note = "长期腹水复诊；既往=doc(156)第1-5块"
    elif cid in ("199_01","200_01","201_01","202_01"):
        note = f"198链复诊；既往锚=doc(198)第1块"
    elif cid == "198_01":
        note = "198链锚案"
    elif cid == "216_01":
        note = "216链锚案(173-3)；既往首诊=doc(214)"
    elif cid == "216_02":
        note = "216链复诊；既往=doc(216)第1块+doc(214)"
    elif cid == "213_01":
        note = "172链复诊；既往=doc(212)第1块"
    elif cid == "160_01":
        note = "132-1复诊；锚案不在本片"
    elif cid == "195_01":
        note = "164-1；首诊日=來診日"
    elif cid == "212_01":
        note = "172-1；213_01之锚"
    elif cid == "214_01":
        note = "173-1；216链之更早锚"
    else:
        note = ""
    rows.append({
        "case_id": cid,
        "visit_type": vt,
        "缺失字段数": len(missing),
        "字段清单": "、".join(missing),
        "当前处方排除": obj.get("当前处方排除确认", True),
        "备注": note,
    })

with io.open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id","visit_type","缺失字段数","字段清单","当前处方排除","备注"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print(f"CSV written: {OUT_CSV}")
for r in rows:
    print(f"  {r['case_id']}: {r['visit_type']}, missing={r['缺失字段数']}")
