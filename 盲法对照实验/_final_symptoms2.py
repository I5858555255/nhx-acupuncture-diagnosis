# -*- coding: utf-8 -*-
"""Final symptom build v2: boundaries = ALL recognized headers; symptom sections truncated at 診斷."""
import io, os, re

OUT = r"D:\projectAGI\nhx\盲法对照实验"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

SYM_HEADERS = ["來診原因","問診","望診","觸診","脈診","耳診"]
ALL_HEADERS = SYM_HEADERS + ["診斷","西醫診斷","針灸處方","中藥處方","備註","複診","解說"]

def build(cid):
    full = io.open(os.path.join(OUT, "full", f"医案{cid}_full.txt"), encoding="utf-8").read()
    positions = []
    for h in ALL_HEADERS:
        for m in re.finditer(h, full):
            positions.append((m.start(), h))
    positions.sort()
    # dedup same header (first occurrence), but keep later 診斷 with content? use first occurrence of each
    seen = set(); uniq = []
    for p, h in positions:
        if h in seen:
            continue
        seen.add(h); uniq.append((p, h))
    uniq.sort()
    parts = []
    for i, (p, h) in enumerate(uniq):
        if h not in SYM_HEADERS:
            continue
        end = uniq[i+1][0] if i+1 < len(uniq) else len(full)
        body = full[p+len(h):end]
        # truncate at 診斷 within body
        m = re.search(r"診斷[：:]", body)
        if m:
            body = body[:m.start()]
        body = body.strip()
        if body:
            parts.append(f"【{h}】\n{body}")
    return "\n\n".join(parts)

for cid in CASE_IDS:
    sym = build(cid)
    with io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 首诊（盲法对照实验·仅症状输入）\n\n" + sym)

print("=== final verify v2 ===")
bad = []
for cid in CASE_IDS:
    sym = io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), encoding="utf-8").read()
    leak_diag = ("診斷" in sym) or ("診断" in sym)
    leak_pres = ("針灸處方" in sym) or ("針灸处方" in sym) or ("中藥處方" in sym) or ("針:" in sym) or ("針 ：" in sym)
    has_shi = ("師：" in sym) or ("(師：" in sym)
    if leak_diag or leak_pres:
        bad.append(cid)
    print(f"医案{cid:>3} | len={len(sym):>4} | 诊断:{'泄露!' if leak_diag else 'ok'} | 处方:{'泄露!' if leak_pres else 'ok'} | 师注:{'有' if has_shi else '无'}")
print("BAD:", bad)
