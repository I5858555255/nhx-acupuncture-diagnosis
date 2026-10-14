# -*- coding: utf-8 -*-
"""Extract raw block texts for slice5 cases. Dump to _raw5/ for human reading."""
import io, os, re, struct, json
import olefile, opencc

BASE = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\_raw5"
os.makedirs(OUT, exist_ok=True)

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

# Slice5 cases: case_id -> (doc_num, block_idx)
cases = [
    ("64_01", 64, 1),
    ("65_01", 65, 1),
    ("66_01", 66, 1),
    ("67_01", 67, 1),
    ("68_01", 68, 1),
    ("69_01", 69, 1),
    ("70_01", 70, 1),
    ("71_01", 71, 1),
    ("72_01", 72, 1),
    ("73_01", 73, 1),
    ("74_01", 74, 1),
    ("75_01", 75, 1),
    ("76_01", 76, 1),
    ("77_01", 77, 1),
    ("78_01", 78, 1),
    ("80_01", 80, 1),
    ("8_01", 8, 1),
]

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

# Also dump all blocks of doc 66 (anchor) and docs 64, 65 for chain judgment
for n in [64, 65, 66]:
    blocks = get_blocks(n)
    if blocks is None: continue
    with io.open(os.path.join(OUT, f"doc{n}_allblocks.txt"), "w", encoding="utf-8") as f:
        for idx, b in enumerate(blocks, 1):
            f.write(f"\n\n===== doc({n}) 第{idx}块 =====\n\n{b}")
    print(f"DUMP doc{n}: {len(blocks)} blocks")
