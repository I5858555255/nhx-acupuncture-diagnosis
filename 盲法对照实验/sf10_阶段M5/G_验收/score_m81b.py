# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
v14=json.load(open(os.path.join(HERE,'盲法v14r7','_blind93v14r7_results.json'),encoding='utf-8'))
cfA=json.load(open(os.path.join(HERE,'_r6cfA_results.json'),encoding='utf-8'))
cfB=json.load(open(os.path.join(HERE,'_r6cfB_results.json'),encoding='utf-8'))
SC=[c for c in CASE_IDS if len(NEW[c]['gold_members'])>0]
CORE=[c for c in SC if c not in EXCLUDE]
def score_list(lst,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(lst or [])
    return per_case_metrics(G,P),sorted(P)
# 版本: v14 从复杂结构取主穴; cfA/cfB 扁平
PER={}
for c in SC:
    m14,p14=score_list(v14[c].get('主穴',[]),c)
    mA,pA=score_list(cfA.get(c,[]),c)
    mB,pB=score_list(cfB.get(c,[]),c)
    PER[c]=dict(v14=(m14,p14),cfA=(mA,pA),cfB=(mB,pB))
def macro(ver,subset_m,cids,key):
    # key: tp/fp/fn/recall/prec/f1/jac
    if key in ('tp','fp','fn'):return sum(PER[c][ver][0][key] for c in cids)
    v=[PER[c][ver][0][key] for c in cids if PER[c][ver][0][key] is not None]
    return round(statistics.mean(v),4)
def blk(ver,cids):
    return dict(TP=macro(ver,None,cids,'tp'),FP=macro(ver,None,cids,'fp'),FN=macro(ver,None,cids,'fn'),
                R=macro(ver,None,cids,'recall'),P=macro(ver,None,cids,'prec'),
                F1=macro(ver,None,cids,'f1'),Jac=macro(ver,None,cids,'jac'))
out={}
for nm,cids in [('全量86',SC),('核心集64',CORE)]:
    out[nm]={v:blk(v,cids) for v in ['v14','cfA','cfB']}
json.dump(out,open(os.path.join(HERE,'判分汇总v14r6cf.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
# 逐案变化表
rows=[]
for c in SC:
    m14=PER[c]['v14'][0];mA=PER[c]['cfA'][0];mB=PER[c]['cfB'][0]
    rows.append([c,
        mA['tp']-m14['tp'],mA['fp']-m14['fp'],mA['fn']-m14['fn'],
        mB['tp']-m14['tp'],mB['fp']-m14['fp'],mB['fn']-m14['fn'],
        ';'.join(PER[c]['cfA'][1]),';'.join(PER[c]['cfB'][1])])
with open(os.path.join(HERE,'r6cf逐案变化表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case','cfA_dTP','cfA_dFP','cfA_dFN','cfB_dTP','cfB_dFP','cfB_dFN','cfA穴集','cfB穴集']);w.writerows(rows)
# 6 触发案
print('=== 6 触发案 ===')
for c in ['199_01','200_01','225_01','323_01','345_01','346_01']:
    print(c,'v14',PER[c]['v14'][0]['tp'],PER[c]['v14'][0]['fp'],'| cfA',PER[c]['cfA'][0]['tp'],PER[c]['cfA'][0]['fp'],'| cfB',PER[c]['cfB'][0]['tp'],PER[c]['cfB'][0]['fp'])
