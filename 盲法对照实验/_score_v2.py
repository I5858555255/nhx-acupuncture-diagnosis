# -*- coding: utf-8 -*-
"""Final scoring v2: hand-curated gold (from manual read of all 37 prescription files) vs blind results.
Also parses old fenxi per-case stats for the 16 aligned cases."""
import io, os, re, json, statistics
import opencc

OUT = r"D:\projectAGI\nhx\盲法对照实验"
SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]
ALIGNED = [1,8,22,23,37,274,298,303,311,312,323,340,345,346,347,355]

cc = opencc.OpenCC('t2s')

# ---------- hand-curated gold (authoritative, from prescription files) ----------
GOLD = {
 1: ["公孙","内关","外关","天突","巨阙","中脘","外迎香透内迎香","肝关"],
 8: ["三间透后溪","膝五针","曲池","足三里"],
 22: ["三阴交","血海"],
 23: ["三阴交","血海"],
 37: ["肝关","肩井","足三里","外关","支沟","照海","足临泣","耳肝点"],
 38: ["肾石点","胆石点","公孙","内关","天突","中脘","日月","肩井","足三里","心俞","督俞","灵台","耳心点"],
 49: ["天突","巨阙","关元","内关","公孙","百会","涌泉","第十椎","心俞","正心点"],
 60: ["合谷","太冲","曲池","肩井","足三里","肩髃","外关","梁丘"],
 107: ["委中","阴谷","承山"],
 136: ["委中","阴谷","承山","曲池","后溪"],
 160: ["三皇穴","关元","中极","水道","心俞","肺俞","肝俞","督俞"],
 194: ["养老透间使","委中","阴谷","腰腿点","曲池","足三里","商丘透丘墟","睛明","头临泣"],
 195: ["攒竹","丝竹空","太阳","耳尖","巨阙","关元","天突","公孙","内关","第十椎压痛点","耳门","听会","复溜"],
 198: ["关元","中极","水道","三阴交","阴陵泉","太冲"],
 207: ["太渊","丘墟","侠溪"],
 208: ["列缺","照海","水泉","大陵","委中","阴谷","足临泣","天突","人迎","睛明"],
 209: ["行间","二间","侠溪","申脉"],
 212: ["合谷","后溪","申脉","侠溪","行间","太阳透率谷"],
 214: ["合谷","地仓透颊车","阳白透鱼腰","曲池","外关","解溪"],
 221: ["大陵","水泉","侠溪","解溪","申脉","复溜","膝五针"],
 223: ["曲池","三里","肩臑"],
 225: ["后溪","申脉","肩井","足三里","三间透后溪"],
 234: ["眼四针","足临泣","公孙","内关","关元","中极","水道"],
 236: ["丘墟","足临泣","天应","侠溪","膝五针","间使","十指麻特效穴","膝关"],
 249: ["委中","阴谷","足临泣","腰腿点","承山"],
 270: ["阴谷","委中","环跳"],
 274: ["合谷","风池","迎香透内迎香"],
 298: ["公孙","内关","巨阙","关元","阴陵泉","足三里","三阴交","心俞","脾俞","肺俞","阳陵泉透阴陵泉"],
 303: ["合谷","曲池","血海","三阴交","筑宾"],
 311: ["外关","耳胆石点","委中","阴谷"],
 312: ["肾结石点","耳肾点"],
 323: ["四白","颧髎","太阳","合谷","侠溪","解溪"],
 340: ["耳肾点"],
 345: ["后溪","申脉","百会","列缺","照海"],
 346: ["膏肓","列缺","照海","合谷","太冲"],
 347: ["行间","公孙","大钟","照海","太溪"],
 355: ["膏肓"],
}

