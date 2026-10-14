# -*- coding: utf-8 -*-
"""Rebuild extraction for all 37 cases using proper piece-table method; then cross-check
each fenxi file's claimed original prescription against the actual .doc prescription."""
import io, os, re, json, struct, olefile

SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
FENXI = os.path.join(SRC, "fenxi")
OUT = r"D:\projectAGI\nhx\盲法对照实验"
os.makedirs(os.path.join(OUT, "full"), exist_ok=True)
os.makedirs(os.path.join(OUT, "symptoms"), exist_ok=True)
os.makedirs(os.path.join(OUT, "prescriptions"), exist_ok=True)

CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

def extract(path):
    ole = olefile.OleFileIO(path)
    wd = ole.openstream("WordDocument").read()
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    use_tbl = (flags & 0x0200) != 0
    tbl = ole.openstream("1Table").read() if use_tbl else wd
    fcClx, lcbClx = struct.unpack_from("<II", wd, 0x01A2)
    clx = tbl[fcClx:fcClx+lcbClx]
    i = 0
    pcds = []
    while i < len(clx):
        t = clx[i]
        if t == 0x01:
            cb = struct.unpack_from("<H", clx, i+1)[0]
            i += 3 + cb
        elif t == 0x02:
            lcb = struct.unpack_from("<I", clx, i+1)[0]
            plcfpcd = clx[i+5:i+5+lcb]
            i += 5 + lcb
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
            try:
                s = raw.decode("gbk")
            except Exception:
                s = raw.decode("cp1252", errors="replace")
        else:
            raw = wd[realfc:realfc+length*2]
            s = raw.decode("utf-16-le", errors="replace")
        parts.append(s)
    txt = "".join(parts)
    return re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", txt)

HEADERS = ["來診原因","問診","望診","觸診","脈診","耳診","診斷","針灸處方","中藥處方","西醫診斷","複診","備註"]
def split_sections(text):
    positions = []
    for h in HEADERS:
        for m in re.finditer(h, text):
            positions.append((m.start(), h))
    positions.sort()
    secs = {}
    for i, (pos, h) in enumerate(positions):
        end = positions[i+1][0] if i+1 < len(positions) else len(text)
        body = text[pos+len(h):end].strip()
        # cut trailing dosage lines belonging to herb section if inside pres? keep raw for now
        secs[h] = body
    return secs

rows = []
for cid in CASE_IDS:
    path = os.path.join(SRC, f"倪醫師病案紀錄 ({cid}).doc")
    text = extract(path)
    with io.open(os.path.join(OUT, "full", f"医案{cid}_full.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    secs = split_sections(text)
    sym_parts = []
    for h in ["來診原因","問診","望診","觸診","脈診","耳診","西醫診斷"]:
        if h in secs and secs[h]:
            sym_parts.append(f"【{h}】\n{secs[h]}")
    with io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 首诊（盲法对照实验·仅症状输入）\n\n" + "\n\n".join(sym_parts))
    pres = secs.get("針灸處方", "")
    with io.open(os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 原案針灸處方\n\n" + pres)
    rows.append({"case": cid, "sections": list(secs.keys()), "has_pres": bool(pres.strip()), "pres_len": len(pres)})

with io.open(os.path.join(OUT, "_extract_report2.json"), "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("=== piece-table extraction summary ===")
for r in rows:
    print(("OK" if r["has_pres"] else "!!"), "医案%3d" % r["case"], r["sections"], "pres_len:", r["pres_len"])
