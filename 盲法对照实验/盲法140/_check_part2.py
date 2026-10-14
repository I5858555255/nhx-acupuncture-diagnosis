# -*- coding: utf-8 -*-
import json, re

path = r"D:\projectAGI\nhx\盲法对照实验\盲法140\_blind140_part2.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

expected = ["160_01","169_01","178_01","185_01","189_01","190_01","194_01","195_01","198_01","199_01","200_01","201_01","202_01","204_01","207_01","208_01","209_01","21_01","210_01","212_01","213_01","214_01","216_01","216_02","216_03","216_04","216_05","217_01","219_01"]

print("=== Self-check 1: JSON parse ===")
print("OK, parsed", len(data), "cases")

print("\n=== Self-check 2: key count == 29 and IDs match ===")
keys = sorted(data.keys())
exp_sorted = sorted(expected)
print("Match:", keys == exp_sorted)
if keys != exp_sorted:
    print("Missing:", set(exp_sorted) - set(keys))
    print("Extra:", set(keys) - set(exp_sorted))

print("\n=== Self-check 3: each case main points 5-8 non-empty ===")
bad3 = []
for cid, c in data.items():
    mp = c["主穴"]
    n = len(mp)
    if n < 5 or n > 8:
        bad3.append((cid, n))
    for p in mp:
        if not p or not p.strip():
            bad3.append((cid, "empty"))
print("Bad:", bad3 if bad3 else "None - all 5-8")

print("\n=== Self-check 4: layered union == main points set ===")
bad4 = []
for cid, c in data.items():
    mp = set(c["主穴"])
    layers = c["主穴分层"]
    union = set(layers["对症"]) | set(layers["俞募背俞"]) | set(layers["八脉交会"]) | set(layers["特效奇穴"])
    if mp != union:
        bad4.append((cid, "main-only:", mp - union, "layer-only:", union - mp))
    # check minimums
    if len(layers["对症"]) < 2:
        bad4.append((cid, "对症<2"))
    if len(layers["俞募背俞"]) < 1:
        bad4.append((cid, "俞募背俞<1"))
    if len(layers["八脉交会"]) < 1:
        bad4.append((cid, "八脉交会<1"))
print("Bad:", bad4 if bad4 else "None - all layers match")

print("\n=== Self-check 5: no forbidden words ===")
forbidden = ["診斷", "診断", "針灸處方", "针灸处方"]
raw = open(path, "r", encoding="utf-8").read()
hits = [w for w in forbidden if w in raw]
print("Forbidden hits:", hits if hits else "None")

print("\n=== Self-check 6: no () or / in point names ===")
# allowed compound names with /
allowed_slash = ["耳肝点/耳肾点"]
bad6 = []
for cid, c in data.items():
    for field in ["主穴", "佐穴", "备选"]:
        for p in c.get(field, []):
            if "（" in p or "）" in p or "(" in p or ")" in p:
                bad6.append((cid, field, p, "paren"))
            if "/" in p:
                # check if it's a known compound
                known_compounds = ["三间透后溪","迎香透内迎香","阳白透鱼腰","中府透云门","地仓透颊车","条口透承山","阳陵泉透阴陵泉","太阳透率谷"]
                if p not in known_compounds and p not in allowed_slash:
                    bad6.append((cid, field, p, "slash"))
print("Bad:", bad6 if bad6 else "None")

print("\n=== Self-check 7: spot check point names exist in knowledge base ===")
# Read knowledge base
kb_path = r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\针灸篇-知识条目整理.md"
kb = open(kb_path, "r", encoding="utf-8").read() if False else ""
# We'll just verify a sample of point names appear in the guide or special effect library
guide_path = r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\诊断与针灸实施指南.md"
guide = open(guide_path, "r", encoding="utf-8").read()
te_path = r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\特效库全量.json"
te = open(te_path, "r", encoding="utf-8").read()
zl_path = r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\治则手法库.json"
zl = open(zl_path, "r", encoding="utf-8").read()

all_names = set()
for cid, c in data.items():
    for p in c["主穴"]:
        # split + pairs and 透 compounds
        for part in re.split(r"[+透]", p):
            part = part.strip()
            if part:
                all_names.add(part)

combined = guide + te + zl
missing = []
for name in sorted(all_names):
    if name not in combined:
        missing.append(name)
print("Unique point fragments:", len(all_names))
print("Not found in references:", missing if missing else "None - all verified")

# Stats
print("\n=== Stats ===")
total_main = sum(len(c["主穴"]) for c in data.values())
print(f"主穴均数: {total_main/len(data):.2f}")
special_count = sum(1 for c in data.values() if c["主穴分层"]["特效奇穴"])
print(f"特效奇穴层非空案数: {special_count}")
zero_hit = 0
for cid, c in data.items():
    if "0命中" in c["推理要点"] or "0 命中" in c["推理要点"]:
        zero_hit += 1
print(f"反查0命中案数: {zero_hit}")
info_short = [cid for cid,c in data.items() if "信息不足" in c["辨证结论"]["虚实"] or "信息不足" in c["推理要点"]]
print(f"信息不足案数: {len(info_short)} -> {info_short}")