# ---------- match relation ----------
TOU = {
 "三间透后溪": ["三间","后溪"], "后溪透三间": ["后溪","三间"],
 "迎香透内迎香": ["迎香","内迎香"], "外迎香透内迎香": ["外迎香","内迎香","迎香"],
 "阳陵泉透阴陵泉": ["阳陵泉","阴陵泉"], "阴陵泉透阳陵泉": ["阴陵泉","阳陵泉"],
 "中府透云门": ["中府","云门"], "条口透承山": ["条口","承山"],
 "地仓透颊车": ["地仓","颊车"], "太阳透率谷": ["太阳","率谷"],
 "阳白透鱼腰": ["阳白","鱼腰"], "攒竹透鱼腰": ["攒竹","鱼腰"],
 "商丘透丘墟": ["商丘","丘墟"], "养老透间使": ["养老","间使"],
 "三间透劳宫": ["三间","劳宫"], "后溪透劳宫": ["后溪","劳宫"],
}
COMPOSITE = {
 "膝五针": ["鹤顶","内膝眼","外膝眼","阳陵泉","阴陵泉"],
 "三皇穴": ["阴陵泉","地机","三阴交"],
 "眼四针": ["攒竹","鱼腰","丝竹空","睛明"],
}
ALIAS = {
 "肩禺": ["肩髃"], "肩臑": ["肩髃"], "太谿": ["太溪"], "解谿": ["解溪"],
 "後谿": ["后溪"], "肾石点": ["肾结石点"], "足肾石点": ["肾结石点"],
 "第十椎": ["第十椎压痛点"], "第十椎压痛点": ["第十椎"],
 "三里": ["三里","手三里","足三里"], "天应": ["天应","阿是"], "天应穴": ["天应","阿是"],
 "太陽": ["太阳"], "太冲": ["太冲"], "太淵": ["太渊"],
 "耳膽石點": ["耳胆石点"], "耳膽点": ["耳胆石点"], "耳胆点": ["耳胆石点"],
 "耳腎點": ["耳肾点"], "耳腎点": ["耳肾点"], "耳肾点": ["耳肾点"],
 "耳肝點": ["耳肝点"], "耳肝点": ["耳肝点"],
 "正心點": ["正心点"], "正心点": ["正心点"],
 "肝關": ["肝关"], "肝关": ["肝关"],
}
SIDE_RE = re.compile(r"^(雙腳|雙側|雙膝|雙手|雙足|雙|左側|右側|對側|同側|兩側|左|右|雙边|双足|双脚|双膝|双手|双侧|对侧|同侧|两侧|双|足)")
ANN_RE = re.compile(r"（[^）]*）|\([^)]*\)|\[[^\]]*\]|【[^】]*】")

def norm_pt(t):
    t = cc.convert(t)
    t = ANN_RE.sub(" ", t)
    m = SIDE_RE.match(t.strip())
    if m and len(t.strip()) > (m.end() - m.start()):
        t = t.strip()[m.end():]
    # unclosed paren truncation
    for op, cl in [("（", "）"), ("(", ")")]:
        if op in t and cl not in t:
            t = t.split(op)[0]
    return t.strip()

def split_plus(t):
    return [x.strip() for x in re.split(r"[+＋/／]", t) if x.strip()]

def match_keys(name):
    keys = {name}
    if name in TOU: keys.update(TOU[name])
    if name in COMPOSITE: keys.update(COMPOSITE[name])
    if name in ALIAS: keys.update(ALIAS[name])
    for k, v in ALIAS.items():
        if name in v: keys.add(k)
    return keys

def blind_lists(cid):
    data = json.load(io.open(os.path.join(OUT, "_blind_results.json"), encoding="utf-8"))
    case = data.get(f"医案{cid}")
    if not case: return [], [], []
    return case.get("主穴", []), case.get("佐穴", []), case.get("备选", [])

def blind_tokens(lists):
    toks = []
    for lst in lists:
        for item in lst:
            item = norm_pt(item)
            if not item: continue
            parts = split_plus(item)
            for p in parts:
                p = norm_pt(p)
                if p: toks.append(p)
    return toks

