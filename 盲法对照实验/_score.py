# -*- coding: utf-8 -*-
"""Scoring engine: gold prescriptions vs blind results (+ old fenxi for aligned subset).
Match: unit name equality OR endpoint/constituent overlap (透刺/复合穴展开).
"""
import io, os, re, json
import opencc

OUT = r"D:\projectAGI\nhx\盲法对照实验"
SRC = r"D:\历史\PDF Candy Desktop(PDF全能工具箱)v2.8.1\1\1\倪醫師08年病案紀錄358篇\含針灸治療醫案\首診醫案"
CASE_IDS = [1,8,22,23,37,38,49,60,107,136,160,194,195,198,207,208,209,212,214,221,223,225,234,236,249,270,274,298,303,311,312,323,340,345,346,347,355]
ALIGNED = {1,8,22,23,37,274,298,303,311,312,323,340,345,346,347,355}

cc = opencc.OpenCC('t2s')

# ---- known point lexicon (simplified) ----
KNOWN = set("""
百会 四神聪 印堂 神庭 上星 攒竹 鱼腰 丝竹空 太阳 睛明 承泣 四白 巨髎 地仓 颊车 下关 头维 率谷 悬颅 颔厌 角孙 风池 风府 哑门 天柱 翳风 完骨 听会 听宫 耳门 上关 瞳子髎 阳白 迎香 人中 兑端 承浆 廉泉 天突 璇玑 华盖 紫宫 玉堂 膻中 中庭 鸠尾 巨阙 上脘 中脘 建里 下脘 水分 神阙 气海 石门 关元 中极 曲骨 会阴 长强 腰俞 腰阳关 命门 悬枢 脊中 中枢 筋缩 至阳 灵台 神道 身柱 陶道 大椎 肩井 缺盆 气舍 水突 人迎 扶突 天鼎 天窗 天容 肩中俞 肩外俞 曲垣 秉风 天髎 肩髃 肩髎 臑俞 肩贞 极泉 青灵 少海 曲泽 尺泽 孔最 列缺 经渠 太渊 鱼际 少商 商阳 二间 三间 合谷 阳溪 偏历 温溜 下廉 上廉 手三里 曲池 肘髎 臂臑 巨骨 少冲 少府 神门 阴郄 通里 灵道 中冲 劳宫 大陵 内关 间使 郄门 天泉 关冲 液门 中渚 阳池 外关 支沟 会宗 三阳络 四渎 天井 清冷渊 消泺 臑会 翳风 瘈脉 颅息 角孙 少泽 前谷 后溪 腕骨 阳谷 养老 支正 小海 膈俞 心俞 督俞 肝俞 胆俞 脾俞 胃俞 三焦俞 肾俞 气海俞 大肠俞 关元俞 小肠俞 膀胱俞 中膂俞 白环俞 上髎 次髎 中髎 下髎 会阳 承扶 殷门 浮郄 委阳 委中 合阳 承筋 承山 飞扬 跗阳 昆仑 仆参 申脉 金门 京骨 束骨 足通谷 至阴 涌泉 然谷 太溪 大钟 水泉 照海 复溜 交信 筑宾 阴谷 横骨 大赫 气穴 四满 中注 肓俞 商曲 石关 阴都 腹通谷 幽门 步廊 神封 灵墟 神藏 彧中 俞府 隐白 大都 太白 公孙 商丘 三阴交 漏谷 地机 阴陵泉 血海 箕门 冲门 府舍 腹结 大横 腹哀 食窦 天溪 胸乡 周荣 大包 厉兑 内庭 陷谷 冲阳 解溪 丰隆 条口 上巨虚 下巨虚 足三里 犊鼻 梁丘 阴市 伏兔 髀关 气冲 归来 水道 大巨 外陵 天枢 滑肉门 太乙 关门 梁门 承满 不容 乳根 乳中 膺窗 屋翳 库房 气户 足窍阴 足临泣 地五会 侠溪 丘墟 悬钟 绝骨 阳辅 光明 外丘 阳交 阳陵泉 膝阳关 中渎 风市 环跳 居髎 维道 五枢 带脉 京门 日月 辄筋 渊腋 瞳子髎 本神 头临泣 目窗 正营 承灵 脑空 大敦 行间 太冲 中封 蠡沟 中都 膝关 曲泉 阴包 足五里 阴廉 急脉 章门 期门 膏肓 百劳 四缝 十宣 八风 八邪
""".split())

