# -*- coding: utf-8 -*-
"""score.py — 逐案判分 + 汇总 + 输出 CSV/JSON"""
import json, os, re, csv, statistics, collections, pickle

BASE = r"D:\projectAGI\nhx\盲法对照实验\盲法140"
with open(os.path.join(BASE,'_blind140_results.json'), encoding='utf-8') as f:
    blind = json.load(f)
with open(os.path.join(BASE,'_gold_results.pkl'),'rb') as f:
    g = pickle.load(f)
results = g['results']; case_ids = g['case_ids']

# 复用 gold_parse 的展开函数
import importlib.util
spec = importlib.util.spec_from_file_location("gp", os.path.join(BASE,"gold_parse.py"))
# 不执行 gold_parse 主流程(它会重跑), 直接复制 expand_blind_unit
def expand_blind_unit(u):
    u=u.strip()
    u=u.replace('天应隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u=u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u=u.replace('膀胱募','中极')
    if u=='心脏点': return {'耳心点'}
    if u=='耳针埋心的压痛点': return {'耳心点'}
    if '透' in u:
        a,b=u.split('透',1); return {a,b}
    if '+' in u:
        return set(p.strip() for p in u.split('+'))
    return {u}

rows = []
per_case = {}
for cid in case_ids:
    rec = blind[cid]
    gold_members = set(results[cid]['gold_members'])
    gold_count = results[cid]['gold_count']
    main_units = rec.get('主穴', [])
    aux_units = rec.get('佐穴', [])
    alt_units = rec.get('备选', [])
    main_count = len(main_units)
    main_aux_count = main_count + len(aux_units)
    # 展开
    main_pts = set()
    for u in main_units: main_pts |= expand_blind_unit(u)
    aux_pts = set()
    for u in aux_units: aux_pts |= expand_blind_unit(u)
    main_aux_pts = main_pts | aux_pts
    # 命中
    hits_main = main_pts & gold_members
    hits_ma = main_aux_pts & gold_members
    hm = len(hits_main); hma = len(hits_ma)
    if gold_count > 0:
        r_main = hm/gold_count
        r_ma = hma/gold_count
        prec = hm/main_count if main_count>0 else 0.0
    else:
        r_main = r_ma = prec = None
    per_case[cid] = dict(gold_count=gold_count, main_count=main_count, main_aux_count=main_aux_count,
                         hm=hm, hma=hma, r_main=r_main, r_ma=r_ma, prec=prec,
                         hits_main=sorted(hits_main), hits_ma=sorted(hits_ma),
                         note=results[cid]['note'], main_units=main_units, aux_units=aux_units, alt_units=alt_units,
                         gold=sorted(gold_members))
    rows.append([cid, gold_count, main_count, main_aux_count, hm, hma,
                 f"{r_main:.4f}" if r_main is not None else "",
                 f"{r_ma:.4f}" if r_ma is not None else "",
                 f"{prec:.4f}" if prec is not None else "",
                 ';'.join(sorted(hits_main)), ';'.join(sorted(hits_ma)),
                 results[cid]['note']])

# 汇总
scored = [cid for cid in case_ids if per_case[cid]['gold_count']>0]
r_main_list = [per_case[c]['r_main'] for c in scored]
r_ma_list = [per_case[c]['r_ma'] for c in scored]
prec_list = [per_case[c]['prec'] for c in scored]
summary = {
 'n_cases': len(case_ids),
 'n_scorable': len(scored),
 'n_unscorable': len(case_ids)-len(scored),
 'mean_r_main': statistics.mean(r_main_list),
 'median_r_main': statistics.median(r_main_list),
 'mean_r_ma': statistics.mean(r_ma_list),
 'median_r_ma': statistics.median(r_ma_list),
 'mean_prec': statistics.mean(prec_list),
 'median_prec': statistics.median(prec_list),
}
# 分布
bins = {'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
for c in scored:
    v = per_case[c]['r_main']
    if v>=0.999: bins['100%']+=1
    elif v>=0.8: bins['80-99%']+=1
    elif v>=0.6: bins['60-79%']+=1
    elif v>=0.4: bins['40-59%']+=1
    else: bins['<40%']+=1
summary['dist_r_main'] = bins

# 四层拆解
layers = ['对症','俞募背俞','八脉交会','特效奇穴']
layer_stat = {}
for L in layers:
    units=0; hit_pts=set(); hit_cases=0; total_gold_hit=0
    for c in scored:
        rec = blind[c]; gold_members=set(results[c]['gold_members'])
        lu = rec.get('主穴分层',{}).get(L,[])
        units += len(lu)
        pts=set()
        for u in lu: pts |= expand_blind_unit(u)
        h = pts & gold_members
        if h: hit_cases+=1
        hit_pts |= h
    layer_stat[L] = dict(units=units, hit_points=sorted(hit_pts), n_hit_pts=len(hit_pts), hit_cases=hit_cases)
summary['layers'] = layer_stat

# 特效奇穴层: 71案非空?
tx_nonempty = [c for c in case_ids if blind[c].get('主穴分层',{}).get('特效奇穴')]
tx_hit_cases=0; tx_hit_pts=set(); tx_pts_counter=collections.Counter()
for c in tx_nonempty:
    rec=blind[c]; gold_members=set(results[c]['gold_members'])
    lu=rec.get('主穴分层',{}).get('特效奇穴',[])
    pts=set()
    for u in lu:
        pts |= expand_blind_unit(u)
        tx_pts_counter[u]+=1
    h=pts & gold_members
    if h: tx_hit_cases+=1
    tx_hit_pts|=h
summary['texiao'] = dict(n_nonempty=len(tx_nonempty), hit_cases=tx_hit_cases,
                          hit_points=sorted(tx_hit_pts), n_hit_pts=len(tx_hit_pts),
                          point_occurrences=dict(tx_pts_counter))

# 教程未录奇穴扫描
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\特效库全量.json",encoding='utf-8') as f:
    tx_lib = f.read()
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\针灸篇-知识条目整理.md",encoding='utf-8') as f:
    zhishi = f.read()
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\教程_utf8.txt",encoding='utf-8') as f:
    jiaocheng = f.read()

# 收集盲法侧词元(主穴/佐穴/备选 单元名)
tok_occ = collections.Counter()
tok_hit = collections.Counter()
for c in case_ids:
    rec=blind[c]; gold_members=set(results[c]['gold_members'])
    toks = rec.get('主穴',[])+rec.get('佐穴',[])+rec.get('备选',[])
    for t in toks:
        tok_occ[t]+=1
        pts = expand_blind_unit(t)
        if pts & gold_members:
            tok_hit[t]+=1
# 判断: 在特效库或知识条目中可查到, 但教程中查不到
weiluo = {}
for t,n in tok_occ.items():
    in_ref = (t in tx_lib) or (t in zhishi)
    in_jc = t in jiaocheng
    if in_ref and not in_jc:
        weiluo[t] = dict(occurrences=n, gold_hits=tok_hit[t])
summary['weiluo_in_jiaocheng'] = weiluo

# 无法解析统计
unresolved = {c: results[c]['note'] for c in case_ids if results[c]['gold_count']==0}
summary['unresolved'] = unresolved

# 写 CSV
with open(os.path.join(BASE,'判分明细.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['case_id','gold穴数','盲法主穴数','盲法主佐穴数','命中数主','命中数主佐','重合率主','重合率主佐','精确率','命中穴清单主','命中穴清单主佐','无法解析/备注'])
    w.writerows(rows)

# 写汇总JSON
out_json = {k:v for k,v in summary.items()}
with open(os.path.join(BASE,'判分汇总.json'),'w',encoding='utf-8') as f:
    json.dump(out_json, f, ensure_ascii=False, indent=2)

print("=== 汇总 ===")
print(json.dumps({k:v for k,v in summary.items() if k not in ('unresolved','layers','texiao','weiluo_in_jiaocheng')}, ensure_ascii=False, indent=2))
print("\n四层:", json.dumps(layer_stat, ensure_ascii=False, indent=2))
print("\n特效奇穴: 非空案数", len(tx_nonempty), "命中案数", tx_hit_cases, "命中点", sorted(tx_hit_pts))
print("\n教程未录奇穴:", json.dumps(weiluo, ensure_ascii=False, indent=2))
print("\n无法解析案数:", len(unresolved))
