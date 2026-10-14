# -*- coding: utf-8 -*-
"""Trace old fenxi case texts: fuzzy-match each fenxi 主诉 against ALL 358 .doc 來診原因.
Goal: find which doc(N) actually contains the case the fenxi describes."""
import io, os, re, struct, json, difflib
import olefile, opencc

BASE = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇"
SRC = os.path.join(BASE, "含針灸治療醫案", "首診醫案")
FENXI = os.path.join(SRC, "fenxi")
OUT = r"D:\projectAGI\nhx\盲法对照实验"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

cc = opencc.OpenCC('t2s')

def extract(path):
    ole = olefile.OleFileIO(path)
    wd = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    use_tbl = (flags & 0x0200) != 0
    tbl = ole.openstream("1Table").read() if use_tbl else wd
    fcClx, lcbClx = struct.unpack_from("<II", wd, 0x01A2)
    clx = tbl[fcClx:fcClx+lcbClx]
    i = 0; pcds = []
    while i < len(clx):
        t = clx[i]
        if t == 0x01:
            cb = struct.unpack_from("<H", clx, i+1)[0]; i += 3 + cb
        elif t == 0x02:
            lcb = struct.unpack_from("<I", clx, i+1)[0]
            plcfpcd = clx[i+5:i+5+lcb]; i += 5 + lcb
            n = (lcb - 4) // 12
            cps = struct.unpack_from("<%dI" % (n+1), plcfpcd, 0)
            base = 4*(n+1)
            for k in range(n):
                pcd = plcfpcd[base+8*k:base+8*k+8]
                fc = struct.unpack_from("<I", pcd, 2)[0]
                pcds.append((cps[k], cps[k+1], fc))
        else:
            i += 1
    parts = []
    for cpStart, cpEnd, fc in sorted(pcds):
        compressed = (fc & 0x40000000) != 0
        realfc = fc & 0x3FFFFFFF
        length = cpEnd - cpStart
        if compressed:
            raw = wd[realfc:realfc+length]
            try: s = raw.decode("gbk")
            except Exception: s = raw.decode("cp1252", errors="replace")
        else:
            raw = wd[realfc:realfc+length*2]
            s = raw.decode("utf-16-le", errors="replace")
        parts.append(s)
    txt = "".join(parts)
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", txt)

def zhusu_from_full(full):
    m = re.search(r"來診原因[：:︰]?\s*(.*?)(問診|脈診|望診|診斷|針灸處方|針[：:]|中藥處方|複診)", full, re.S)
    if m:
        return m.group(1).strip()[:120]
    return full[:120]

def norm(s):
    s = cc.convert(s)
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", s)
    return s

# build doc index: number -> (raw 來診原因, norm)
doc_index = {}
for n in range(1, 359):
    p = os.path.join(BASE, f"倪醫師病案紀錄 ({n}).doc")
    if not os.path.exists(p):
        continue
    try:
        full = extract(p)
        zs = zhusu_from_full(full)
        doc_index[n] = (zs, norm(zs))
    except Exception as e:
        doc_index[n] = ("", "")
print(f"indexed {len(doc_index)} docs")

# fenxi 主诉
def fx_zhusu(cid):
    t = io.open(os.path.join(FENXI, f"医案{cid}_盲法辨证分析.txt"), encoding="utf-8").read()
    m = re.search(r"【原案症状信息[^】]*】\n(.*?)\n\n", t, re.S)
    block = m.group(1) if m else ""
    for line in block.split("\n"):
        if line.startswith("- 主诉") or line.startswith("- 主訴"):
            return line.split("：", 1)[1].strip() if "：" in line else line.split(":", 1)[1].strip()
    return ""

results = []
for cid in CASE_IDS:
    fx = fx_zhusu(cid)
    nfx = norm(fx)
    if not nfx:
        results.append({"case": cid, "fx": fx[:40], "best": None, "score": 0})
        continue
    best_n, best_score, best_cont = None, 0.0, False
    for n, (raw, nraw) in doc_index.items():
        if not nraw:
            continue
        cont = (nfx[:20] in nraw) or (nraw[:20] in nfx)
        ratio = difflib.SequenceMatcher(None, nfx[:40], nraw[:40]).ratio()
        score = ratio + (0.5 if cont else 0)
        if score > best_score:
            best_n, best_score, best_cont = n, score, cont
    same = "SAME" if best_n == cid else ("ALIGN" if best_n in CASE_IDS else "OTHER")
    results.append({"case": cid, "fx": fx[:40], "best_doc": best_n, "score": round(best_score,2), "cont": best_cont, "loc": same,
                    "best_raw": (doc_index.get(best_n) or ("",""))[0][:40]})
    print(f"fenxi医案{cid:>3} | 命中doc({best_n}) | score={best_score:.2f} cont={best_cont} | {same} | fx={fx[:30]} | doc={ (doc_index.get(best_n) or ('',''))[0][:30]}")

json.dump(results, io.open(os.path.join(OUT, "_trace_src.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
same_cnt = sum(1 for r in results if r["loc"] == "SAME")
align_cnt = sum(1 for r in results if r["loc"] == "ALIGN")
other_cnt = sum(1 for r in results if r["loc"] == "OTHER")
print(f"\nSAME(编号即内容): {same_cnt} | ALIGN(命中另一首诊doc): {align_cnt} | OTHER(命中非首诊doc或未命中): {other_cnt}")
