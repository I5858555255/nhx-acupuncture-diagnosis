# -*- coding: utf-8 -*-
"""Extract raw block texts for slice2 cases. Dump to _raw/ for human reading."""
import io, os, re, struct, json
import olefile, opencc

BASE = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\_raw"
os.makedirs(OUT, exist_ok=True)

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

def split_blocks(full):
    parts = re.split(r"(倪醫師病案紀錄)", full)
    blocks = []
    i = 1
    while i < len(parts):
        blocks.append(parts[i] + parts[i+1] if i+1 < len(parts) else parts[i])
        i += 2
    return [b for b in blocks if len(b) > 20]

# Cases to dump: (case_id, doc_num, block_idx)
cases = [
    ("156_06", 156, 6),
    ("160_01", 160, 1),
    ("178_01", 178, 1),
    ("194_01", 194, 1),
    ("195_01", 195, 1),
    ("198_01", 198, 1),
    ("199_01", 199, 1),
    ("1_01", 1, 1),
    ("200_01", 200, 1),
    ("201_01", 201, 1),
    ("202_01", 202, 1),
    ("207_01", 207, 1),
    ("208_01", 208, 1),
    ("209_01", 209, 1),
    ("212_01", 212, 1),
    ("213_01", 213, 1),
    ("214_01", 214, 1),
    ("216_01", 216, 1),
    ("216_02", 216, 2),
]

# Also dump full docs for chain references
extra_docs = [198, 199, 200, 201, 202, 216]

# Cache extracted full texts by doc number
doc_cache = {}
def get_blocks(n):
    if n in doc_cache: return doc_cache[n]
    p = os.path.join(BASE, f"倪醫師病案紀錄 ({n}).doc")
    if not os.path.exists(p):
        doc_cache[n] = None
        return None
    full = extract(p)
    blocks = split_blocks(full)
    doc_cache[n] = blocks
    return blocks

# Dump each case block
for cid, n, bidx in cases:
    blocks = get_blocks(n)
    if blocks is None:
        print(f"MISSING doc {n}")
        continue
    if bidx > len(blocks):
        print(f"BLOCK MISSING doc {n} block {bidx}, total blocks={len(blocks)}")
        continue
    b = blocks[bidx-1]
    with io.open(os.path.join(OUT, f"{cid}_block.txt"), "w", encoding="utf-8") as f:
        f.write(f"doc({n}) 第{bidx}块 (共{len(blocks)}块)\n\n{b}")
    print(f"OK {cid}: doc({n}) block {bidx}/{len(blocks)}, len={len(b)}")

# Dump extra full docs for chain reading
for n in extra_docs:
    blocks = get_blocks(n)
    if blocks is None: continue
    with io.open(os.path.join(OUT, f"doc{n}_allblocks.txt"), "w", encoding="utf-8") as f:
        for idx, b in enumerate(blocks, 1):
            f.write(f"\n\n===== doc({n}) 第{idx}块 =====\n\n{b}")
    print(f"DUMP doc{n}: {len(blocks)} blocks")
