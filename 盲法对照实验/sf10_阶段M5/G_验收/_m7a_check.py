# -*- coding: utf-8 -*-
"""M7-A 病例身份批量核验：组装清单 × case_list.json × 盲法症状文件头部 × full 文件存在性"""
import csv, json, os, re, hashlib, io

ROOT = r"D:\projectAGI\nhx\盲法对照实验"
ZL = os.path.join(ROOT, "sf10_阶段D", "组装清单.csv")
CL = os.path.join(ROOT, "盲法93", "case_list.json")
SYMP_DIR = os.path.join(ROOT, "盲法93", "symptoms")
PRES_DIR = os.path.join(ROOT, "盲法93", "prescriptions")
FULL_DIR = os.path.join(ROOT, "全集针灸首诊", "full")
OUT_MAP = os.path.join(ROOT, "sf10_阶段M5", "G_验收", "病例映射.csv")

# 1. 读组装清单
rows = []
with io.open(ZL, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows.append(r)
print("组装清单行数:", len(rows))

# 2. 读 case_list.json
with io.open(CL, encoding="utf-8") as f:
    clist = json.load(f)
print("case_list.json 成员数:", len(clist))

zl_ids = [r["case_id"] for r in rows]
print("case_list == 组装清单:", sorted(clist) == sorted(zl_ids))
only_cl = sorted(set(clist) - set(zl_ids))
only_zl = sorted(set(zl_ids) - set(clist))
if only_cl: print("仅在 case_list:", only_cl)
if only_zl: print("仅在组装清单:", only_zl)

# 3. 逐案核验
anomalies = []
map_rows = []
hdr_re = re.compile(r"doc\((\d+)\)")
for r in rows:
    cid, doc, block = r["case_id"], r["doc"], r["block"]
    sym = os.path.join(SYMP_DIR, cid + "_symptoms.txt")
    pres = os.path.join(PRES_DIR, cid + "_prescription.txt")
    full = os.path.join(FULL_DIR, cid + "_full.txt")
    exists = {"sym": os.path.exists(sym), "pres": os.path.exists(pres), "full": os.path.exists(full)}
    doc_in_header = None
    first_line = ""
    if exists["sym"]:
        with io.open(sym, encoding="utf-8") as f:
            first_line = f.readline().strip()
        m = hdr_re.search(first_line)
        if m:
            doc_in_header = m.group(1)
        else:
            anomalies.append((cid, "症状文件头部无 doc(N)", first_line[:60]))
    else:
        anomalies.append((cid, "缺症状文件", sym))
    if exists["pres"] is False:
        anomalies.append((cid, "缺处方文件", pres))
    if exists["full"] is False:
        anomalies.append((cid, "缺full文件", full))
    if doc_in_header is not None and doc_in_header != doc:
        anomalies.append((cid, "头部doc号与组装清单不符", f"头部doc({doc_in_header}) vs 清单doc({doc})"))
    map_rows.append({
        "盲法案号": cid, "原始doc号": doc, "块号": block,
        "就诊类型": r["visit_type"], "患者链": r["chain"],
        "症状文件路径": sym, "处方文件路径": pres, "full文件路径": full,
        "头部doc号": doc_in_header or "", "一致性": "OK" if not any(a[0] == cid for a in anomalies) else "CHECK"
    })

with io.open(OUT_MAP, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(map_rows[0].keys()))
    w.writeheader(); w.writerows(map_rows)
print("映射CSV已写:", OUT_MAP, "行数:", len(map_rows))

print("\n=== 异常清单 ===")
if not anomalies:
    print("无异常")
for a in anomalies:
    print(a)
