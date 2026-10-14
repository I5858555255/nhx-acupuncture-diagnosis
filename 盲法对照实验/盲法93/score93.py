# -*- coding: utf-8 -*-
"""score93.py — 盲法93回归判分：本轮 vs 140版同案基线，口径复刻盲法140/score.py"""
import json, os, re, csv, statistics, collections, pickle

BASE = r"D:\projectAGI\nhx\盲法对照实验\盲法93"
B140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

with open(os.path.join(BASE,'_blind93_results.json'), encoding='utf-8') as f:
    b93 = json.load(f)
with open(os.path.join(B140,'_blind140_results.json'), encoding='utf-8') as f:
    b140 = json.load(f)
with open(os.path.join(BASE,'_gold_results93.pkl'),'rb') as f:
    g = pickle.load(f)
results = g['results']; case_ids = g['case_ids']  # sorted, 93个

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

def score_rec(rec, gold_members, gold_count):
    main_units = rec.get('主穴', [])
    aux_units = rec.get('佐穴', [])
    main_count = len(main_units)
    main_aux_count = main_count + len(aux_units)
    main_pts=set()
    for u in main_units: main_pts |= expand_blind_unit(u)
    aux_pts=set()
    for u in aux_units: aux_pts |= expand_blind_unit(u)
    ma_pts = main_pts | aux_pts
    hits_main = main_pts & gold_members
    hits_ma = ma_pts & gold_members
    hm=len(hits_main); hma=len(hits_ma)
    if gold_count>0:
        r_main=hm/gold_count; r_ma=hma/gold_count
        prec=hm/main_count if main_count>0 else 0.0
    else:
        r_main=r_ma=prec=None
    return dict(main_count=main_count, main_aux_count=main_aux_count, hm=hm, hma=hma,
                r_main=r_main, r_ma=r_ma, prec=prec,
                hits_main=sorted(hits_main), hits_ma=sorted(hits_ma),
                main_units=main_units, aux_units=aux_units,
                layers=rec.get('主穴分层',{}))

rows=[]
per={}
for cid in case_ids:
    gold_members=set(results[cid]['gold_members'])
    gc=results[cid]['gold_count']
    s93=score_rec(b93[cid], gold_members, gc)
    s140=score_rec(b140[cid], gold_members, gc)
    per[cid]=dict(gold_count=gc, s93=s93, s140=s140, note=results[cid]['note'], gold=sorted(gold_members))
    rows.append([
        cid, gc,
        s93['main_count'], s93['main_aux_count'], s93['hm'], s93['hma'],
        f"{s93['r_main']:.4f}" if s93['r_main'] is not None else "",
        f"{s93['r_ma']:.4f}" if s93['r_ma'] is not None else "",
        f"{s93['prec']:.4f}" if s93['prec'] is not None else "",
        ';'.join(s93['hits_main']), ';'.join(s93['hits_ma']),
        s140['main_count'], s140['hm'],
        f"{s140['r_main']:.4f}" if s140['r_main'] is not None else "",
        f"{s140['prec']:.4f}" if s140['prec'] is not None else "",
        results[cid]['note'],
    ])

scored=[c for c in case_ids if per[c]['gold_count']>0]   # 86
unscored=[c for c in case_ids if per[c]['gold_count']==0] # 7

def mean(xs): return statistics.mean(xs) if xs else None
def med(xs): return statistics.median(xs) if xs else None

# ===== 本轮汇总（86案）=====
r93_main=[per[c]['s93']['r_main'] for c in scored]
r93_ma=[per[c]['s93']['r_ma'] for c in scored]
p93=[per[c]['s93']['prec'] for c in scored]
# ===== 140基线（同86案）=====
r140_main=[per[c]['s140']['r_main'] for c in scored]
r140_ma=[per[c]['s140']['r_ma'] for c in scored]
p140=[per[c]['s140']['prec'] for c in scored]

