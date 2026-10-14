# -*- coding: utf-8 -*-
"""Patch extraction: capture '針:'-style prescription headers; verify symptoms files have no 診斷 leak."""
import io, os, re, json, struct, olefile

SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
OUT = r"D:\projectAGI\nhx\盲法对照实验"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

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

# section headers with regex: 針灸處方, or standalone 針:
HEADER_RE = [
    ("來診原因", "來診原因"), ("問診", "問診"), ("望診", "望診"), ("觸診", "觸診"),
    ("脈診", "脈診"), ("耳診", "耳診"), ("診斷", "診斷"), ("西醫診斷", "西醫診斷"),
    ("針灸處方", "針灸處方"), ("針", r"針(?![後灸][^\n]{0,3}禁忌)[：:]"),  # standalone 針: 
    ("中藥處方", "中藥處方"), ("備註", "備註"), ("複診", "複診"),
]
def split_sections(text):
    positions = []
    for name, pat in HEADER_RE:
        for m in re.finditer(pat, text):
            positions.append((m.start(), name))
    positions.sort()
    # keep the FIRST occurrence of each name (avoid 針 matching 針灸處方 etc.)
    seen = set(); uniq = []
    for pos, name in positions:
        if name in seen:
            continue
        # if 針 name matched inside 針灸處方, skip
        if name == "針" and "針灸處方" in text[max(0,pos-5):pos+5]:
            continue
        seen.add(name); uniq.append((pos, name))
    uniq.sort()
    secs = {}
    for i, (pos, name) in enumerate(uniq):
        end = uniq[i+1][0] if i+1 < len(uniq) else len(text)
        secs[name] = text[pos+len(name):end].strip() if name != "針" else text[pos+1:end].strip()
    return secs

for cid in CASE_IDS:
    path = os.path.join(SRC, f"倪醫師病案紀錄 ({cid}).doc")
    text = extract(path)
    secs = split_sections(text)
    sym_parts = []
    for h in ["來診原因","問診","望診","觸診","脈診","耳診","西醫診斷"]:
        if h in secs and secs[h]:
            sym_parts.append(f"【{h}】\n{secs[h]}")
    with io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 首诊（盲法对照实验·仅症状输入）\n\n" + "\n\n".join(sym_parts))
    pres = secs.get("針灸處方", "") or secs.get("針", "")
    with io.open(os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 原案針灸處方\n\n" + pres)

# verify: no 診斷 leak in symptoms; report per-case pres
print("=== verify ===")
for cid in CASE_IDS:
    sym = io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), encoding="utf-8").read()
    leak = "診斷" in sym or "診断" in sym
    pres = io.open(os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt"), encoding="utf-8").read()
    pres_body = pres.replace("原案針灸處方","").strip()
    has_shi = ("師：" in sym) or ("(師：" in sym)
    print(f"医案{cid:>3} | 症状len={len(sym):>4} | 诊断泄露={'有!' if leak else '无'} | 处方len={len(pres_body):>4} | 含师注={has_shi} | 处方预览: {pres_body[:60]}")
