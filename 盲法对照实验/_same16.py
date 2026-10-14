# -*- coding: utf-8 -*-
"""同16案对比：旧技能(37案判分) vs 新技能(140案盲法)在同一手工gold下的重合率。"""
import io, json, re, opencc

cc = opencc.OpenCC('t2s')

SAME = [1, 8, 22, 37, 136, 274, 298, 303, 311, 312, 323, 340, 345, 346, 347, 355]

ALIAS = {
    "肩禺": "肩髃", "肩臑": "肩髃", "太谿": "太溪", "太谿透": "太溪透",
    "肾石点": "肾结石点", "三里": "足三里", "中皖": "中脘", "大凌": "大陵",
    "腿腰点": "腰腿点", "外迎香": "迎香", "正心点": "耳心点",
}

def norm(s):
    s = cc.convert(s)
    for k, v in ALIAS.items():
        s = s.replace(k, v)
    return s

def expand_unit(s):
    """拆成匹配端点集合：X+Y -> {X,Y}; A透B -> {A,B}; 膝五针/三皇/开四关/眼四针展开"""
    s = norm(s)
    out = set()
    for part in re.split(r"[+＋、,，]", s):
        part = part.strip()
        if not part:
            continue
        m = re.search(r"(.+?)透(.+)", part)
        if m:
            a, b = m.group(1).strip(), m.group(2).strip()
            out.add(a); out.add(b)
            continue
        out.add(part)
    return out

def gold_hits(gold, mains):
    gm = set()
    for g in gold:
        ge = expand_unit(g)
        hit = False
        for m in mains:
            me = expand_unit(m)
            if ge & me:
                hit = True
                break
        if hit:
            gm.add(g)
    return gm

old = json.load(io.open(r"D:\projectAGI\nhx\盲法对照实验\_score_v2.json", encoding="utf-8"))
new = json.load(io.open(r"D:\projectAGI\nhx\盲法对照实验\盲法140\_blind140_results.json", encoding="utf-8"))

print("案 | 旧技能重合率(主) | 新技能重合率(主) | 旧命中/gold | 新命中/gold | gold穴数 | 旧盲法穴数 | 新盲法穴数")
rows = []
for n in SAME:
    key = f"{n}_01"
    if str(n) not in old or key not in new:
        print(n, "缺失", str(n) in old, key in new)
        continue
    o = old[str(n)]
    gold = o["gold"]
    old_hits = gold_hits(gold, o["blind_main"])
    new_hits = gold_hits(gold, new[key]["主穴"])
    r_old = len(old_hits) / len(gold)
    r_new = len(new_hits) / len(gold)
    rows.append((n, r_old, r_new, len(old_hits), len(new_hits), len(gold), len(o["blind_main"]), len(new[key]["主穴"])))
    print(f"{n:>3} | {r_old:6.1%} | {r_new:6.1%} | {len(old_hits):>2}/{len(gold):<2} | {len(new_hits):>2}/{len(gold):<2} | {len(gold):>2} | {len(o['blind_main']):>3} | {len(new[key]['主穴']):>3}")

import statistics
ro = [r[1] for r in rows]; rn = [r[2] for r in rows]
print("\n旧技能16案均值: %.1f%% 中位 %.1f%%" % (statistics.mean(ro) * 100, statistics.median(ro) * 100))
print("新技能16案均值: %.1f%% 中位 %.1f%%" % (statistics.mean(rn) * 100, statistics.median(rn) * 100))
print("新技能命中数合计:", sum(r[4] for r in rows), "旧技能命中数合计:", sum(r[3] for r in rows))
print("新技能盲法出穴均值:", round(statistics.mean([r[7] for r in rows]), 2), "旧:", round(statistics.mean([r[6] for r in rows]), 2))
json.dump([{"案": r[0], "旧重合率": r[1], "新重合率": r[2], "旧命中": r[3], "新命中": r[4], "gold": r[5]} for r in rows],
          io.open(r"D:\projectAGI\nhx\盲法对照实验\_same16.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
