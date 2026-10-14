# -*- coding: utf-8 -*-
"""Final symptom build: truncate each symptom section at 診斷 label; drop 西醫診斷 section."""
import io, os, re

OUT = r"D:\projectAGI\nhx\盲法对照实验"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

SYM_HEADERS = ["來診原因","問診","望診","觸診","脈診","耳診"]

def truncate_at_diagnosis(body):
    m = re.search(r"診斷[：:]", body)
    if m:
        return body[:m.start()].rstrip()
    return body.rstrip()

for cid in CASE_IDS:
    full = io.open(os.path.join(OUT, "full", f"医案{cid}_full.txt"), encoding="utf-8").read()
    # locate headers by position
    positions = []
    for h in SYM_HEADERS:
        for m in re.finditer(h, full):
            positions.append((m.start(), h))
    # also find last 診斷 position (diagnosis boundary)
    diag_positions = [m.start() for m in re.finditer(r"診斷[：:]", full)]
    last_diag = max(diag_positions) if diag_positions else len(full)
    positions = [(p, h) for p, h in positions if p < last_diag]
    positions.sort()
    # merge adjacent / dedup same header (keep first occurrence position)
    uniq = []
    seen = set()
    for p, h in positions:
        if h in seen:
            continue
        seen.add(h)
        uniq.append((p, h))
    uniq.sort()
    parts = []
    for i, (p, h) in enumerate(uniq):
        end = uniq[i+1][0] if i+1 < len(uniq) else last_diag
        body = full[p+len(h):end].strip()
        body = truncate_at_diagnosis(body)
        if body:
            parts.append(f"【{h}】\n{body}")
    with io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 首诊（盲法对照实验·仅症状输入）\n\n" + "\n\n".join(parts))

print("=== final verify ===")
bad = []
for cid in CASE_IDS:
    sym = io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), encoding="utf-8").read()
    leak_diag = ("診斷" in sym) or ("診断" in sym)
    leak_pres = ("針灸處方" in sym) or ("針灸处方" in sym) or ("中藥處方" in sym)
    has_shi = ("師：" in sym) or ("(師：" in sym)
    if leak_diag or leak_pres:
        bad.append(cid)
    print(f"医案{cid:>3} | len={len(sym):>4} | 诊断:{'泄露!' if leak_diag else 'ok'} | 处方:{'泄露!' if leak_pres else 'ok'} | 师注:{'有' if has_shi else '无'}")
print("BAD:", bad)