def overlap(gold, blind):
    gold_k = [(g, match_keys(g)) for g in gold]
    blind_k = [(b, match_keys(b)) for b in blind]
    matched, missed = [], []
    for g, gk in gold_k:
        if any(gk & bk for _, bk in blind_k):
            matched.append(g)
        else:
            missed.append(g)
    return matched, missed

def old_stat(cid):
    path = os.path.join(SRC, "fenxi", f"医案{cid}_盲法辨证分析.txt")
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r"(?:共同穴位|一致性)[：:]\s*(\d+)\s*/\s*(\d+)", t)
    return (int(m.group(1)), int(m.group(2))) if m else None

# ---------- run ----------
res = {}
print("=== 真盲法判分（主穴 / 主穴+佐穴 / 全部）===")
for cid in CASE_IDS:
    gold = GOLD[cid]
    main, aux, alt = blind_lists(cid)
    bm = blind_tokens([main])
    bp = blind_tokens([main, aux])
    ba = blind_tokens([main, aux, alt])
    mm, ms = overlap(gold, bm)
    mp, _ = overlap(gold, bp)
    ma, _ = overlap(gold, ba)
    den = len(gold)
    r1, r2, r3 = len(mm)/den, len(mp)/den, len(ma)/den
    prec = len(mm)/len(bm) if bm else 0.0
    f1 = 2*r1*prec/(r1+prec) if (r1+prec) else 0.0
    res[cid] = {"gold": gold, "blind_main": bm, "r_main": round(r1,3), "r_plus": round(r2,3),
                "r_all": round(r3,3), "prec": round(prec,3), "f1": round(f1,3),
                "matched": mm, "missed": ms}
    print(f"医案{cid:>3} | G={den:>2} B主={len(bm):>2} | 主={r1:.2f} 主+佐={r2:.2f} 全={r3:.2f} | 命中={mm}")

json.dump(res, io.open(os.path.join(OUT, "_score_v2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

r1s = [res[c]["r_main"] for c in CASE_IDS]
r2s = [res[c]["r_plus"] for c in CASE_IDS]
def dist(rs):
    d = {"100":0,"80_99":0,"60_79":0,"40_59":0,"lt40":0}
    for r in rs:
        if r >= 1.0: d["100"]+=1
        elif r >= 0.8: d["80_99"]+=1
        elif r >= 0.6: d["60_79"]+=1
        elif r >= 0.4: d["40_59"]+=1
        else: d["lt40"]+=1
    return d
print("\n=== 37案汇总（真盲法）===")
print(f"主穴: mean={statistics.mean(r1s):.3f} median={statistics.median(r1s):.2f} dist={dist(r1s)}")
print(f"主+佐: mean={statistics.mean(r2s):.3f} dist={dist(r2s)}")

print("\n=== 对齐16案：旧报告 vs 真盲法主穴 ===")
old_rates, new_rates = [], []
for c in ALIGNED:
    o = old_stat(c)
    ov = o[0]/o[1] if o else None
    nv = res[c]["r_main"]
    if ov is not None: old_rates.append(ov)
    new_rates.append(nv)
    o_str = f"{ov:.2f}" if ov is not None else "-"
    d_str = f"{ov-nv:+.2f}" if ov is not None else "-"
    print(f"医案{c:>3} | 旧={o_str} | 真盲法={nv:.2f} | Δ={d_str}")
print(f"旧(16案) mean={statistics.mean(old_rates):.3f}")
print(f"真盲法(16案) mean={statistics.mean(new_rates):.3f}")
print(f"泄漏贡献(16案同案例差) mean Δ={statistics.mean([o-n for o,n in zip(old_rates,new_rates)]):.3f}")

json.dump({"aligned_old": {str(c): old_stat(c) for c in ALIGNED},
           "summary37": {"r_main_mean": statistics.mean(r1s), "r_plus_mean": statistics.mean(r2s), "dist_main": dist(r1s)},
           "aligned_old_mean": statistics.mean(old_rates), "aligned_new_mean": statistics.mean(new_rates)},
          io.open(os.path.join(OUT, "_score_agg.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
