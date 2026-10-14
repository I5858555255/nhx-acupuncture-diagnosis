# -*- coding: utf-8 -*-
"""Gold-point evidence audit: for every gold point, check whether it (and its disease context)
is documented in the skill's 指南 / 特效库 / 治则手法库 / 知识条目."""
import io, os, re, json, csv
import opencc

OUT = r"D:\projectAGI\nhx\盲法对照实验"
SKILL = r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis"

GOLD = {
 1: ["公孙","内关","外关","天突","巨阙","中脘","外迎香透内迎香","肝关"],
 8: ["三间透后溪","膝五针","曲池","足三里"],
 22: ["三阴交","血海"], 23: ["三阴交","血海"],
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
cc = opencc.OpenCC('t2s')
cc2 = opencc.OpenCC('s2t')

def load():
    sources = {}
    # 指南
    for p in [os.path.join(SKILL, "skill", "references", "诊断与针灸实施指南.md"),
              os.path.join(SKILL, "诊断与针灸实施指南.md")]:
        if os.path.exists(p):
            sources["指南"] = io.open(p, encoding="utf-8").read(); break
    for p in [os.path.join(SKILL, "skill", "references", "特效库全量.json"),
              os.path.join(SKILL, "特效库全量.json")]:
        if os.path.exists(p):
            sources["特效库"] = json.dumps(json.load(io.open(p, encoding="utf-8")), ensure_ascii=False); break
    for p in [os.path.join(SKILL, "skill", "references", "治则手法库.json"),
              os.path.join(SKILL, "治则手法库.json")]:
        if os.path.exists(p):
            sources["治则库"] = json.dumps(json.load(io.open(p, encoding="utf-8")), ensure_ascii=False); break
    p = os.path.join(SKILL, "针灸篇-知识条目整理.md")
    if os.path.exists(p):
        sources["知识条目"] = io.open(p, encoding="utf-8").read()
    return sources

sources = load()
print("sources:", {k: len(v) for k, v in sources.items()})

rows = []
for cid, pts in GOLD.items():
    for pt in pts:
        simp = cc.convert(pt)
        trad = cc2.convert(pt)
        hits = {}
        for name, text in sources.items():
            c_s = text.count(simp)
            c_t = text.count(trad)
            hits[name] = max(c_s, c_t)
        rows.append({"案号": cid, "原案穴": pt, "简化": simp,
                     "指南": hits["指南"], "特效库": hits["特效库"], "治则库": hits["治则库"], "知识条目": hits["知识条目"],
                     "有依据": any(hits.values())})
        print(f"案{cid:>3} | {pt:>10} | 指南{hits['指南']:>2} 特效{hits['特效库']:>2} 治则{hits['治则库']:>2} 知识{hits['知识条目']:>2} | {'有' if any(hits.values()) else '无'}")

with io.open(os.path.join(OUT, "_gold_evidence.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

total = len(rows); with_ev = sum(1 for r in rows if r["有依据"])
print(f"\ntotal gold穴次={total}, 有依据={with_ev} ({with_ev/total:.1%}), 无依据={total-with_ev}")
no_ev = [r for r in rows if not r["有依据"]]
print("无依据列表:", [(r['案号'], r['原案穴']) for r in no_ev])
