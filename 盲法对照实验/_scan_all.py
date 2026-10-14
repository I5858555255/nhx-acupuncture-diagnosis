# -*- coding: utf-8 -*-
"""Full scan of all 358 docs: split into visit blocks; detect 針灸處方; classify 首诊/覆诊;
extract complete text + symptoms + prescription for every acupuncture first-visit block."""
import io, os, re, struct, json, csv
import olefile, opencc

BASE = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇"
OUT = r"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊"
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "full"), exist_ok=True)
os.makedirs(os.path.join(OUT, "symptoms"), exist_ok=True)
os.makedirs(os.path.join(OUT, "prescriptions"), exist_ok=True)

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

RE_SLASH = re.compile(r"(\d{1,4})[/\-.](\d{1,2})[/\-.](\d{1,4})")
RE_CN = re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日")
RE_8 = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")
def valid_date(y, m, d):
    try:
        if not (1900 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31):
            return False
        import calendar
        calendar.monthrange(y, m)
        return d <= calendar.monthrange(y, m)[1]
    except Exception:
        return False
def norm_date_at(text, pos):
    """Return first valid date (normalized yyyy-mm-dd) at/after pos, else None."""
    seg = text[pos:pos+120]
    for pat in (RE_CN, RE_SLASH, RE_8):
        for m in pat.finditer(seg):
            g = m.groups()
            if len(g) == 3:
                if pat is RE_CN:
                    y, mo, d = int(g[0]), int(g[1]), int(g[2])
                elif pat is RE_8:
                    y, mo, d = int(g[0]), int(g[1]), int(g[2])
                else:
                    a, b, c = int(g[0]), int(g[1]), int(g[2])
                    if a > 31: y, mo, d = a, b, c
                    elif c > 31: y, mo, d = c, a, b
                    else: y, mo, d = c, a, b
                if valid_date(y, mo, d):
                    return f"{y:04d}-{mo:02d}-{d:02d}"
    return None

HEADERS = ["來診原因","問診","望診","觸診","脈診","耳診","診斷","針灸處方","中藥處方","備註","複診","覆診"]
def split_blocks(full):
    parts = re.split(r"(倪醫師病案紀錄)", full)
    blocks = []
    i = 1
    while i < len(parts):
        blocks.append(parts[i] + parts[i+1] if i+1 < len(parts) else parts[i])
        i += 2
    return [b for b in blocks if len(b) > 20]

def block_info(docn, idx, block):
    pos_chu = block.find("初診日期")
    d_chu = norm_date_at(block, pos_chu) if pos_chu >= 0 else None
    pos_lai = block.find("來診日期")
    d_lai = norm_date_at(block, pos_lai) if pos_lai >= 0 else None
    has_acup = bool(re.search(r"針灸處方[：:]|針[：:](?!灸)", block)) and not re.search(r"針灸處方[：:]\s*$", block)
    # first-visit: 初診日期 == 來診日期 (date method); both present & unequal => follow-up, no fallback
    is_first = False
    if d_chu is not None and d_lai is not None:
        is_first = (d_chu == d_lai)
    else:
        m_no = re.search(r"來診日期[：:]?\s*(\d{2,4})[—\-–](\d{1,2})\D", block)
        if m_no and int(m_no.group(2)) == 1:
            is_first = True
        elif m_no and int(m_no.group(2)) > 1:
            is_first = False
        elif re.search(r"覆診|複診|回診|二診|第二診|再診|服前方|服藥後|服藥後數小時", block):
            is_first = False
        else:
            is_first = bool(re.search(r"來診原因[：:]", block))
    m_reason = re.search(r"來診原因[：:︰]?\s*([^問診診斷]{2,80})", block)
    reason = m_reason.group(1).strip()[:60] if m_reason else ""
    m_diag = re.search(r"診斷[：:]\s*([^針灸中藥備註]{2,60})", block)
    diag = m_diag.group(1).strip()[:40] if m_diag else ""
    return {"doc": docn, "block": idx, "初診日期": d_chu, "來診日期": d_lai,
            "含針灸": has_acup, "首诊": is_first, "主訴": reason, "診斷": diag}

# ---- scan ----
rows = []
all_blocks = 0
for n in range(1, 359):
    p = os.path.join(BASE, f"倪醫師病案紀錄 ({n}).doc")
    if not os.path.exists(p):
        continue
    try:
        full = extract(p)
    except Exception as e:
        rows.append({"doc": n, "error": str(e)})
        continue
    blocks = split_blocks(full)
    for idx, b in enumerate(blocks, 1):
        all_blocks += 1
        info = block_info(n, idx, b)
        rows.append(info)

