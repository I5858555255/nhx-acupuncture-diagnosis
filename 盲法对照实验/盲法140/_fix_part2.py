# -*- coding: utf-8 -*-
import json

path = r"D:\projectAGI\nhx\盲法对照实验\盲法140\_blind140_part2.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# A. Add inner case_id
for cid, c in data.items():
    c["case_id"] = cid

# B1. 185_01: 备选 "丰隆导痰" → "丰隆"
data["185_01"]["备选"] = ["丰隆"]
data["185_01"]["推理要点"] += "（丰隆为胃经络穴，导痰针法：针丰隆得气后提至皮层斜倒45度朝身体上方再捻，待酸麻后复斜下45度刺之，留针二十分钟。）"

# B2. 216_03: 佐穴 "廉泉方向" → "廉泉"
data["216_03"]["佐穴"] = ["神门", "廉泉"]
data["216_03"]["推理要点"] += "（舌麻取廉泉，向舌根方向刺。）"

# B3. 199_01: 备选 "梅花针拍击皮肤炎处" → "梅花针"
data["199_01"]["备选"] = ["梅花针"]
data["199_01"]["推理要点"] += "（梅花针拍击湿热皮肤炎患处放血，针头前部七支针形如榔头，拍击需稍用力，牛角制者为佳。）"

# B4. 178_01: 备选 "灸中脘隔姜" → "中脘"
data["178_01"]["备选"] = ["中脘"]
data["178_01"]["推理要点"] += "（胃寒重可于中脘行隔生姜灸，灸时感温热即止勿起泡。）"

# B5. 194_01: 备选 "灸足三里预防中风" → "足三里"
data["194_01"]["备选"] = ["足三里"]
data["194_01"]["推理要点"] += "（足三里行灸法预防中风，灸至不麻为度，可起水泡刺破放水，连灸数壮。）"

# B6. 198_01: 备选 "耳针肾膀胱区埋针" → "耳针肾膀胱区压痛点"
data["198_01"]["备选"] = ["肝一肝二肝三", "耳针肾膀胱区压痛点"]
data["198_01"]["推理要点"] += "（耳针肾膀胱区找压痛点埋图钉样耳针，胶布固定，留置4-7天保持干燥。）"

# Reorder keys: put case_id first
ordered = {}
for cid in sorted(data.keys()):
    c = data[cid]
    new_c = {"case_id": cid}
    for k, v in c.items():
        if k != "case_id":
            new_c[k] = v
    ordered[cid] = new_c

with open(path, "w", encoding="utf-8") as f:
    json.dump(ordered, f, ensure_ascii=False, indent=2)

# Verify
with open(path, "r", encoding="utf-8") as f:
    check = json.load(f)

print("Cases:", len(check))
print("All have inner case_id:", all("case_id" in c and c["case_id"] == cid for cid, c in check.items()))
print("185_01 备选:", check["185_01"]["备选"])
print("216_03 佐穴:", check["216_03"]["佐穴"])
print("199_01 备选:", check["199_01"]["备选"])
print("178_01 备选:", check["178_01"]["备选"])
print("194_01 备选:", check["194_01"]["备选"])
print("198_01 备选:", check["198_01"]["备选"])
print("195_01 备选 (should keep 耳针埋心的压痛点):", check["195_01"]["备选"])

# Forbidden word check
raw = open(path, "r", encoding="utf-8").read()
forbidden = ["診斷", "診断", "針灸處方", "针灸处方"]
hits = [w for w in forbidden if w in raw]
print("Forbidden hits:", hits if hits else "None")

# Check no () in point arrays
import re
bad = []
for cid, c in check.items():
    for field in ["主穴", "佐穴", "备选"]:
        for p in c.get(field, []):
            if "（" in p or "）" in p or "(" in p or ")" in p:
                bad.append((cid, field, p))
print("Paren in arrays:", bad if bad else "None")
