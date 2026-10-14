# -*- coding: utf-8 -*-
"""M5-B：三条件 A(v12)/B(v12b)/C(v12c) 评分对比。canonical scorer。"""
import json, os, sys, csv, statistics, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','B_输入实验','评分');os.makedirs(HERE,exist_ok=True)
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units, load_blind
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))

COND={
 'A':os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),
 'B':os.path.join(ROOT,'sf10_阶段M5','B_输入实验','盲法B','_blind93v12b_results.json'),
 'C':os.path.join(ROOT,'sf10_阶段M5','B_输入实验','盲法C','_blind93v12c_results.json'),
}
BL={k:load_blind(p) for k,p in COND.items()}
def score(rec,c):
    G=set(NEW[c]['gold_members'])
    Pm=normalize_units(rec.get('主穴',[]));Pa=normalize_units(rec.get('主穴',[])+rec.get('佐穴',[]))
    return dict(main=per_case_metrics(G,Pm),all=per_case_metrics(G,Pa),points_main=len(Pm),units_main=len(rec.get('主穴',[])))
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:score(BL[k][c],c) for k in COND}
SCORED=list(PER.keys())
CORE=[c for c in SCORED if c not in EXCLUDE]
follow=[c for c in SCORED if SUMMARY['chain_map'].get(c,'').startswith('followup')]
def macro(cond,subset,metric,cids):
    v=[PER[c][cond][subset][metric] for c in cids if PER[c][cond][subset][metric] is not None]
    return statistics.mean(v) if v else None
def blk(cond,cids):
    return dict(R=round(macro(cond,'main','recall',cids),4),P=round(macro(cond,'main','prec',cids),4),
                F1=round(macro(cond,'main','f1',cids),4),Jac=round(macro(cond,'main','jac',cids),4),
                allR=round(macro(cond,'all','recall',cids),4),allF1=round(macro(cond,'all','f1',cids),4),
                mean_points=round(statistics.mean([PER[c][cond]['points_main'] for c in cids]),2))
out={}
for nm,cids in [('全量86',SCORED),('核心集64',CORE),('复诊跟随',follow)]:
    out[nm]={k:blk(k,cids) for k in COND}
# 逐案主穴差异
diff_rows=[]
for c in SCORED:
    a=set(BL['A'][c].get('主穴',[]));b=set(BL['B'][c].get('主穴',[]));cc=set(BL['C'][c].get('主穴',[]))
    diff_rows.append([c,';'.join(sorted(a^b)),';'.join(sorted(b^cc)),'同' if a==b else '异','同' if b==cc else '异'])
json.dump(out,open(os.path.join(HERE,'三条件评分汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(HERE,'三条件评分汇总对比.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['分层','条件','R','P','F1','Jac','allR','allF1','平均点数'])
    for lay,dd in out.items():
        for k,m in dd.items():w.writerow([lay,k,m['R'],m['P'],m['F1'],m['Jac'],m['allR'],m['allF1'],m['mean_points']])
with open(os.path.join(HERE,'逐案输入差异表_预测层.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','A^B差集','B^C差集','AvsB','BvsC']);w.writerows(diff_rows)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('AvsB 异案数=',sum(1 for r in diff_rows if r[3]=='异'),'BvsC 异案数=',sum(1 for r in diff_rows if r[4]=='异'))
print('异案明细:',[r for r in diff_rows if r[3]=='异' or r[4]=='异'])
