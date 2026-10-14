# -*- coding: utf-8 -*-
"""Cross-check: fenxi-claimed original content vs actual .doc content for all 37 cases."""
import io, os, re, json

SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
FENXI = os.path.join(SRC, "fenxi")
OUT = r"D:\projectAGI\nhx\盲法对照实验"

CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]

SIMPMAP = str.maketrans({
    "闕":"阙","關":"关","衝":"冲","谿":"溪","節":"节","後":"后","髮":"发","髒":"脏","裡":"里","虛":"虚",
    "實":"实","陰":"阴","陽":"阳","膽":"胆","癱":"瘫","腫":"肿","醫":"医","藥":"药","處":"处","診":"诊",
    "問":"问","脈":"脉","復":"复","雙":"双","針":"针","經":"经","絡":"络","膚":"肤","導":"导","會":"会",
    "裡":"里","為":"为","與":"与","於":"于","體":"体","氣":"气","萬":"万","瀉":"泻","補":"补","熱":"热",
    "臨":"临","泣":"泣","頰":"颊","車":"车","陽":"阳","驗":"验","壓":"压","觸":"触","齒":"齿","齡":"龄",
    "年":"年","門":"门","間":"间","宮":"宫","覽":"览","曆":"历","發":"发","髮":"发","麵":"面","麵":"面",
    "烏":"乌","溫":"温","涼":"凉","庫":"库","醫":"医","癒":"愈","癒":"愈","針":"针","連":"连","圖":"图",
    "頸":"颈","項":"项","額":"额","顴":"颧","頷":"颔","頭":"头","顳":"颞","頁":"页","餘":"余","數":"数",
    "壺":"壶","藥":"药","飽":"饱","餓":"饿","牽":"牵","擊":"击","勢":"势","熱":"热","痠":"酸","痺":"痹",
})

def norm(s):
    s = re.sub(r"[（(][^）)]*[）)]", "", s)          # strip annotations
    s = s.translate(SIMPMAP)
    s = re.sub(r"[左右雙双][側边]?", "", s)          # strip left/right/both markers
    s = re.sub(r"腳|脚|手|足", "", s)                # risky? strip 脚/手/足 prefixes like 右脚公孙? keep for now? 
    s = s.replace("，", " ").replace("、", " ").replace("；", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def points_from(text):
    # split into point tokens by separators
    text = text.replace("＋", " ").replace("+", " ").replace("，", " ").replace("、", " ").replace("；", " ").replace("。", " ")
    text = re.sub(r"[（(][^）)]*[）)]", " ", text)
    toks = re.split(r"[\s,，、;；/]+", text)
    out = []
    for t in toks:
        t = t.translate(SIMPMAP).strip()
        t = re.sub(r"^(左|右|雙|双|兩|兩側|雙側|單側)[側边]?", "", t)
        t = t.strip(" ：:．.、")
        if t and len(t) >= 2:
            out.append(t)
    return out

results = []
for cid in CASE_IDS:
    fx_path = os.path.join(FENXI, f"医案{cid}_盲法辨证分析.txt")
    doc_path = os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt")
    sym_path = os.path.join(OUT, "symptoms", f"医案{cid}_symptoms.txt")
    if not os.path.exists(fx_path):
        results.append({"case": cid, "error": "fenxi missing"})
        continue
    fx = io.open(fx_path, encoding="utf-8", errors="replace").read()
    # claimed chief complaint from fenxi
    m = re.search(r"主诉[：:]?\s*(.+)", fx)
    fx_zhusu = m.group(1).strip()[:40] if m else ""
    # claimed original prescription from fenxi
    m2 = re.search(r"原案(?:针灸|針灸)?(?:处方|處方|选穴|選穴)[：:]\s*([^\n]*(?:\n(?!【|原案|我们的|佐穴|五行|时令|【与|逐穴|【一致性|【结论|免责|====|差异分析).*)*)", fx)
    fx_pres_raw = m2.group(1).strip() if m2 else ""
    # fallback: lines between 原案选穴 and next section
    if not fx_pres_raw:
        m3 = re.search(r"原案选穴[：:](.*?)(?=\n\n|\n【|\n差|\n\[|$)", fx, re.S)
        fx_pres_raw = m3.group(1).strip() if m3 else ""
    doc_pres_raw = io.open(doc_path, encoding="utf-8", errors="replace").read()
    doc_pres_raw = doc_pres_raw.replace("原案針灸處方", "")
    fx_pts = set(points_from(fx_pres_raw))
    doc_pts = set(points_from(doc_pres_raw))
    inter = fx_pts & doc_pts
    union = fx_pts | doc_pts
    ov = len(inter) / len(doc_pts) if doc_pts else 0
    # chief complaint from doc symptoms file
    doc_sym = io.open(sym_path, encoding="utf-8", errors="replace").read()
    m4 = re.search(r"【來診原因】\s*\n(.*?)(?=\n\n【|\n【|$)", doc_sym, re.S)
    doc_zhusu = (m4.group(1).strip()[:40] if m4 else "")
    results.append({
        "case": cid,
        "fx_zhusu": fx_zhusu, "doc_zhusu": doc_zhusu,
        "zhusu_match": (fx_zhusu[:12] in doc_zhusu) or (doc_zhusu[:12] in fx_zhusu),
        "fx_pts": sorted(fx_pts), "doc_pts": sorted(doc_pts),
        "n_fx": len(fx_pts), "n_doc": len(doc_pts),
        "overlap": round(ov, 2),
    })

with io.open(os.path.join(OUT, "_crosscheck.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

print("case | zhusu-match | fenxi-pts/doc-pts | overlap | fenxi zhusu | doc zhusu")
for r in results:
    if "error" in r:
        print(r)
        continue
    flag = "✓" if r["zhusu_match"] and r["overlap"] >= 0.8 else "✗"
    print(f"{flag} {r['case']:>3} | {str(r['zhusu_match']):5} | {r['n_fx']}/{r['n_doc']} | {r['overlap']:.2f} | {r['fx_zhusu'][:22]} || {r['doc_zhusu'][:22]}")
