# -*- coding: utf-8 -*-
"""Extract 37 first-visit case records from legacy .doc files.
Strategy: decode whole file as utf-16-le (errors=replace); reconstruct text runs;
split by section headers; write symptoms-only (NO 診斷/針灸處方/中藥處方) and prescription-only files.
"""
import io, os, re, glob, json

SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
OUT = r"D:\projectAGI\nhx\盲法对照实验"
os.makedirs(os.path.join(OUT, "full"), exist_ok=True)
os.makedirs(os.path.join(OUT, "symptoms"), exist_ok=True)
os.makedirs(os.path.join(OUT, "prescriptions"), exist_ok=True)

CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

def extract_text(path):
    data = open(path, "rb").read()
    txt = data.decode("utf-16-le", errors="replace")
    # keep printable segments (CJK-heavy or ascii printable), discard replacement-char noise
    segs = []
    cur = []
    for ch in txt:
        ok = (0x4E00 <= ord(ch) <= 0x9FFF) or (0x3000 <= ord(ch) <= 0x303F) or \
             (0xFF00 <= ord(ch) <= 0xFFEF) or ch.isascii() and (ch.isprintable() or ch in "\r\n\t")
        if ok:
            cur.append(ch)
        else:
            if cur:
                s = "".join(cur)
                if s.strip():
                    segs.append(s)
                cur = []
    if cur:
        s = "".join(cur)
        if s.strip():
            segs.append(s)
    # join segments with newline when gap implies new content block; heuristic: merge if seg has punctuation ending
    text = "\n".join(segs)
    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

HEADERS = ["來診原因","問診","望診","觸診","脈診","耳診","診斷","針灸處方","中藥處方","西醫診斷","複診","備註"]
def split_sections(text):
    # find header positions (traditional + simplified tolerance)
    positions = []
    for h in HEADERS:
        for m in re.finditer(h, text):
            positions.append((m.start(), h))
    positions.sort()
    secs = {}
    for i, (pos, h) in enumerate(positions):
        end = positions[i+1][0] if i+1 < len(positions) else len(text)
        body = text[pos+len(h):end].strip()
        secs[h] = body
    return secs

report = []
problems = []
for cid in CASE_IDS:
    fname = f"倪醫師病案紀錄 ({cid}).doc"
    path = os.path.join(SRC, fname)
    if not os.path.exists(path):
        problems.append(f"{cid}: file missing")
        continue
    text = extract_text(path)
    # keep title/date line
    with io.open(os.path.join(OUT, "full", f"医案{cid}_full.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    secs = split_sections(text)
    # symptoms: chief complaint etc. exclude 診斷/針灸處方/中藥處方
    sym_parts = []
    for h in ["來診原因","問診","望診","觸診","脈診","耳診","西醫診斷"]:
        if h in secs and secs[h]:
            sym_parts.append(f"【{h}】\n{secs[h]}")
    sym_text = "\n\n".join(sym_parts)
    with io.open(os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 首诊（盲法对照实验·仅症状输入）\n\n" + sym_text)
    # prescription only
    pres = secs.get("針灸處方", "")
    with io.open(os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt"), "w", encoding="utf-8") as f:
        f.write(f"医案{cid} 原案針灸處方\n\n" + pres)
    # diagnostic info for the record (we keep it out of symptoms)
    report.append({"case": cid, "has_symptoms": bool(sym_text), "has_pres": bool(pres),
                   "len_full": len(text), "sections": list(secs.keys()),
                   "pres_text": pres[:120].replace("\n", " / ")})

with io.open(os.path.join(OUT, "_extract_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)

print("=== extraction summary ===")
for r in report:
    flag = "OK" if r["has_symptoms"] and r["has_pres"] else "!!"
    print(f"{flag} 医案{r['case']:>3}: secs={r['sections']} | pres: {r['pres_text'][:80]}")
print("\nproblems:", problems)
