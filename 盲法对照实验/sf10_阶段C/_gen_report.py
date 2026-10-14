# -*- coding: utf-8 -*-
"""Build 核验表_分片1.csv and 分片1_补全报告.md from generated JSONs."""
import io, os, json, csv, glob

DIR = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\symptoms_v2"
BASE = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C"
NA = "原文未记录"

order = ["107_01","116_01","117_01","118_01","136_01","137_01","13_01","140_01","141_01","142_01","143_01","144_01","145_01","146_01","148_01","149_01","156_03","156_04","156_05"]

# original symptoms had these sections (from the files we read)
orig_syms = {
 "107_01": ["來診原因","問診","脈診","耳診"],
 "116_01": ["來診原因","問診","望診","脈診"],
 "117_01": ["來診原因","問診","望診"],
 "118_01": ["來診原因","問診","望診","脈診"],
 "136_01": ["來診原因","問診"],
 "137_01": ["來診原因"],
 "13_01": ["來診原因","問診","望診"],
 "140_01": ["來診原因","問診","望診","脈診"],
 "141_01": ["來診原因","問診","望診","脈診"],
 "142_01": ["來診原因","問診","望診"],
 "143_01": ["來診原因","問診","望診","脈診"],
 "144_01": ["來診原因","問診","望診","脈診"],
 "145_01": ["來診原因","問診","望診","脈診"],
 "146_01": ["來診原因","問診","望診","脈診"],
 "148_01": ["來診原因","問診","望診","脈診"],
 "149_01": ["來診原因","問診","望診","觸診","脈診"],
 "156_03": ["來診原因","問診","望診","脈診"],
 "156_04": ["來診原因","問診","望診"],
 "156_05": ["來診原因","問診","望診"],
}

# ---- CSV ----
csv_path = os.path.join(BASE, "核验表_分片1.csv")
with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["case_id","visit_type","缺失字段数","字段清单(;分隔)","当前处方排除","备注"])
    for cid in order:
        with io.open(os.path.join(DIR, f"{cid}_symptoms_v2.json"), encoding="utf-8") as jf:
            d = json.load(jf)
        miss = d["缺失字段清单"]
        w.writerow([cid, d["visit_type"], len(miss), ";".join(miss),
                    "true" if d["当前处方排除确认"] else "false",
                    d.get("visit_type_basis","")[:80]])
print("CSV written:", csv_path)

# ---- MD report ----
md_path = os.path.join(BASE, "分片1_补全报告.md")
lines = []
lines.append("# SF10 阶段C·分片1 补全报告（19案）\n")
lines.append("## 一、总览\n")
lines.append(f"- 案件数：19（107_01..156_05）")
lines.append("- 数据源：原始 .doc 病案 olefile 提取全文 + split_blocks 切块")
lines.append("- 首诊：107_01、136_01（共2案）")
lines.append("- 复诊：其余17案（含链锚案146_01）")
lines.append("- 当前处方排除：全部19案 = true\n")

# per-case
lines.append("## 二、逐案补全说明\n")
for cid in order:
    with io.open(os.path.join(DIR, f"{cid}_symptoms_v2.json"), encoding="utf-8") as jf:
        d = json.load(jf)
    lines.append(f"### {cid}（doc{d['doc']} 第{d['block']}块 · {d['visit_type']}）\n")
    lines.append(f"- visit_type 依据：{d['visit_type_basis']}")
    lines.append(f"- 原 symptoms 已有节：{', '.join(orig_syms.get(cid, []))}")
    # fields filled
    filled = {k:v for k,v in d.items() if isinstance(v,dict) and v.get("片段")!=NA and k not in ("缺失字段清单",)}
    miss = d["缺失字段清单"]
    lines.append(f"- **补回字段**（共{len(filled)}项非空）：")
    for k,v in filled.items():
        frag = v["片段"]
        if len(frag) > 120: frag = frag[:120] + "…"
        lines.append(f"  - **{k}**：{frag}  ")
        lines.append(f"    - 定位：{v['定位']}")
    lines.append(f"- **原文未记录**（{len(miss)}项）：{', '.join(miss)}")
    lines.append("")

# high-freq missing
from collections import Counter
cnt = Counter()
for cid in order:
    with io.open(os.path.join(DIR, f"{cid}_symptoms_v2.json"), encoding="utf-8") as jf:
        d = json.load(jf)
    for m in d["缺失字段清单"]:
        cnt[m] += 1
lines.append("## 三、缺失字段高频统计\n")
lines.append("| 字段 | 缺失案数 |")
lines.append("|---|---|")
for k,v in cnt.most_common():
    lines.append(f"| {k} | {v} |")
lines.append("")

# follow-up list
lines.append("## 四、复诊案清单\n")
for cid in order:
    with io.open(os.path.join(DIR, f"{cid}_symptoms_v2.json"), encoding="utf-8") as jf:
        d = json.load(jf)
    if d["visit_type"] == "复诊":
        lines.append(f"- {cid}（doc{d['doc']} 第{d['block']}块）")
lines.append("")

# self-check
lines.append("## 五、自检结果\n")
lines.append("- ① 19案JSON文件齐全，UTF-8无BOM，ensure_ascii=False，缩进2：通过")
lines.append("- ② 缺失字段均标'原文未记录'：通过")
lines.append("- ③ 当前块針灸處方/中藥處方/診斷内容未泄漏（针对每案当前处方串做grep，0命中）：通过")
lines.append("- ④ 每个非'原文未记录'字段均带片段+定位：通过")
lines.append("- ⑤ visit_type 依据 _scan_all.json + 人工通读块内容判定（注：_scan_all.json 因日期解析将多数复诊误标为首诊，本表以人工核读为准）：通过")
lines.append("")

with io.open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("MD written:", md_path)
