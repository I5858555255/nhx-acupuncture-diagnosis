# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
M1=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M5','A_迁移核验','迁移核验逐案表.csv'),encoding='utf-8-sig')) if r['M1审计案']=='Y')
vt={r['case_id']:str(r.get('visit_type','')) for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段D','组装清单.csv'),encoding='utf-8-sig'))}
PREV={'v14r2':os.path.join(HERE,'盲法v14r2','_blind93v14r2_results.json'),
      'v14r5':os.path.join(HERE,'盲法v14r5','_blind93v14r5_results.json')}
BL={k:json.load(open(p,encoding='utf-8')) for k,p in PREV.items()}
def s(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));return per_case_metrics(G,P),sorted(P)
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:s(BL[k][c],c) for k in PREV}
SC=list(PER);CORE=[c for c in SC if c not in EXCLUDE]
fu=[c for c in SC if vt.get(c,'').startswith('复诊')];fs=[c for c in SC if c not in fu]
def macro(k,m,cids):
    if m in('tp','fp','fn'):return sum(PER[c][k][0][m] for c in cids)
    v=[PER[c][k][0][m] for c in cids if PER[c][k][0][m] is not None]
    return round(statistics.mean(v),4)
def blk(k,cids):return dict(TP=macro(k,'tp',cids),FP=macro(k,'fp',cids),FN=macro(k,'fn',cids),
    R=macro(k,'recall',cids),P=macro(k,'prec',cids),F1=macro(k,'f1',cids),Jac=macro(k,'jac',cids))
out={nm:{k:blk(k,cids) for k in PREV} for nm,cids in [('全量86',SC),('核心集64',CORE),('M1_28',[c for c in SC if c in M1]),('未M1_58',[c for c in SC if c not in M1]),('复诊',fu),('首诊',fs)]}
diff=[]
for c in SC:
    a=set(PER[c]['v14r2'][1]);b=set(PER[c]['v14r5'][1])
    if a!=b:diff.append((c,sorted(b-a),sorted(a-b),PER[c]['v14r5'][0]['tp']-PER[c]['v14r2'][0]['tp'],PER[c]['v14r5'][0]['fp']-PER[c]['v14r2'][0]['fp']))
json.dump(out,open(os.path.join(HERE,'判分汇总v14r5.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('差异案:',diff)
# 巨阙/水道 gold 核验
for c in ['140_01','141_01','142_01','143_01','144_01','145_01','146_01','148_01','149_01']:
    G=set(NEW[c]['gold_members'])
    print(c,'巨阙in gold?',('巨阙' in G),'水道in gold?',('水道' in G))