# ---- summary ----
n_acup = sum(1 for r in rows if r.get("含針灸"))
n_first_acup = sum(1 for r in rows if r.get("含針灸") and r.get("首诊"))
n_follow_acup = sum(1 for r in rows if r.get("含針灸") and not r.get("首诊"))
n_first_all = sum(1 for r in rows if r.get("首诊"))
print(f"总块数={all_blocks}, 含針灸块={n_acup}, 针灸首诊块={n_first_acup}, 针灸覆诊块={n_follow_acup}, 全部首诊块={n_first_all}")

# CSV + json
with io.open(os.path.join(OUT, "扫描清单.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["doc","block","初診日期","來診日期","首诊","含針灸","主訴","診斷"])
    w.writeheader()
    for r in rows:
        if r.get("error"): continue
        w.writerow({k: r.get(k, "") for k in w.fieldnames})
json.dump(rows, io.open(os.path.join(OUT, "_scan_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- extract first-visit acup blocks ----
# re-extract with full text to save
saved = 0
for n in range(1, 359):
    p = os.path.join(BASE, f"倪醫師病案紀錄 ({n}).doc")
    if not os.path.exists(p): continue
    try:
        full = extract(p)
    except Exception:
        continue
    blocks = split_blocks(full)
    for idx, b in enumerate(blocks, 1):
        pos_chu = b.find("初診日期")
        d_chu = norm_date_at(b, pos_chu) if pos_chu >= 0 else None
        pos_lai = b.find("來診日期")
        d_lai = norm_date_at(b, pos_lai) if pos_lai >= 0 else None
        has_acup = bool(re.search(r"針灸處方[：:]|針[：:](?!灸)", b)) and not re.search(r"針灸處方[：:]\s*$", b)
        is_first = False
        if d_chu is not None and d_lai is not None:
            is_first = (d_chu == d_lai)
        else:
            m_no = re.search(r"來診日期[：:]?\s*(\d{2,4})[—\-–](\d{1,2})\D", b)
            if m_no:
                is_first = (int(m_no.group(2)) == 1)
            elif re.search(r"覆診|複診|回診|二診|第二診|再診|服前方|服藥後", b):
                is_first = False
            else:
                is_first = bool(re.search(r"來診原因[：:]", b))
        if not (has_acup and is_first):
            continue
        # sections
        secs = {}
        for h in HEADERS:
            m = re.search(re.escape(h) + r"[：:︰]?", b)
            if m:
                secs[h] = m.start()
        sym_parts = []
        for h in ["來診原因","問診","望診","觸診","脈診","耳診"]:
            if h in secs:
                end = min([v for k, v in secs.items() if k != h and v > secs[h]] or [len(b)])
                body = b[secs[h]+len(h)+1:end].strip()
                m = re.search(r"診斷[：:]", body)
                if m: body = body[:m.start()].strip()
                if body:
                    sym_parts.append(f"【{h}】\n{body}")
        pres = ""
        if "針灸處方" in secs:
            end = min([v for k, v in secs.items() if k in ("中藥處方","備註") and v > secs["針灸處方"]] or [len(b)])
            pres = b[secs["針灸處方"]+len("針灸處方")+1:end].strip()
        elif "針灸處方" not in secs and re.search(r"針[：:](?!灸)", b):
            m = re.search(r"針[：:](?!灸)", b)
            end = min([v for k, v in secs.items() if k in ("中藥處方","備註") and v > m.start()] or [len(b)])
            pres = b[m.end():end].strip()
        key = f"{n}_{idx:02d}"
        with io.open(os.path.join(OUT, "full", f"{key}_full.txt"), "w", encoding="utf-8") as f:
            f.write(f"doc({n}) 第{idx}块 首诊·含針灸\n\n" + b)
        with io.open(os.path.join(OUT, "symptoms", f"{key}_symptoms.txt"), "w", encoding="utf-8") as f:
            f.write(f"doc({n}) 第{idx}块 首诊·仅症状（盲法对照用）\n\n" + "\n\n".join(sym_parts))
        with io.open(os.path.join(OUT, "prescriptions", f"{key}_prescription.txt"), "w", encoding="utf-8") as f:
            f.write(f"doc({n}) 第{idx}块 原案針灸處方\n\n" + pres)
        saved += 1
print(f"已保存针灸首诊块: {saved}")
