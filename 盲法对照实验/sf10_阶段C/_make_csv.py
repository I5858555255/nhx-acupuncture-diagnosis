# -*- coding: utf-8 -*-
"""Generate 核验表_分片5.csv and aggregate stats."""
import io, os, json, csv

D = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C"
cases = ["64_01","65_01","66_01","67_01","68_01","69_01","70_01","71_01","72_01",
         "73_01","74_01","75_01","76_01","77_01","78_01","80_01","8_01"]

notes = {
 "64_01": "乳癌鏈早期覆診(4/7)，承接更早未入本片之就診；與65/66同病患L,ML",
 "65_01": "乳癌鏈早期覆診(4/9)，針灸同前、中藥同3/24方加味",
 "66_01": "乳癌鏈錨案(4/11)，'藥仍有四付'，67-78既往引用此塊",
 "67_01": "乳癌鏈覆診(4/16)，首次出現標準鏈主訴(三年多/未經西醫治療)",
 "68_01": "乳癌鏈覆診(4/21)",
 "69_01": "乳癌鏈覆診(4/23)",
 "70_01": "乳癌鏈覆診(4/25)",
 "71_01": "乳癌鏈覆診(4/28)",
 "72_01": "乳癌鏈覆診(5/5)",
 "73_01": "乳癌鏈覆診(5/7)",
 "74_01": "乳癌鏈覆診(5/12)",
 "75_01": "乳癌鏈覆診(5/14)",
 "76_01": "乳癌鏈覆診(5/16)",
 "77_01": "乳癌鏈覆診(5/19)",
 "78_01": "乳癌鏈末診(5/21)，病人將回國，今日乃最後一診",
 "80_01": "獨立首診，C,LH男胖，咳嗽/口臭/25年前B肝，與乳癌鏈無關",
 "8_01": "獨立首診，S,ZH女46歲，類風濕性關節炎，初診=來診日期2008/3/10",
}

rows = []
miss_counter = {}
for cid in cases:
    with io.open(os.path.join(D, f"{cid}_symptoms_v2.json"), encoding="utf-8") as f:
        d = json.load(f)
    m = d["缺失字段清单"]
    for x in m:
        miss_counter[x] = miss_counter.get(x, 0) + 1
    rows.append({
        "case_id": cid,
        "visit_type": d["visit_type"],
        "缺失字段数": len(m),
        "字段清单": "、".join(m),
        "当前处方排除": "true" if d["当前处方排除确认"] else "false",
        "备注": notes[cid],
    })

with io.open(os.path.join(OUT, "核验表_分片5.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id","visit_type","缺失字段数","字段清单","当前处方排除","备注"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

print("CSV written.")
print("\n=== 缺失字段高频统计 ===")
for k, v in sorted(miss_counter.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"\n总缺失字段数: {sum(miss_counter.values())}")
