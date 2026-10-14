# -*- coding: utf-8 -*-
"""score93v3.py — 三轮判分：140基线 / 第二轮(v2) / 第三轮(v3)，同86案同gold。
v3 新增耳穴命名归并（盲法侧）。gold 与第二轮完全一致。"""
import json, os, csv, statistics, collections, pickle

V3 = r"D:\projectAGI\nhx\盲法对照实验\盲法93_v3"
V2 = r"D:\projectAGI\nhx\盲法对照实验\盲法93"
B140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

with open(os.path.join(V3,'_gold_results93v3.pkl'),'rb') as f:
    g = pickle.load(f)
results = g['results']; case_ids = g['case_ids']

b140 = json.load(open(os.path.join(B140,'_blind140_results.json'),encoding='utf-8'))
b93  = json.load(open(os.path.join(V2,'_blind93_results.json'),encoding='utf-8'))   # v2
b93v3= json.load(open(os.path.join(V3,'_blind93v3_results.json'),encoding='utf-8'))# v3

# ---- v2 展开（140基线与v2用，与第二轮score93.py完全一致）----
def expand_v2(u):
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

# ---- v3 展开：在v2基础上新增耳穴命名归并 ----
EAR_MAP = {
 '耳针肾膀胱区压痛点':'耳肾点','耳针肾点':'耳肾点',
 '耳针埋心的压痛点':'耳心点','耳针心的压痛点':'耳心点',
 '耳胆石点':'耳胆点','耳针胆点':'耳胆点','埋耳针<胆>':'耳胆点',
 '耳针埋肝点':'耳肝点','耳穴肝点':'耳肝点',
}
def expand_v3(u):
    u=u.strip()
    u=u.replace('天应隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u=u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u=u.replace('膀胱募','中极')
    if u in EAR_MAP: return {EAR_MAP[u]}
    if u=='心脏点': return {'耳心点'}
    if '透' in u:
        a,b=u.split('透',1); return {a,b}
    if '+' in u:
        return set(p.strip() for p in u.split('+'))
    return {u}

def score(rec, gold_members, gold_count, expand):
    main=rec.get('主穴',[]); aux=rec.get('佐穴',[])
    main_pts=set()
    for u in main: main_pts|=expand(u)
    aux_pts=set()
    for u in aux: aux_pts|=expand(u)
    hm_pts=main_pts&gold_members; hma_pts=(main_pts|aux_pts)&gold_members
    hm=len(hm_pts); hma=len(hma_pts)
    if gold_count>0:
        return dict(mc=len(main), mac=len(main)+len(aux), hm=hm, hma=hma,
                    r_main=hm/gold_count, r_ma=hma/gold_count,
                    prec=hm/len(main) if main else 0.0,
                    hits_main=sorted(hm_pts), layers=rec.get('主穴分层',{}))
    return dict(mc=len(main), mac=len(main)+len(aux), hm=hm, hma=hma,
                r_main=None, r_ma=None, prec=None,
                hits_main=sorted(hm_pts), layers=rec.get('主穴分层',{}))

per={}
rows=[]
for cid in case_ids:
    gm=set(results[cid]['gold_members']); gc=results[cid]['gold_count']
    s140=score(b140[cid],gm,gc,expand_v2)
    s2  =score(b93[cid],gm,gc,expand_v2)
    s3  =score(b93v3[cid],gm,gc,expand_v3)
    per[cid]=dict(gc=gc,s140=s140,s2=s2,s3=s3,gold=sorted(gm),note=results[cid]['note'])
    def f(x): return f"{x:.4f}" if x is not None else ""
    rows.append([cid,gc,
        s3['mc'], s3['hm'],
        f(s140['r_main']), f(s2['r_main']), f(s3['r_main']),
        f(s140['r_ma']),   f(s2['r_ma']),   f(s3['r_ma']),
        f(s140['prec']),   f(s2['prec']),   f(s3['prec']),
        ';'.join(s3['hits_main']),
        results[cid]['note']])

scored=[c for c in case_ids if per[c]['gc']>0]   # 86
unscored=[c for c in case_ids if per[c]['gc']==0] # 7

def col(key, sub): return [per[c][sub][key] for c in scored]
summary=dict(
 n_cases=len(case_ids), n_scorable=len(scored), n_unscored=len(unscored),
 unscored={c:per[c]['note'] for c in unscored})
for sub,label in [('s140','v140'),('s2','v2'),('s3','v3')]:
    summary[label]=dict(
        mean_r_main=statistics.mean(col('r_main',sub)), median_r_main=statistics.median(col('r_main',sub)),
        mean_r_ma=statistics.mean(col('r_ma',sub)),   median_r_ma=statistics.median(col('r_ma',sub)),
        mean_prec=statistics.mean(col('prec',sub)),   median_prec=statistics.median(col('prec',sub)))

def dist(vals):
    b={'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
    for v in vals:
        if v>=0.999: b['100%']+=1
        elif v>=0.8: b['80-99%']+=1
        elif v>=0.6: b['60-79%']+=1
        elif v>=0.4: b['40-59%']+=1
        else: b['<40%']+=1
    return b
summary['dist_v140']=dist(col('r_main','s140'))
summary['dist_v2']=dist(col('r_main','s2'))
summary['dist_v3']=dist(col('r_main','s3'))

# 层间拆解三轮
layers=['对症','俞募背俞','八脉交会','特效奇穴']
def layer_block(sub, expand):
    out={}
    for L in layers:
        units=0; hit_cases=0; empty=0; pts=set()
        for c in scored:
            lu=per[c][sub]['layers'].get(L,[])
            units+=len(lu)
            if not lu: empty+=1
            p=set()
            for u in lu: p|=expand(u)
            h=p & set(results[c]['gold_members'])
            if h: hit_cases+=1; pts|=h
        out[L]=dict(出单元=units,命中案=hit_cases,空置案=empty,命中点数=len(pts),命中点=sorted(pts))
    return out
summary['层_140']=layer_block('s140',expand_v2)
summary['层_v2']=layer_block('s2',expand_v2)
summary['层_v3']=layer_block('s3',expand_v3)

# 特效奇穴命中率（93全集非空案）
def te(blind, expand):
    ne=[c for c in case_ids if blind[c].get('主穴分层',{}).get('特效奇穴')]
    hc=0; pts=set()
    for c in ne:
        p=set()
        for u in blind[c].get('主穴分层',{}).get('特效奇穴',[]): p|=expand(u)
        h=p & set(results[c]['gold_members'])
        if h: hc+=1; pts|=h
    return dict(非空=len(ne),命中案=hc,命中率=hc/len(ne) if ne else None,命中点=sorted(pts))
summary['特效_140']=te(b140,expand_v2)
summary['特效_v2']=te(b93,expand_v2)
summary['特效_v3']=te(b93v3,expand_v3)

# 逐案变化（v140→v2→v3）与显著差异（|Δv3-v2|>=0.3）
per_case=[]
sig=[]
for c in scored:
    a=per[c]['s140']['r_main']; b=per[c]['s2']['r_main']; d=per[c]['s3']['r_main']
    per_case.append(dict(case_id=c,v140=round(a,3),v2=round(b,3),v3=round(d,3),dv3_v2=round(d-b,3)))
    if abs(d-b)>=0.3: sig.append(dict(case_id=c,v140=round(a,3),v2=round(b,3),v3=round(d,3),dv3_v2=round(d-b,3)))
summary['逐案变化']=sorted(per_case,key=lambda x:x['case_id'])
summary['显著差异_dv3_v2>=0.3']=sorted(sig,key=lambda x:x['dv3_v2'])
# 新回退案（v3<v2）按降幅排序
down=sorted([p for p in per_case if p['dv3_v2']<0],key=lambda x:x['dv3_v2'])
up=sorted([p for p in per_case if p['dv3_v2']>0],key=lambda x:-x['dv3_v2'])
summary['v3较v2上升案']=up
summary['v3较v2下降案']=down

# 四个重点验证案
for c in ['107_01','117_01','118_01','207_01','38_01','213_01','312_01','340_01','311_01','37_01','216_04']:
    summary.setdefault('重点验证',{})[c]=dict(
        gold=per[c]['gold'],
        v140_r=round(per[c]['s140']['r_main'],3), v2_r=round(per[c]['s2']['r_main'],3), v3_r=round(per[c]['s3']['r_main'],3),
        v3命中=per[c]['s3']['hits_main'])

# 教程未录（v3）
tx_lib=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\特效库全量.json",encoding='utf-8').read()
zhishi=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\针灸篇-知识条目整理.md",encoding='utf-8').read()
jc=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\教程_utf8.txt",encoding='utf-8').read()
occ=collections.Counter(); hit=collections.Counter()
for c in case_ids:
    gm=set(results[c]['gold_members'])
    for t in b93v3[c].get('主穴',[])+b93v3[c].get('佐穴',[])+b93v3[c].get('备选',[]):
        occ[t]+=1
        if expand_v3(t)&gm: hit[t]+=1
weiluo={t:dict(出现=n,命中=hit[t]) for t,n in occ.items() if (t in tx_lib or t in zhishi) and t not in jc}
summary['教程未录_v3']=weiluo

# CSV
header=['case_id','gold穴数','v3主穴数','v3命中主',
        '重合率主_140','重合率主_v2','重合率主_v3',
        '重合率主佐_140','重合率主佐_v2','重合率主佐_v3',
        '精确率_140','精确率_v2','精确率_v3','v3命中清单','备注']
with open(os.path.join(V3,'判分明细.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f); w.writerow(header); w.writerows(rows)
json.dump(summary,open(os.path.join(V3,'判分汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

# 简报
for sub in ['v140','v2','v3']:
    s=summary[sub]
    print(f"{sub}: 主{s['mean_r_main']:.4f}({s['median_r_main']:.3f}) 主佐{s['mean_r_ma']:.4f}({s['median_r_ma']:.3f}) 精确{s['mean_prec']:.4f}({s['median_prec']:.3f})")
print('分布 v3:',summary['dist_v3'])
print('特效 v3:',summary['特效_v3'])
print('特效 v2:',summary['特效_v2'])
print('特效 140:',summary['特效_140'])
print('显著差异:',json.dumps(summary['显著差异_dv3_v2>=0.3'],ensure_ascii=False))
print('下降案:',json.dumps(down,ensure_ascii=False))
print('重点验证 340/312/38/311/37:',json.dumps({k:summary['重点验证'][k] for k in ['340_01','312_01','38_01','311_01','37_01']},ensure_ascii=False))
