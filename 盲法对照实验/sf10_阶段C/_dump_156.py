# -*- coding: utf-8 -*-
import io, os, re, struct
import olefile

BASE = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段C\_raw"

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

for n in [156]:
    p = os.path.join(BASE, f"倪醫師病案紀錄 ({n}).doc")
    full = extract(p)
    blocks = split_blocks(full)
    with io.open(os.path.join(OUT, f"doc{n}_allblocks.txt"), "w", encoding="utf-8") as f:
        for idx, b in enumerate(blocks, 1):
            f.write(f"\n\n===== doc({n}) 第{idx}块 =====\n\n{b}")
    print(f"doc{n}: {len(blocks)} blocks")
