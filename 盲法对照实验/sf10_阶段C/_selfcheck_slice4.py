# -*- coding: utf-8 -*-
"""Self-check for slice4 symptoms_v2."""
import io, os, json, re, glob

OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C"
SYMDIR = os.path.join(OUT, "symptoms_v2")
FIELDS = ["初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象",
          "脉象","触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註"]
META = ["case_id","doc","block","visit_type","visit_type_依据","缺失字段清单","当前处方排除确认"]

files = sorted(glob.glob(os.path.join(SYMDIR, "*_symptoms_v2.json")))
print(f"JSON count: {len(files)}")

# Prescription-content leak patterns (these are current-block prescription texts that must NOT appear)
LEAK_PATTERNS = [
    # 311 prescription
    "雙外關","耳膽石點(埋耳針)","HT-43","麻子仁丸","HT-14","膽結石",
    # 312 prescription
    "豬苓湯","滑石五錢","阿膠二錢","雙足腎石點，雙耳腎點",
    # 318 prescription
    "頭臨泣,睛明,合谷","太淵,曲池,大凌","瓜蔞實三錢","薤白三錢","炮附子四錢→",
    # 323 prescription
    "四白﹑顴髎","右俠溪","解溪（胃經）","葛根6錢","防風3錢",
    # 340 prescription
    "右耳腎點埋耳針","HT-26",
    # 342 prescription
    "同4/13","旋覆花3、半夏３、五味子3","600 caps",
    # 345 prescription
    "後谿、申脈","百會。列缺，照海","真武湯加減","炮附子三錢","巴戟天三錢",
    # 346 prescription
    "右膏肓放血","列缺（統任脈）","照海（統陰蹺脈）","合谷、太沖（開四關）","桂枝加葛根湯方","甘草附子湯",
    # 347 prescription
    "左行間、公孫、大鐘、照海、太谿","柴胡三錢  玉金六錢","金鈴子1  延胡索1",
    # 355 prescription
    "膏肓放血","小承氣湯","龍膽草3錢","補金（清肺",
    # 37 prescription
    "左肝關，右肩井","左外關，左支溝","足臨泣，右足三里","大柴胡湯加減","茵陳二錢","海金沙二錢",
    # 38 prescription
    "瓜蔞實五錢","公孫，內關，天突，中脘","埋右耳針",
    # 49 prescription
    "天突、巨闕、關元","桔梗一兩","射干三錢 紫菀三錢","HT-32","烏金丸",
    # 55 prescription
    "公孫  內關  天突","魚際->滎穴","中皖  章門","左俠谿  右太陽透率谷",
    # 57 prescription
    "同前(公孫 內關 天突",
    # 60 prescription
    "合谷、太衝、曲池、肩井、足三里","HT-2 六兩","防己五錢、茯苓五錢","瓦楞子五錢","黃連阿膠湯",
    # 61 prescription
    "加四物湯","梁丘(胃經郄穴",
    # 62 prescription
    "同3/24方加茜草五錢","乳香一錢",
    # 63 prescription
    "神門、大陵","上巨虛","同3/24方再二付",
]

expected_keys = set(FIELDS) | set(META)
errors = []
field_present_counts = {f:0 for f in FIELDS}

for fp in files:
    cid = os.path.basename(fp).replace("_symptoms_v2.json","")
    txt = io.open(fp, encoding="utf-8").read()
    try:
        obj = json.loads(txt)
    except Exception as e:
        errors.append(f"{cid}: JSON parse error: {e}")
        continue
    # key consistency
    if set(obj.keys()) != expected_keys:
        missing_k = expected_keys - set(obj.keys())
        extra_k = set(obj.keys()) - expected_keys
        errors.append(f"{cid}: key mismatch missing={missing_k} extra={extra_k}")
    # check fields
    for f in FIELDS:
        v = obj.get(f)
        if v == "原文未记录":
            pass
        elif isinstance(v, dict):
            if "片段" not in v or "定位" not in v:
                errors.append(f"{cid}.{f}: object missing 片段/定位")
            else:
                field_present_counts[f] += 1
        else:
            errors.append(f"{cid}.{f}: unexpected value type: {type(v)} = {v!r}")
    # check 缺失字段清单 matches
    actual_missing = [f for f in FIELDS if obj[f] == "原文未记录"]
    if sorted(actual_missing) != sorted(obj["缺失字段清单"]):
        errors.append(f"{cid}: 缺失字段清单 mismatch: actual={actual_missing} listed={obj['缺失字段清单']}")
    # leak check
    for pat in LEAK_PATTERNS:
        if pat in txt:
            errors.append(f"{cid}: LEAK pattern '{pat}' found in output!")

print("Errors:", len(errors))
for e in errors:
    print(" -", e)

print("\nField presence counts (non-missing):")
for f in FIELDS:
    print(f"  {f}: {field_present_counts[f]}/19")

# visit type summary
vtypes = {}
for fp in files:
    obj = json.load(io.open(fp, encoding="utf-8"))
    vtypes.setdefault(obj["visit_type"], []).append(obj["case_id"])
print("\nVisit types:")
for k, v in vtypes.items():
    print(f"  {k}: {len(v)} -> {v}")
