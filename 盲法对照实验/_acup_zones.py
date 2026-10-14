# -*- coding: utf-8 -*-
"""提取140个首诊块的针灸处方区段原文（原样保留，不做解析），供人工全文核读。
判定块内是否真有可解析的针灸方案内容。"""
import io, os, json, re, glob

OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
full_dir = os.path.join(OUT, "full")

# 140 首诊块（扫描清单为准）
rows = json.load(io.open(os.path.join(OUT, "_scan_all.json"), encoding="utf-8"))
first = [r for r in rows if r.get("含針灸") and r.get("首诊")]
first.sort(key=lambda r: (r["doc"], r["block"]))
print("首诊块数:", len(first))

SECTIONS = ["中藥處方", "解說", "備註", "複診", "覆診", "倪醫師病案紀錄"]

out = io.open(r"D:\projectAGI\nhx\盲法对照实验\_acup_zones_all.txt", "w", encoding="utf-8")
empty_cnt = 0
for r in first:
    key = "%d_%02d" % (r["doc"], r["block"])
    fp = os.path.join(full_dir, key + "_full.txt")
    if not os.path.exists(fp):
        out.write("=== %s [full文件缺失] ===\n\n" % key)
        continue
    block = io.open(fp, encoding="utf-8").read()
    # 去掉我们写入的页眉
    mh = re.search(r"\n\n", block)
    if mh:
        block = block[mh.end():]
    # 找针灸处方标题
    m = re.search(r"針灸處方[：:]|針[：:](?!灸)", block)
    if not m:
        out.write("=== %s [无針灸處方标题] 块头120字: %s ===\n\n" % (key, block[:120].replace("\n", " ")))
        continue
    start = m.end()
    ends = [block.find(s, start) for s in SECTIONS]
    ends = [e for e in ends if e >= 0]
    end = min(ends) if ends else len(block)
    zone = block[start:end].strip()
    if not zone:
        empty_cnt += 1
        out.write("=== %s [区段为空] 标题上下文: ...%s... ===\n\n" % (key, block[max(0, m.start()-30):min(len(block), m.end()+60)].replace("\n", " ")))
    else:
        out.write("=== %s 针灸处方区段原文 ===\n%s\n\n" % (key, zone))
out.close()
print("区段为空的块数:", empty_cnt)
print("已输出 _acup_zones_all.txt")
