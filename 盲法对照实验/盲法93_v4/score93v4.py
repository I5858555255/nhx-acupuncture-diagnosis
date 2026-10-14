# -*- coding: utf-8 -*-
"""score93v4.py — 四轮判分：140基线 / v2 / v3 / v4，同86案同gold。
v3起启用耳穴归并；v4沿用（天应直接出穴、透刺端点、繁简归一前三轮已生效）。"""
import json, os, csv, statistics, collections, pickle

V4 = r"D:\projectAGI\nhx\盲法对照实验\盲法93_v4"
V3 = r"D:\projectAGI\nhx\盲法对照实验\盲法93_v3"
V2 = r"D:\projectAGI\nhx\盲法对照实验\盲法93"
B140 = r"D:\projectAGI\nhx\盲法对照实验\盲法140"

g = pickle.load(open(os.path.join(V4,'_gold_results93v4.pkl'),'rb'))
results = g['results']; case_ids = g['case_ids']

b140 = json.load(open(os.path.join(B140,'_blind140_results.json'),encoding='utf-8'))
b93  = json.load(open(os.path.join(V2,'_blind93_results.json'),encoding='utf-8'))
b93v3= json.load(open(os.path.join(V3,'_blind93v3_results.json'),encoding='utf-8'))
b93v4= json.load(open(os.path.join(V4,'_blind93v4_results.json'),encoding='utf-8'))

def expand_pre(u):  # 140/v2 用（无耳穴归并，与第二轮一致）
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

