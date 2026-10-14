# -*- coding: utf-8 -*-
"""score93v8.py — 八轮判分：140/v2/v3/v4/v5/v6/v7/v8，同86案同gold。"""
import json, os, csv, statistics, collections, pickle

V8=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v8"
V7=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v7"
V6=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v6"
V5=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v5"
V4=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v4"
V3=r"D:\projectAGI\nhx\盲法对照实验\盲法93_v3"
V2=r"D:\projectAGI\nhx\盲法对照实验\盲法93"
B140=r"D:\projectAGI\nhx\盲法对照实验\盲法140"

g=pickle.load(open(os.path.join(V8,'_gold_results93v8.pkl'),'rb'))
results=g['results']; case_ids=g['case_ids']
b140=json.load(open(os.path.join(B140,'_blind140_results.json'),encoding='utf-8'))
b93=json.load(open(os.path.join(V2,'_blind93_results.json'),encoding='utf-8'))
b93v3=json.load(open(os.path.join(V3,'_blind93v3_results.json'),encoding='utf-8'))
b93v4=json.load(open(os.path.join(V4,'_blind93v4_results.json'),encoding='utf-8'))
b93v5=json.load(open(os.path.join(V5,'_blind93v5_results.json'),encoding='utf-8'))
b93v6=json.load(open(os.path.join(V6,'_blind93v6_results.json'),encoding='utf-8'))
b93v7=json.load(open(os.path.join(V7,'_blind93v7_results.json'),encoding='utf-8'))
b93v8=json.load(open(os.path.join(V8,'_blind93v8_results.json'),encoding='utf-8'))

