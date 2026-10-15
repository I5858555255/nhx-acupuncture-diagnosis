# -*- coding: utf-8 -*-
"""M8.1 哈希冻结清单"""
import os, io, hashlib
ROOT = r"D:\projectAGI\nhx"
BLIND = os.path.join(ROOT, "盲法对照实验")
G = os.path.join(BLIND, "sf10_阶段M5", "G_验收")

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(65536),b""): h.update(c)
    return h.hexdigest()

items = [
 ("v14 SKILL.md", os.path.join(ROOT,"doubao-acupuncture-diagnosis_v14r7","skill","SKILL.md")),
 ("v14 盲法预测JSON", os.path.join(G,"盲法v14r7","_blind93v14r7_results.json")),
 ("M8-A报告", os.path.join(G,"M8-A-R6-病例映射与原书核验.md")),
 ("M8-B报告", os.path.join(G,"M8-B-R6-触发扫描.md")),
 ("M8-A复算脚本", os.path.join(G,"_m8a_r6trace.py")),
 ("M8-B扫描脚本", os.path.join(G,"_m8b_scan.py")),
 ("R6反事实脚本", os.path.join(G,"_m81_cf.py")),
]
# references 4 文件
refdir = os.path.join(ROOT,"doubao-acupuncture-diagnosis_v14r7","skill","references")
if os.path.isdir(refdir):
    for f in sorted(os.listdir(refdir)):
        items.append(("references/"+f, os.path.join(refdir,f)))

lines=["# M8.1 哈希冻结清单","","> 冻结记录：v14/预测/报告/脚本 SHA-256。日期 2026-10-15。",""]
for name,p in items:
    if os.path.isfile(p):
        lines.append(f"- {name}: `{sha(p)}`  ({os.path.relpath(p,ROOT)})")
    else:
        lines.append(f"- {name}: [缺失] {p}")
io.open(os.path.join(G,"M8.1-哈希冻结清单.md"),"w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
