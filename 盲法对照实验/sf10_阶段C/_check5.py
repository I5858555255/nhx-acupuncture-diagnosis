# -*- coding: utf-8 -*-
"""Self-check for slice5: parse, key consistency, leakage scan."""
import io, os, json

D = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
cases = ["64_01","65_01","66_01","67_01","68_01","69_01","70_01","71_01","72_01",
         "73_01","74_01","75_01","76_01","77_01","78_01","80_01","8_01"]

FIELDS = ["初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象",
          "脉象","触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註"]
EXPECTED_KEYS = ["case_id","doc","block","visit_type","visit_type_evidence","当前处方排除确认"] + FIELDS + ["缺失字段清单"]

# Tokens that indicate CURRENT-block prescription content (must not be in any 片段)
# These are the actual point lists / herb dose strings from the current blocks.
LEAK = [
    # acupuncture point lists
    "肩井、足三里","大陵、神門","肩禺","梁丘、上巨虛","合谷、太衝","曲池、梁丘",
    "三間透後谿","膝五針","針同前穴","針同前","同前+ 外關","針灸處方",
    # current herb dosing (with 錢/兩 pattern)
    "五錢","三錢","一兩","二錢","十碗煮","九碗煮","三付","二付","五帖","五付",
    "HT2(退乳丸) 6兩","HT- 68","麻杏甘石湯   100",
    # current 診斷 labels that are treatment targets
    "陰盛陽虛","三焦積濕","陰陽交爭","陽氣仍無法完全運行","目前陰陽仍在相抗中",
]

base_keys = None
all_ok = True
for cid in cases:
    p = os.path.join(D, f"{cid}_symptoms_v2.json")
    with io.open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    if base_keys is None:
        base_keys = list(d.keys())
    elif list(d.keys()) != base_keys:
        print(f"KEY MISMATCH {cid}")
        all_ok = False
    for fld in FIELDS:
        v = d.get(fld)
        if v == "原文未记录":
            continue
        if not (isinstance(v, dict) and v.get("片段") and v.get("定位")):
            print(f"BAD {cid}/{fld}: {v}")
            all_ok = False
    # leak scan across all 片段
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            for tok in LEAK:
                if tok in v["片段"]:
                    print(f"LEAK {cid}/{k}: '{tok}' in: {v['片段'][:80]}")
                    all_ok = False

print("JSON count:", len(cases))
print("KEYS:", base_keys)
print("ALL OK" if all_ok else "PROBLEMS FOUND")