def expand_pre(u):
    u=u.strip()
    u=u.replace('天应隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u=u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u=u.replace('膀胱募','中极')
    if u=='心脏点':return {'耳心点'}
    if u=='耳针埋心的压痛点':return {'耳心点'}
    if '透' in u:a,b=u.split('透',1);return {a,b}
    if '+' in u:return set(x.strip() for x in u.split('+'))
    return {u}
EAR={'耳针肾膀胱区压痛点':'耳肾点','耳针肾点':'耳肾点','耳针埋心的压痛点':'耳心点','耳针心的压痛点':'耳心点',
     '耳胆石点':'耳胆点','耳针胆点':'耳胆点','埋耳针<胆>':'耳胆点','耳针埋肝点':'耳肝点','耳穴肝点':'耳肝点'}
def expand_post(u):
    u=u.strip()
    u=u.replace('天应隔姜灸','天应').replace('天應隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u=u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u=u.replace('膀胱募','中极')
    if u in EAR:return {EAR[u]}
    if u=='心脏点':return {'耳心点'}
    if '透' in u:a,b=u.split('透',1);return {a,b}
    if '+' in u:return set(x.strip() for x in u.split('+'))
    return {u}

def score(rec,gm,gc,ex):
    main=rec.get('主穴',[]);aux=rec.get('佐穴',[])
    mp=set();ap=set()
    for u in main:mp|=ex(u)
    for u in aux:ap|=ex(u)
    hm=mp&gm;hma=(mp|ap)&gm
    if gc>0:
        return dict(mc=len(main),hm=len(hm),hma=len(hma),r_main=len(hm)/gc,r_ma=len(hma)/gc,
                    prec=len(hm)/len(main) if main else 0.0,hits=sorted(hm),layers=rec.get('主穴分层',{}))
    return dict(mc=len(main),hm=len(hm),hma=len(hma),r_main=None,r_ma=None,prec=None,hits=sorted(hm),layers=rec.get('主穴分层',{}))

R=[('s140','v140',b140,expand_pre),('s2','v2',b93,expand_pre),
   ('s3','v3',b93v3,expand_post),('s4','v4',b93v4,expand_post),
   ('s5','v5',b93v5,expand_post),('s6','v6',b93v6,expand_post),
   ('s7','v7',b93v7,expand_post),('s8','v8',b93v8,expand_post)]
per={};rows=[]
for cid in case_ids:
    gm=set(results[cid]['gold_members']);gc=results[cid]['gold_count']
    d={}
    for sub,lab,bl,ex in R:
        d[sub]=score(bl[cid],gm,gc,ex)
    per[cid]=dict(gc=gc,**d,gold=sorted(gm),note=results[cid]['note'])
    f=lambda x:f"{x:.4f}" if x is not None else ""
    rows.append([cid,gc,d['s8']['mc'],d['s8']['hm']]+
        [f(d[s]['r_main']) for s,_,_,_ in R]+
        [f(d[s]['r_ma']) for s,_,_,_ in R]+
        [f(d[s]['prec']) for s,_,_,_ in R]+
        [';'.join(d['s8']['hits']),results[cid]['note']])

scored=[c for c in case_ids if per[c]['gc']>0]
unscored=[c for c in case_ids if per[c]['gc']==0]
def col(sub,k):return [per[c][sub][k] for c in scored]
S=dict(n_cases=len(case_ids),n_scorable=len(scored),n_unscored=len(unscored),
       unscored={c:per[c]['note'] for c in unscored})
for sub,lab,bl,ex in R:
    S[lab]=dict(mean_r_main=statistics.mean(col(sub,'r_main')),median_r_main=statistics.median(col(sub,'r_main')),
                mean_r_ma=statistics.mean(col(sub,'r_ma')),median_r_ma=statistics.median(col(sub,'r_ma')),
                mean_prec=statistics.mean(col(sub,'prec')),median_prec=statistics.median(col(sub,'prec')),
                mean_mc=statistics.mean(col(sub,'mc')))
def dist(v):
    b={'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
    for x in v:
        if x>=0.999:b['100%']+=1
        elif x>=0.8:b['80-99%']+=1
        elif x>=0.6:b['60-79%']+=1
        elif x>=0.4:b['40-59%']+=1
        else:b['<40%']+=1
    return b
for sub,lab,bl,ex in R:
    S[f'dist_{lab}']=dist(col(sub,'r_main'))
    S[lab]['sum_hm']=sum(per[c][sub]['hm'] for c in scored)
    S[lab]['sum_mc']=sum(per[c][sub]['mc'] for c in scored)

layers=['对症','俞募背俞','八脉交会','特效奇穴']
def layer(sub,ex):
    out={}
    for L in layers:
        u=0;hc=0
        for c in scored:
            lu=per[c][sub]['layers'].get(L,[])
            u+=len(lu)
            p=set()
            for x in lu:p|=ex(x)
            if p&set(results[c]['gold_members']):hc+=1
        out[L]=dict(出单元=u,命中案=hc)
    return out
for sub,lab,bl,ex in R:
    S[f'层_{lab}']=layer(sub,ex)

pc=[];sig=[]
for c in scored:
    w=per[c]['s8']['r_main'];v=per[c]['s7']['r_main']
    row=dict(case_id=c)
    for sub,lab,bl,ex in R:row[lab]=round(per[c][sub]['r_main'],3)
    row['dv8_v7']=round(w-v,3)
    pc.append(row)
    if abs(w-v)>=0.3:sig.append(dict(case_id=c,v7=round(v,3),v8=round(w,3),dv8_v7=round(w-v,3)))
S['逐案变化']=sorted(pc,key=lambda x:x['case_id'])
S['显著差异_dv8_v7>=0.3']=sorted(sig,key=lambda x:x['dv8_v7'])
S['v8较v7下降']=sorted([p for p in pc if p['dv8_v7']<0],key=lambda x:x['dv8_v7'])
S['v7零命中']=[c for c in scored if per[c]['s7']['hm']==0]
S['v8零命中']=[c for c in scored if per[c]['s8']['hm']==0]

for c in ['107_01','156_05','60_01','213_01','340_01','201_01','207_01','318_01','216_04']:
    S.setdefault('重点',{})[c]=dict(gold=per[c]['gold'],v7=round(per[c]['s7']['r_main'],3),v8=round(per[c]['s8']['r_main'],3),v8命中=per[c]['s8']['hits'])

header=['case_id','gold穴数','v8主穴数','v8命中主']+[f'重合率主_{l}' for _,l,_,_ in R]+[f'重合率主佐_{l}' for _,l,_,_ in R]+[f'精确率_{l}' for _,l,_,_ in R]+['v8命中清单','备注']
csv.writer(open(os.path.join(V8,'判分明细.csv'),'w',newline='',encoding='utf-8-sig')).writerows([header]+rows)
json.dump(S,open(os.path.join(V8,'判分汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

for sub,lab,bl,ex in R:
    s=S[lab];ratio=s['sum_hm']/s['sum_mc'] if s['sum_mc'] else 0
    print(f"{lab}: 主{s['mean_r_main']:.4f}({s['median_r_main']:.3f}) 主佐{s['mean_r_ma']:.4f} 精确{s['mean_prec']:.4f} 主穴均{s['mean_mc']:.2f} 命中/出{s['sum_hm']}/{s['sum_mc']}={ratio:.3f}")
print('分布v8:',S['dist_v8'])
print('零命中 v7:',S['v7零命中'],'v8:',S['v8零命中'])
print('显著:',S['显著差异_dv8_v7>=0.3'])
print('下降:',S['v8较v7下降'])