# Ni Shi extra / special names (also treated as known)
EXTRA = {
    "膝五针": ["鹤顶","内膝眼","外膝眼","阳陵泉","阴陵泉"],
    "鹤顶": [], "内膝眼": [], "外膝眼": [],
    "三皇穴": ["阴陵泉","地机","三阴交"],
    "眼四针": ["攒竹","鱼腰","丝竹空","睛明"],
    "腰腿点": [], "肾结石点": [], "肾石点": ["肾结石点"], "胆石点": [],
    "耳肝点": [], "耳胆点": [], "耳肾点": [], "耳心点": [], "耳尖": [], "耳门": [],
    "正心点": [], "十指麻特效穴": [], "定喘穴": [], "消积穴": [], "痞根": [],
    "肝关": [], "肾关": [], "中平": [], "大白": [], "灵骨": [],
    "天应": [], "阿是": [], "第十椎压痛点": [], "第十椎": ["第十椎压痛点"],
    "肩禺": ["肩髃"], "太谿": ["太溪"], "解谿": ["解溪"], "後谿": ["后溪"],
    "足临泣": [], "头临泣": [],
    "乳中": [], "鸠尾": [],
}
# through-needle (透刺) units -> endpoints
TOU = {
    "三间透后溪": ["三间","后溪"], "后溪透三间": ["后溪","三间"],
    "迎香透内迎香": ["迎香","内迎香"], "外迎香透内迎香": ["外迎香","内迎香","迎香"],
    "阳陵泉透阴陵泉": ["阳陵泉","阴陵泉"], "阴陵泉透阳陵泉": ["阴陵泉","阳陵泉"],
    "中府透云门": ["中府","云门"], "条口透承山": ["条口","承山"],
    "地仓透颊车": ["地仓","颊车"], "太阳透率谷": ["太阳","率谷"],
    "阳白透鱼腰": ["阳白","鱼腰"], "攒竹透鱼腰": ["攒竹","鱼腰"],
    "商丘透丘墟": ["商丘","丘墟"], "养老透间使": ["养老","间使"],
    "神门透少海": ["神门","少海"], "后溪透劳宫": ["后溪","劳宫"],
    "三间透劳宫": ["三间","劳宫"],
}
ALL_KNOWN = set(KNOWN) | set(EXTRA.keys()) | set(TOU.keys())
SIDE_RE = re.compile(r"^(雙腳|雙側|雙膝|雙手|雙|左|右|對側|同側|兩側|雙足)")
ANN_RE = re.compile(r"（[^）]*）|\([^)]*\)|\[[^\]]*\]")
SEP_RE = re.compile(r"[、，,；;。．．\s]+|及|與")

def strip_side(t):
    t = t.strip()
    m = SIDE_RE.match(t)
    if m and len(t) > m.end() - m.start():
        return t[m.end():]
    return t

def norm_pt(t):
    t = cc.convert(t)
    t = strip_side(t)
    t = ANN_RE.sub("", t).strip()
    return t

def split_plus(t):
    return [x.strip() for x in re.split(r"[+＋/／]", t) if x.strip()]

def split_chunks(text):
    """Split prescription text into candidate chunks, keep 透/穿 units and plus-groups."""
    text = ANN_RE.sub(" ", text)  # drop annotations first
    chunks = []
    for part in SEP_RE.split(text):
        part = part.strip()
        if not part:
            continue
        if "透" in part or "穿" in part:
            chunks.append(part)
        else:
            chunks.extend(split_plus(part))
    return [c for c in chunks if c]

def match_keys(name):
    """All keys a mention matches: itself + endpoints + composite constituents + aliases."""
    keys = {name}
    if name in TOU:
        keys.update(TOU[name])
    if name in EXTRA:
        for k in EXTRA[name]:
            keys.add(k)
            if k in EXTRA:
                keys.update(EXTRA[k])
    if name in EXTRA and name in {"肾石点"}:
        keys.update(EXTRA[name])
    # alias reverse: 肩禺->肩髃
    for k, v in EXTRA.items():
        if name in v and k != name:
            keys.add(k)
    return keys

def gold_mentions(cid):
    path = os.path.join(OUT, "prescriptions", f"医案{cid}_prescription.txt")
    t = io.open(path, encoding="utf-8").read()
    t = re.sub(r"^医案\d+ 原案針灸處方", "", t)
    t = re.sub(r"解說.*$", "", t, flags=re.S)
    mentions = []
    raw_chunks = split_chunks(t)
    for ch in raw_chunks:
        name = norm_pt(ch)
        if not name:
            continue
        # lexicon filter: must contain a known point name (or be an extra)
        known_hit = name in ALL_KNOWN or any(k in name for k in ALL_KNOWN if len(k) >= 2)
        if not known_hit:
            continue
        mentions.append(name)
    return mentions

def blind_tokens(cid, scope):
    data = json.load(io.open(os.path.join(OUT, "_blind_results.json"), encoding="utf-8"))
    case = data.get(f"医案{cid}")
    if not case:
        return [], [], []
    main, aux, alt = case.get("主穴", []), case.get("佐穴", []), case.get("备选", [])
    if scope == "main":
        lists = [main]
    elif scope == "mainplus":
        lists = [main, aux]
    else:
        lists = [main, aux, alt]
    toks = []
    for lst in lists:
        for item in lst:
            item = norm_pt(item)
            if not item:
                continue
            if "透" in item:
                toks.append(item)
            else:
                toks.extend(split_plus(item))
    return [t for t in toks if t], main, aux

