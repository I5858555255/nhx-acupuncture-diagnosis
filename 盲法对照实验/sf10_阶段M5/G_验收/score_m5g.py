# -*- coding: utf-8 -*-
import json, os, sys, csv, statistics, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收');os.makedirs(HERE,exist_ok=True)
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
PREV={'v11':os.path.join(ROOT,'盲法93_v11','_blind93v11_results.json'),
      'v12':os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),
      'v13':os.path.join(HERE,'盲法v13','_blind93v13_results.json')}
BL={k:json.load(open(p,encoding='utf-8')) for k,p in PREV.items()}
def score(rec,c):
    G=set(NEW[c]['gold_members']);Pm=normalize_units(rec.get('主穴',[]));Pa=normalize_units(rec.get('主穴',[])+rec.get('佐穴',[]))
    return dict(main=per_case_metrics(G,Pm),all=per_case_metrics(G,Pa),points_main=len(Pm),units_main=len(rec.get('主穴',[])),pred=sorted(Pm))
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:score(BL[k][c],c) for k in PREV}
SCORED=list(PER);CORE=[c for c in SCORED if c not in EXCLUDE]
M1set=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M5','C_残余归因','..','A_迁移核验'),encoding='utf-8-sig'))) if False else None
# M1 28 案
M1=set()
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M5','A_迁移核验','迁移核验逐案表.csv'),encoding='utf-8-sig')):
    if r['M1审计案']=='Y':M1.add(r['case_id'])
def macro(k,subset,m,cids):
    v=[PER[c][k][subset][m] for c in cids if PER[c][k][subset][m] is not None]
    return statistics.mean(v) if v else None
def blk(k,cids):
    return dict(R=round(macro(k,'main','recall',cids),4),P=round(macro(k,'main','prec',cids),4),
                F1=round(macro(k,'main','f1',cids),4),Jac=round(macro(k,'main','jac',cids),4),
                allR=round(macro(k,'all','recall',cids),4),allF1=round(macro(k,'all','f1',cids),4),
                tp=sum(PER[c][k]['main']['tp'] for c in cids),fp=sum(PER[c][k]['main']['fp'] for c in cids),
                fn=sum(PER[c][k]['main']['fn'] for c in cids),
                mean_points=round(statistics.mean([PER[c][k]['points_main'] for c in cids]),2))
out={}
for nm,cids in [('全量86',SCORED),('核心集64',CORE),('M1_28',[c for c in SCORED if c in M1]),('未M1_58',[c for c in SCORED if c not in M1])]:
    out[nm]={k:blk(k,cids) for k in PREV}
# 逐案 v13 vs v12
pc=[]
for c in SCORED:
    a=PER[c]['v12']['main'];b=PER[c]['v13']['main']
    pc.append(dict(case=c,dTP=b['tp']-a['tp'],dFP=b['fp']-a['fp'],dF1=round((b['f1'] or 0)-(a['f1'] or 0),4)))
json.dump(dict(out=out,逐案=pc),open(os.path.join(HERE,'判分汇总v13.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('=== 横向 main macro ===')
for nm in out:
    print(nm,{k:out[nm][k] for k in PREV})
# 逐案变化
imp=[p for p in pc if p['dTP']>0];wor=[p for p in pc if p['dTP']<0];sam=[p for p in pc if p['dTP']==0]
print('改善案',len(imp),'退步案',len(wor),'不变',len(sam))