EAR_MAP = {
 '耳针肾膀胱区压痛点':'耳肾点','耳针肾点':'耳肾点',
 '耳针埋心的压痛点':'耳心点','耳针心的压痛点':'耳心点',
 '耳胆石点':'耳胆点','耳针胆点':'耳胆点','埋耳针<胆>':'耳胆点',
 '耳针埋肝点':'耳肝点','耳穴肝点':'耳肝点',
}
def expand_post(u):  # v3/v4 用（含耳穴归并；天应/透/+ 同前）
    u=u.strip()
    u=u.replace('天应隔姜灸','天应').replace('天應隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u=u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u=u.replace('膀胱募','中极')
    if u in EAR_MAP: return {EAR_MAP[u]}
    if u=='心脏点': return {'耳心点'}
    if '透' in u:
        a,b=u.split('透',1); return {a,b}
    if '+' in u:
        return set(p.strip() for p in u.split('+'))
    return {u}

def score(rec, gm, gc, expand):
    main=rec.get('主穴',[]); aux=rec.get('佐穴',[])
    mp=set(); ap=set()
    for u in main: mp|=expand(u)
    for u in aux: ap|=expand(u)
    hm=mp&gm; hma=(mp|ap)&gm
    if gc>0:
        return dict(mc=len(main),hm=len(hm),hma=len(hma),
                    r_main=len(hm)/gc,r_ma=len(hma)/gc,
                    prec=len(hm)/len(main) if main else 0.0,
                    hits=sorted(hm),layers=rec.get('主穴分层',{}))
    return dict(mc=len(main),hm=len(hm),hma=len(hma),r_main=None,r_ma=None,prec=None,
                hits=sorted(hm),layers=rec.get('主穴分层',{}))

per={}; rows=[]
for cid in case_ids:
    gm=set(results[cid]['gold_members']); gc=results[cid]['gold_count']
    s140=score(b140[cid],gm,gc,expand_pre)
    s2  =score(b93[cid],gm,gc,expand_pre)
    s3  =score(b93v3[cid],gm,gc,expand_post)
    s4  =score(b93v4[cid],gm,gc,expand_post)
    per[cid]=dict(gc=gc,s140=s140,s2=s2,s3=s3,s4=s4,gold=sorted(gm),note=results[cid]['note'])
    f=lambda x:f"{x:.4f}" if x is not None else ""
    rows.append([cid,gc,s4['mc'],s4['hm'],
        f(s140['r_main']),f(s2['r_main']),f(s3['r_main']),f(s4['r_main']),
        f(s140['r_ma']),f(s2['r_ma']),f(s3['r_ma']),f(s4['r_ma']),
        f(s140['prec']),f(s2['prec']),f(s3['prec']),f(s4['prec']),
        ';'.join(s4['hits']),results[cid]['note']])

scored=[c for c in case_ids if per[c]['gc']>0]
unscored=[c for c in case_ids if per[c]['gc']==0]

def col(sub,k): return [per[c][sub][k] for c in scored]
S=dict(n_cases=len(case_ids),n_scorable=len(scored),n_unscored=len(unscored),
       unscored={c:per[c]['note'] for c in unscored})
for sub,lab in [('s140','v140'),('s2','v2'),('s3','v3'),('s4','v4')]:
    S[lab]=dict(mean_r_main=statistics.mean(col(sub,'r_main')),median_r_main=statistics.median(col(sub,'r_main')),
                mean_r_ma=statistics.mean(col(sub,'r_ma')),median_r_ma=statistics.median(col(sub,'r_ma')),
                mean_prec=statistics.mean(col(sub,'prec')),median_prec=statistics.median(col(sub,'prec')))

def dist(v):
    b={'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
    for x in v:
        if x>=0.999:b['100%']+=1
        elif x>=0.8:b['80-99%']+=1
        elif x>=0.6:b['60-79%']+=1
        elif x>=0.4:b['40-59%']+=1
        else:b['<40%']+=1
    return b
for sub,k in [('s140','dist_v140'),('s2','dist_v2'),('s3','dist_v3'),('s4','dist_v4')]:
    S[k]=dist(col(sub,'r_main'))

layers=['对症','俞募背俞','八脉交会','特效奇穴']
def layer(sub,expand):
    out={}
    for L in layers:
        u=0;hc=0;em=0;pts=set()
        for c in scored:
            lu=per[c][sub]['layers'].get(L,[])
            u+=len(lu)
            if not lu:em+=1
            p=set()
            for x in lu:p|=expand(x)
            h=p&set(results[c]['gold_members'])
            if h:hc+=1;pts|=h
        out[L]=dict(出单元=u,命中案=hc,空置案=em,命中点=sorted(pts))
    return out
S['层_140']=layer('s140',expand_pre)
S['层_v2']=layer('s2',expand_pre)
S['层_v3']=layer('s3',expand_post)
S['层_v4']=layer('s4',expand_post)

def te(blind,expand):
    ne=[c for c in case_ids if blind[c].get('主穴分层',{}).get('特效奇穴')]
    hc=0;pts=set()
    for c in ne:
        p=set()
        for x in blind[c].get('主穴分层',{}).get('特效奇穴',[]):p|=expand(x)
        h=p&set(results[c]['gold_members'])
        if h:hc+=1;pts|=h
    return dict(非空=len(ne),命中案=hc,命中率=hc/len(ne) if ne else None,命中点=sorted(pts))
S['特效_140']=te(b140,expand_pre);S['特效_v2']=te(b93,expand_pre)
S['特效_v3']=te(b93v3,expand_post);S['特效_v4']=te(b93v4,expand_post)

# 逐案变化
pc=[];sig=[]
for c in scored:
    a=per[c]['s140']['r_main'];b=per[c]['s2']['r_main'];d=per[c]['s3']['r_main'];e=per[c]['s4']['r_main']
    pc.append(dict(case_id=c,v140=round(a,3),v2=round(b,3),v3=round(d,3),v4=round(e,3),dv4_v3=round(e-d,3)))
    if abs(e-d)>=0.3:sig.append(dict(case_id=c,v3=round(d,3),v4=round(e,3),dv4_v3=round(e-d,3)))
S['逐案变化']=sorted(pc,key=lambda x:x['case_id'])
S['显著差异_dv4_v3>=0.3']=sorted(sig,key=lambda x:x['dv4_v3'])
S['v4较v3上升']=sorted([p for p in pc if p['dv4_v3']>0],key=lambda x:-x['dv4_v3'])
S['v4较v3下降']=sorted([p for p in pc if p['dv4_v3']<0],key=lambda x:x['dv4_v3'])

for c in ['194_01','216_01','216_02','216_03','216_04','216_05','117_01','118_01','207_01','61_01','62_01','63_01','60_01','1_01','202_01','38_01']:
    S.setdefault('重点',{})[c]=dict(gold=per[c]['gold'],
        v3=round(per[c]['s3']['r_main'],3),v4=round(per[c]['s4']['r_main'],3),
        v4命中=per[c]['s4']['hits'])

# 教程未录 v4
tx=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\skill\references\特效库全量.json",encoding='utf-8').read()
zs=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\针灸篇-知识条目整理.md",encoding='utf-8').read()
jc=open(r"D:\projectAGI\nhx\doubao-acupuncture-diagnosis\教程_utf8.txt",encoding='utf-8').read()
occ=collections.Counter();hit=collections.Counter()
for c in case_ids:
    gm=set(results[c]['gold_members'])
    for t in b93v4[c].get('主穴',[])+b93v4[c].get('佐穴',[])+b93v4[c].get('备选',[]):
        occ[t]+=1
        if expand_post(t)&gm:hit[t]+=1
S['教程未录_v4']={t:dict(出现=n,命中=hit[t]) for t,n in occ.items() if (t in tx or t in zs) and t not in jc}

header=['case_id','gold穴数','v4主穴数','v4命中主',
        '重合率主_140','重合率主_v2','重合率主_v3','重合率主_v4',
        '重合率主佐_140','重合率主佐_v2','重合率主佐_v3','重合率主佐_v4',
        '精确率_140','精确率_v2','精确率_v3','精确率_v4','v4命中清单','备注']
csv.writer(open(os.path.join(V4,'判分明细.csv'),'w',newline='',encoding='utf-8-sig')).writerows([header]+rows)
json.dump(S,open(os.path.join(V4,'判分汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

for lab in ['v140','v2','v3','v4']:
    s=S[lab];print(f"{lab}: 主{s['mean_r_main']:.4f}({s['median_r_main']:.3f}) 主佐{s['mean_r_ma']:.4f} 精确{s['mean_prec']:.4f}")
print('分布v4:',S['dist_v4'],'v3:',S['dist_v3'])
print('特效v4:',S['特效_v4'],'v3:',S['特效_v3'])
print('显著:',json.dumps(S['显著差异_dv4_v3>=0.3'],ensure_ascii=False))
print('下降:',json.dumps(S['v4较v3下降'],ensure_ascii=False))
print('上升:',json.dumps(S['v4较v3上升'],ensure_ascii=False))
