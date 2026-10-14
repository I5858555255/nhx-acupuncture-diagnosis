# -*- coding: utf-8 -*-
"""Self-checks for symptoms_v2 outputs."""
import io, os, json, re

V2 = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
cases_order = ["156_06","160_01","178_01","194_01","195_01","198_01","199_01","1_01",
               "200_01","201_01","202_01","207_01","208_01","209_01","212_01",
               "213_01","214_01","216_01","216_02"]

FIELDS = ["初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象","脉象","触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註"]
META = ["case_id","doc","block","visit_type","缺失字段清单","当前处方排除确认"]

print("=== CHECK 1: All 19 JSONs parse, keys consistent ===")
ok = True
for cid in cases_order:
    p = os.path.join(V2, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(p, encoding="utf-8"))
    keys = set(obj.keys())
    expected = set(FIELDS + META)
    if keys != expected:
        print(f"  KEY MISMATCH {cid}: extra={keys-expected}, missing={expected-keys}")
        ok = False
if ok:
    print("  PASS: all 19 JSONs have identical key set")

print("\n=== CHECK 2: Missing fields marked, non-missing have fragment+loc ===")
ok = True
for cid in cases_order:
    p = os.path.join(V2, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(p, encoding="utf-8"))
    for k in FIELDS:
        v = obj.get(k)
        if v == "原文未记录":
            if k not in obj["缺失字段清单"]:
                print(f"  MISMATCH {cid}/{k}")
                ok = False
        elif isinstance(v, dict):
            if k in obj["缺失字段清单"]:
                print(f"  MISMATCH {cid}/{k}: has fragment but in missing list")
                ok = False
            if "片段" not in v or "定位" not in v:
                print(f"  NO LOC {cid}/{k}")
                ok = False
        else:
            print(f"  BAD TYPE {cid}/{k}: {type(v)}")
            ok = False
if ok:
    print("  PASS")

print("\n=== CHECK 3: No current prescription-section headers in non-既往 fields ===")
leak_words = ["中藥處方：", "針灸處方：", "九碗煮成三碗", "九碗煮3碗"]
ok = True
for cid in cases_order:
    p = os.path.join(V2, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(p, encoding="utf-8"))
    for k in FIELDS:
        v = obj.get(k)
        if isinstance(v, dict) and k != "既往就诊及治疗反馈":
            text = v.get("片段", "")
            for lw in leak_words:
                if lw in text:
                    print(f"  LEAK {cid}/{k}: '{lw}' in: {text[:80]}")
                    ok = False
if ok:
    print("  PASS")

print("\n=== SUMMARY ===")
missing_freq = {}
total = 0
for cid in cases_order:
    p = os.path.join(V2, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(p, encoding="utf-8"))
    for k in obj["缺失字段清单"]:
        missing_freq[k] = missing_freq.get(k, 0) + 1
        total += 1
print(f"Total missing field-instances: {total}/(19*14={19*14})")
print("Missing frequency:")
for k, v in sorted(missing_freq.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}/19")