summary=dict(
 n_cases=len(case_ids), n_scorable=len(scored), n_unscorable=len(unscored),
 unscorable_cases={c:per[c]['note'] for c in unscored},
本轮=dict(
   mean_r_main=mean(r93_main), median_r_main=med(r93_main),
   mean_r_ma=mean(r93_ma), median_r_ma=med(r93_ma),
   mean_prec=mean(p93), median_prec=med(p93)),
基线140=dict(
   mean_r_main=mean(r140_main), median_r_main=med(r140_main),
   mean_r_ma=mean(r140_ma), median_r_ma=med(r140_ma),
   mean_prec=mean(p140), median_prec=med(p140)),
)

# 分布（本轮重合率主）
def dist(vals):
    b={'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
    for v in vals:
        if v>=0.999: b['100%']+=1
        elif v>=0.8: b['80-99%']+=1
        elif v>=0.6: b['60-79%']+=1
        elif v>=0.4: b['40-59%']+=1
        else: b['<40%']+=1
    return b
summary['dist_本轮_r_main']=dist(r93_main)
summary['dist_140_r_main']=dist(r140_main)

# ===== 层间拆解（本轮 & 140基线，同口径，仅86可判分案）=====
layers=['对症','俞募背俞','八脉交会','特效奇穴']
def layer_block(rec_key):
    out={}
    for L in layers:
        units=0; hit_pts=set(); hit_cases=0
        empty_cases=0
        for c in scored:
            lu=per[c][rec_key]['layers'].get(L,[])
            units+=len(lu)
            if not lu: empty_cases+=1
            pts=set()
            for u in lu: pts|=expand_blind_unit(u)
            h=pts & set(results[c]['gold_members'])
            if h: hit_cases+=1; hit_pts|=h
        out[L]=dict(出单元数=units, 命中案数=hit_cases, 空置案数=empty_cases,
                    命中点数=len(hit_pts), 命中点=sorted(hit_pts))
    return out
summary['层间_本轮']=layer_block('s93')
summary['层间_140']=layer_block('s140')

# ===== 特效奇穴层单独统计（93全集 + 86可判分）=====
def texiao_block(blind):
    nonempty=[c for c in case_ids if blind[c].get('主穴分层',{}).get('特效奇穴')]
    hit_cases=0; hit_pts=set(); occ=collections.Counter()
    for c in nonempty:
        gold_members=set(results[c]['gold_members'])
        lu=blind[c].get('主穴分层',{}).get('特效奇穴',[])
        pts=set()
        for u in lu:
            pts|=expand_blind_unit(u); occ[u]+=1
        h=pts & gold_members
        if h: hit_cases+=1; hit_pts|=h
    return dict(非空案数=len(nonempty), 命中案数=hit_cases,
                命中率=hit_cases/len(nonempty) if nonempty else None,
                命中点=sorted(hit_pts), 点出现次数=dict(occ.most_common()))
summary['特效奇穴_本轮']=texiao_block(b93)
summary['特效奇穴_140']=texiao_block(b140)

# ===== 教程未录奇穴扫描（本轮：主穴+佐穴+备选）=====
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\特效库全量.json",encoding='utf-8') as f:
    tx_lib=f.read()
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\针灸篇-知识条目整理.md",encoding='utf-8') as f:
    zhishi=f.read()
with open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\教程_utf8.txt",encoding='utf-8') as f:
    jc=f.read()
tok_occ=collections.Counter(); tok_hit=collections.Counter()
for c in case_ids:
    gold_members=set(results[c]['gold_members'])
    toks=b93[c].get('主穴',[])+b93[c].get('佐穴',[])+b93[c].get('备选',[])
    for t in toks:
        tok_occ[t]+=1
        if expand_blind_unit(t) & gold_members: tok_hit[t]+=1
weiluo={}
for t,n in tok_occ.items():
    in_ref=(t in tx_lib) or (t in zhishi)
    in_jc=t in jc
    if in_ref and not in_jc:
        weiluo[t]=dict(出现案数=n, 命中gold次数=tok_hit[t])
summary['教程未录奇穴_本轮']=weiluo

# ===== 单操作案 =====
summary['单操作案']={}
for c in ['340_01','355_01']:
    summary['单操作案'][c]=dict(
        gold=per[c]['gold'],
        本轮主穴=b93[c].get('主穴'),
        本轮命中主=per[c]['s93']['hits_main'],
        基线140主穴=b140[c].get('主穴'),
        基线140命中主=per[c]['s140']['hits_main'])

# ===== 逐案对比（86案）：显著差异 =====
diffs=[]
for c in scored:
    a=per[c]['s93']['r_main']; b=per[c]['s140']['r_main']
    diffs.append((c, b, a, a-b))
diffs_sorted=sorted(diffs, key=lambda x:x[3])
summary['逐案对比_下降TOP']=[dict(case_id=c, r140=round(b,3), r93=round(a,3), delta=round(d,3)) for c,b,a,d in diffs_sorted[:10]]
summary['逐案对比_上升TOP']=[dict(case_id=c, r140=round(b,3), r93=round(a,3), delta=round(d,3)) for c,b,a,d in diffs_sorted[-10:][::-1]]
sig=[(c,b,a,d) for c,b,a,d in diffs if abs(d)>=0.3]
summary['显著差异案_abs>=0.3']=[dict(case_id=c, r140=round(b,3), r93=round(a,3), delta=round(d,3)) for c,b,a,d in sorted(sig,key=lambda x:x[3])]

# ===== 写 CSV =====
header=['case_id','gold穴数','本轮盲法主穴数','本轮主佐穴数','命中数主','命中数主佐',
        '重合率主','重合率主佐','精确率','命中穴清单主','命中穴清单主佐',
        '140版主穴数','140版命中数','140版重合率主','140版精确率','无法解析/备注']
with open(os.path.join(BASE,'判分明细.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(header); w.writerows(rows)

with open(os.path.join(BASE,'判分汇总.json'),'w',encoding='utf-8') as f:
    json.dump(summary,f,ensure_ascii=False,indent=2)

# ===== 控制台简报 =====
print("=== 本轮(86) vs 140基线(同86案) ===")
print(f"重合率主   本轮 {summary['本轮']['mean_r_main']:.4f} (中位{summary['本轮']['median_r_main']:.3f}) | 140 {summary['基线140']['mean_r_main']:.4f} (中位{summary['基线140']['median_r_main']:.3f})")
print(f"重合率主佐 本轮 {summary['本轮']['mean_r_ma']:.4f} (中位{summary['本轮']['median_r_ma']:.3f}) | 140 {summary['基线140']['mean_r_ma']:.4f} (中位{summary['基线140']['median_r_ma']:.3f})")
print(f"精确率     本轮 {summary['本轮']['mean_prec']:.4f} (中位{summary['本轮']['median_prec']:.3f}) | 140 {summary['基线140']['mean_prec']:.4f} (中位{summary['基线140']['median_prec']:.3f})")
print("分布本轮:",summary['dist_本轮_r_main']," 140:",summary['dist_140_r_main'])
print("\n层间本轮:",json.dumps(summary['层间_本轮'],ensure_ascii=False))
print("层间140:",json.dumps(summary['层间_140'],ensure_ascii=False))
print("\n特效奇穴本轮:",json.dumps(summary['特效奇穴_本轮'],ensure_ascii=False))
print("特效奇穴140:",json.dumps(summary['特效奇穴_140'],ensure_ascii=False))
print("\n教程未录:",json.dumps(weiluo,ensure_ascii=False))
print("\n单操作:",json.dumps(summary['单操作案'],ensure_ascii=False))
print("\n显著差异案:",json.dumps(summary['显著差异案_abs>=0.3'],ensure_ascii=False))
print("\n不可判分:",unscored)
