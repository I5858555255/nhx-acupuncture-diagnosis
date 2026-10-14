# -*- coding: utf-8 -*-
"""Self-check for slice4 only (19 cases)."""
import io, os, json, re

OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C"
SYMDIR = os.path.join(OUT, "symptoms_v2")
FIELDS = ["初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象",
          "脉象","触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註"]
META = ["case_id","doc","block","visit_type","visit_type_依据","缺失字段清单","当前处方排除确认"]

MY_CASES = ["311_01","312_01","318_01","323_01","340_01","342_01","345_01",
            "346_01","347_01","355_01","37_01","38_01","49_01","55_01",
            "57_01","60_01","61_01","62_01","63_01"]

# Prescription content that must NOT appear (current-block 針灸/中藥處方 bodies)
# We check for actual prescription herb/point strings, not diagnostic words that also appear in symptoms.
LEAK_PATTERNS = [
    "雙外關","HT-43","HT-14","麻子仁丸","耳膽石點(埋耳針)",
    "豬苓湯","滑石五錢","阿膠二錢","雙足腎石點，雙耳腎點",
    "頭臨泣,睛明,合谷","太淵,曲池,大凌","炮附子四錢→","瓜蔞實三錢 薤白三錢",
    "四白﹑顴髎","右俠溪","解溪（胃經）","葛根6錢","防風3錢",
    "右耳腎點埋耳針","HT-26",
    "同4/13","旋覆花3、半夏３、五味子3","600 caps",
    "後谿、申脈","百會。列缺，照海","真武湯加減","巴戟天三錢",
    "右膏肓放血","列缺（統任脈）","照海（統陰蹺脈）","開四關","桂枝加葛根湯方","甘草附子湯",
    "左行間、公孫、大鐘、照海、太谿","玉金六錢","金鈴子1  延胡索1",
    "小承氣湯","龍膽草3錢","補金（清肺",
    "左肝關，右肩井","左外關，左支溝","足臨泣，右足三里","大柴胡湯加減","茵陳二錢","海金沙二錢",
    "瓜蔞實五錢","公孫，內關，天突，中脘","埋右耳針",
    "天突、巨闕、關元","桔梗一兩","射干三錢","HT-32","烏金丸",
    "魚際->滎穴","中皖  章門","左俠谿  右太陽透率谷",
    "同前(公孫 內關 天突",
    "合谷、太衝、曲池、肩井、足三里","HT-2 六兩","防己五錢、茯苓五錢","瓦楞子五錢","黃連阿膠湯",
    "加四物湯","梁丘(胃經郄穴",
    "同3/24方加茜草五錢","乳香一錢",
    "神門、大陵","上巨虛","同3/24方再二付",
]

expected_keys = set(FIELDS) | set(META)
errors = []
field_present = {f:0 for f in FIELDS}

for cid in MY_CASES:
    fp = os.path.join(SYMDIR, f"{cid}_symptoms_v2.json")
    if not os.path.exists(fp):
        errors.append(f"{cid}: FILE MISSING")
        continue
    txt = io.open(fp, encoding="utf-8").read()
    try:
        obj = json.loads(txt)
    except Exception as e:
        errors.append(f"{cid}: JSON parse error: {e}")
        continue
    if set(obj.keys()) != expected_keys:
        errors.append(f"{cid}: key mismatch missing={expected_keys-set(obj.keys())} extra={set(obj.keys())-expected_keys}")
    for f in FIELDS:
        v = obj.get(f)
        if v == "原文未记录":
            pass
        elif isinstance(v, dict):
            if "片段" not in v or "定位" not in v:
                errors.append(f"{cid}.{f}: missing 片段/定位")
            else:
                field_present[f] += 1
        else:
            errors.append(f"{cid}.{f}: bad type {type(v)}")
    actual_missing = sorted([f for f in FIELDS if obj[f] == "原文未记录"])
    if actual_missing != sorted(obj["缺失字段清单"]):
        errors.append(f"{cid}: missing list mismatch: {actual_missing} vs {obj['缺失字段清单']}")
    if obj.get("当前处方排除确认") is not True:
        errors.append(f"{cid}: 当前处方排除确认 not true")
    for pat in LEAK_PATTERNS:
        if pat in txt:
            errors.append(f"{cid}: LEAK '{pat}'")

print(f"Checked {len(MY_CASES)} cases")
print(f"Errors: {len(errors)}")
for e in errors:
    print(" -", e)

print("\nField presence (non-missing):")
for f in FIELDS:
    print(f"  {f}: {field_present[f]}/19")

# missing field frequency
from collections import Counter
miss_counter = Counter()
vtypes = {"首诊":[], "复诊":[]}
for cid in MY_CASES:
    fp = os.path.join(SYMDIR, f"{cid}_symptoms_v2.json")
    obj = json.load(io.open(fp, encoding="utf-8"))
    for m in obj["缺失字段清单"]:
        miss_counter[m] += 1
    vtypes.setdefault(obj["visit_type"], []).append(cid)

print("\nMissing field frequency:")
for f, c in miss_counter.most_common():
    print(f"  {f}: {c}")

print("\nVisit types:")
for k, v in vtypes.items():
    print(f"  {k}: {len(v)} -> {v}")
