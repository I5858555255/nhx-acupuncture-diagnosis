# -*- coding: utf-8 -*-
"""Debug FIB/piece-table parsing on two case files."""
import olefile, struct

paths = [
    r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案\倪醫師病案紀錄 (1).doc",
    r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案\倪醫師病案紀錄 (60).doc",
]
for p in paths:
    print("=" * 40)
    print("FILE:", p.split("\\")[-1])
    ole = olefile.OleFileIO(p)
    wd = ole.openstream("WordDocument").read()
    nFib = struct.unpack_from("<H", wd, 0x02)[0]
    flags = struct.unpack_from("<H", wd, 0x0A)[0]
    print("nFib:", nFib, "flags:", hex(flags))
    # fcClx at 0x01A2 per FibRgFcLcb97
    fcClx, lcbClx = struct.unpack_from("<II", wd, 0x01A2)
    print("fcClx@0x1A2:", fcClx, "lcbClx:", lcbClx)
    if 0 <= fcClx < len(wd) and 0 < lcbClx < 200:
        clx = wd[fcClx:fcClx+lcbClx]
        print("CLX first bytes:", clx[:20].hex())
    # also try scanning for plausible CLX: find 0x02 (Pcdt) preceded by lcb
    # heuristic: scan for sequences where clx starts with 0x01 or 0x02
    for probe in (0x000A, 0x0122, 0x00A2, 0x0112):
        try:
            fc, lcb = struct.unpack_from("<II", wd, probe)
            if 0 < lcb < 200 and 0 <= fc < len(wd):
                clx = wd[fc:fc+lcb]
                if clx[:1] in (b"\x01", b"\x02"):
                    print(f"probe@{hex(probe)}: fc={fc} lcb={lcb} clx={clx[:16].hex()}")
        except Exception:
            pass
