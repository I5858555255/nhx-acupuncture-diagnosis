# -*- coding: utf-8 -*-
"""Robust alignment check: fenxi 主诉 vs doc 來診原因 (fuzzy); secondary: fenxi 原案选穴 vs doc prescription."""
import io, os, re, json, difflib
import opencc

SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
OUT = r"D:\projectAGI\nhx\盲法对照实验"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

cc = opencc.OpenCC('t2s')

def norm(s):
    s = cc.convert(s)
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s)
    return s

def fx_zhusu(path):
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r"【原案症状信息[^】]*】\n(.*?)\n\n", t, re.S)
    if not m:
        return ""
    block = m.group(1)
    for line in block.split("\n"):
        if line.startswith("- 主诉") or line.startswith("- 主訴"):
            return line.split("：", 1)[1].strip() if "：" in line else line.split(":",1)[1].strip()
    return block[:120]

def doc_zhusu(cid):
    full = io.open(os.path.join(OUT, "full", f"医案{cid}_full.txt"), encoding="utf-8").read()
    m = re.search(r"來診原因：?(.*?)(問診|脈診|望診|診斷|針灸處方|針：|中藥處方)", full, re.S)
    return m.group(1).strip() if m else full[:80]

results = []
for cid in CASE_IDS:
    fx = fx_zhusu(os.path.join(SRC, "fenxi", f"医案{cid}_盲法辨证分析.txt"))
    doc = doc_zhusu(cid)
    nf, nd = norm(fx), norm(doc)
    # containment: first 15 chars of the shorter one inside the longer
    cont = (nf[:15] in nd) or (nd[:15] in nf) if nf and nd else False
    ratio = difflib.SequenceMatcher(None, nf[:40], nd[:40]).ratio() if nf and nd else 0.0
    verdict = "ALIGNED" if (cont or ratio >= 0.62) else "MISMATCH"
    results.append({"case": cid, "fx": fx[:60], "doc": doc[:60], "cont": cont, "ratio": round(ratio,2), "verdict": verdict})
    print(f"医案{cid:>3} | {verdict:8s} | cont={cont} ratio={ratio:.2f} | fx={fx[:38]} | doc={doc[:38]}")

json.dump(results, io.open(os.path.join(OUT, "_align_check2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n_align = sum(1 for r in results if r["verdict"] == "ALIGNED")
print(f"\nALIGNED: {n_align}/37 -> {[r['case'] for r in results if r['verdict']=='ALIGNED']}")
