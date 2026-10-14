# -*- coding: utf-8 -*-
"""Self-check: JSON parse, key consistency, no prescription leak."""
import io, os, json, re, glob

DIR = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
files = sorted(glob.glob(os.path.join(DIR, "*_symptoms_v2.json")))
print(f"Found {len(files)} JSON files")

REQUIRED = {"case_id","doc","block","visit_type","visit_type_basis",
            "初診日期","來診日期","病程","來診原因","主诉变化","問診","望诊","舌象","脉象",
            "触诊压痛","耳穴","西醫診斷","既往就诊及治疗反馈","備註",
            "缺失字段清单","当前处方排除确认"}

# Prescription leak patterns - these strings must NOT appear in any 片段
LEAK = ["針灸處方","中藥處方","委中","承山","陰谷","後溪","外關","公孫","內關","巨闕","關元",
        "三皇穴","復溜","照海","水泉","太衝","足三里","章門","中極","水道","水分",
        "紫參","炙甘草","桔梗","半夏","南星","柴胡","鬱金","黃芩","茜草","牡蠣","五味子",
        "乾薑","補骨脂","炙鱉甲","桂枝","白芍","生薑","大棗","葛根","黃芪","黃耆","當歸",
        "川芎","生地","酸棗仁","升麻","知母","竹茹","阿膠","黃連","黨參","白朮","茯苓",
        "澤瀉","豬苓","陳皮","厚樸","蒼朮","燈心草","大腹皮","淮山","薏仁","薏苡仁","芡實","蓮子",
        "生附子","炮附子","細辛","吳茱萸","皂莢","洋參","麥冬","車前子","通草","木通",
        "澤瀉","丹皮","桃仁","三七","續斷","旋覆花","代赭石","吳茱萸","細辛","烏藥",
        "龍膽草","白芷","西洋參","澤瀉","麻黃","射干","紫苑","冬花","細辛","五味子",
        "車前子","通草","鬱金","丹皮","桃仁","補骨脂","敗龜板","硫磺","陽起石",
        "HT-43","HT-40","十棗湯","甘遂半夏湯","分消湯","真武湯","四逆湯","五苓散",
        "胃苓湯","烏梅丸","當歸建中湯","炙甘草湯","補氣治濕湯","麻子仁丸",
        "睛明","太陽","頭臨泣","光明","肩井","解溪","梁丘","商丘","丘墟","合谷","養老",
        "上巨虛","曲池","頰車","地倉","中脘","公孫","腎俞","京門","心俞","肺俞","神門",
        "金匱","九碗煮","九碗水煮","三付","五付","貳付","七付","伍付","四付","早晚餐前","bf B/S","bf B&S"]

for fp in files:
    cid = os.path.basename(fp).replace("_symptoms_v2.json","")
    with io.open(fp, encoding="utf-8") as f:
        d = json.load(f)
    missing_keys = REQUIRED - set(d.keys())
    extra_keys = set(d.keys()) - REQUIRED
    errs = []
    if missing_keys: errs.append(f"missing keys: {missing_keys}")
    if not d.get("当前处方排除确认"): errs.append("当前处方排除确认 not True")
    # check leak
    alltext = json.dumps(d, ensure_ascii=False)
    leaks = []
    for pat in LEAK:
        # only flag if it appears in a 片段 value (not in 定位 where we might mention section names)
        for k,v in d.items():
            if isinstance(v, dict) and "片段" in v:
                if pat in v["片段"]:
                    # allow known medical-history mentions
                    leaks.append((k, pat, v["片段"][:60]))
    if errs:
        print(f"!! {cid}: {errs}")
    if leaks:
        print(f"?? {cid} potential leak:")
        for k,p,s in leaks[:5]:
            print(f"    [{k}] '{p}' in: {s}")
print("\nDone.")
