# -*- coding: utf-8 -*-
"""M7-A 来源文件 SHA-256 清单生成"""
import hashlib, os, io

ROOT = r"D:\projectAGI\nhx\盲法对照实验"
OUT = os.path.join(ROOT, "sf10_阶段M5", "G_验收", "来源文件SHA256清单.md")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

groups = []

# 1. case_list.json
groups.append(("case_list.json", [os.path.join(ROOT, "盲法93", "case_list.json")]))

# 2. 93 symptoms + 93 prescriptions
sym_dir = os.path.join(ROOT, "盲法93", "symptoms")
pres_dir = os.path.join(ROOT, "盲法93", "prescriptions")
groups.append(("盲法93 symptoms (93)", [os.path.join(sym_dir, f) for f in sorted(os.listdir(sym_dir))]))
groups.append(("盲法93 prescriptions (93)", [os.path.join(pres_dir, f) for f in sorted(os.listdir(pres_dir))]))

# 3. full\ 全量 (140)
full_dir = os.path.join(ROOT, "全集针灸首诊", "full")
groups.append(("全集针灸首诊 full (140)", [os.path.join(full_dir, f) for f in sorted(os.listdir(full_dir))]))

# 4. 组装清单
groups.append(("组装清单.csv", [os.path.join(ROOT, "sf10_阶段D", "组装清单.csv")]))

# 5. 残余归因表×2
c1 = os.path.join(ROOT, "sf10_阶段M5", "C_残余归因", "残余归因表_分片1.csv")
c2 = os.path.join(ROOT, "sf10_阶段M5", "C_残余归因", "残余归因表_分片2.csv")
groups.append(("残余归因表×2", [c1, c2]))

# 6. M6-E 报告
groups.append(("M6-E-候选优先级清单.md", [os.path.join(ROOT, "sf10_阶段M5", "G_验收", "M6-E-候选优先级清单.md")]))

lines = ["# M7-A 来源文件 SHA-256 清单", "",
         "> 生成方式：SHA-256，64KB 分块读取。生成日期：2026-10-14。", ""]
total = 0
for name, paths in groups:
    lines.append("## " + name)
    for p in paths:
        total += 1
        lines.append("- `%s` — `%s`" % (os.path.relpath(p, ROOT), sha(p)))
    lines.append("")
lines.append("> 合计 %d 个文件。" % total)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("SHA清单已写:", OUT, "文件数:", total)