def overlap(gold, blind):
    gold_keys = [(g, match_keys(g)) for g in gold]
    blind_keys = [(b, match_keys(b)) for b in blind]
    matched = 0
    matched_names = []
    for g, gk in gold_keys:
        hit = any((gk & bk) for _, bk in blind_keys)
        if hit:
            matched += 1
            matched_names.append(g)
    return matched, matched_names

def old_fenxi(cid):
    path = os.path.join(SRC, "fenxi", f"医案{cid}_盲法辨证分析.txt")
    t = io.open(path, encoding="utf-8").read()
    # old blind main list
    mm = re.search(r"主穴：\n((?:-\s*[^\n]+\n?)+)", t)
    old_main = []
    if mm:
        for line in mm.group(1).split("\n"):
            line = line.strip()
            if line.startswith("-"):
                old_main.append(norm_pt(line[1:].strip()))
    # old gold list
    gm = re.search(r"原案针灸处方选穴：\n(.*?)(\n\n|\n我们的辨证选穴)", t, re.S)
    old_gold_raw = gm.group(1) if gm else ""
    old_gold = [norm_pt(x.strip()) for x in re.split(r"[、，,；;\s\n]+", old_gold_raw) if x.strip()]
    # reported stat
    sm = re.search(r"共同穴位：(\d+)/(\d+)", t)
    reported = (int(sm.group(1)), int(sm.group(2))) if sm else None
    return old_main, old_gold, reported

# ---- run ----
res = {}
print("=== per-case scoring (gold | blind_main | blind_mainplus) ===")
for cid in CASE_IDS:
    gold = gold_mentions(cid)
    bm, main_raw, aux_raw = blind_tokens(cid, "main")
    bp, _, _ = blind_tokens(cid, "mainplus")
    m_main, mm_main = overlap(gold, bm)
    m_plus, _ = overlap(gold, bp)
    denom = len(gold)
    r_main = m_main / denom if denom else 0.0
    r_plus = m_plus / denom if denom else 0.0
    prec = m_main / len(bm) if bm else 0.0
    f1 = 2*r_main*prec/(r_main+prec) if (r_main+prec) else 0.0
    res[cid] = {"gold": gold, "blind_main": bm, "r_main": round(r_main,3), "r_plus": round(r_plus,3),
                "prec": round(prec,3), "f1": round(f1,3), "matched": mm_main}
    old = old_fenxi(cid) if cid in ALIGNED else None
    if old:
        og, oold_gold, reported = old
        # old overlap computed with old gold (sanity) — reported stat used instead
        res[cid]["old_main"] = og
        res[cid]["old_gold"] = oold_gold
        res[cid]["old_reported"] = reported
    print(f"医案{cid:>3} | gold={len(gold):>2} | blind主={len(bm):>2} | 重合主={m_main}/{denom}={r_main:.2f} | 主+佐={m_plus}/{denom}={r_plus:.2f} | prec={prec:.2f} | gold={gold}")
    print(f"        blind主穴={bm}")

json.dump(res, io.open(os.path.join(OUT, "_score_detail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- aggregate ----
import statistics
rates_main = [res[c]["r_main"] for c in CASE_IDS]
rates_plus = [res[c]["r_plus"] for c in CASE_IDS]
def dist(rates):
    d = {"100": 0, "80_99": 0, "60_79": 0, "40_59": 0, "lt40": 0}
    for r in rates:
        if r >= 1.0: d["100"] += 1
        elif r >= 0.8: d["80_99"] += 1
        elif r >= 0.6: d["60_79"] += 1
        elif r >= 0.4: d["40_59"] += 1
        else: d["lt40"] += 1
    return d
print("\n=== 全部37案（真盲法·主穴）===")
print("mean r_main =", round(statistics.mean(rates_main), 3), " median =", statistics.median(rates_main))
print("dist:", dist(rates_main))
print("=== 全部37案（主穴+佐穴）===")
print("mean r_plus =", round(statistics.mean(rates_plus), 3))
print("dist:", dist(rates_plus))
print("\n=== 对齐16案: 旧报告(共同穴位行) vs 真盲法主穴 ===")
old_r = []
new_r_aligned = []
for c in sorted(ALIGNED):
    o = res[c].get("old_reported")
    ov = (o[0]/o[1]) if o and o[1] else None
    nv = res[c]["r_main"]
    old_r.append(ov); new_r_aligned.append(nv)
    print(f"医案{c:>3} | 旧={ov and round(ov,2)} | 真盲法={round(nv,2)} | delta={ov and round(ov-nv,2)}")
print("旧对齐子集 mean =", round(statistics.mean([x for x in old_r if x is not None]), 3))
print("真盲法对齐子集 mean =", round(statistics.mean(new_r_aligned), 3))
