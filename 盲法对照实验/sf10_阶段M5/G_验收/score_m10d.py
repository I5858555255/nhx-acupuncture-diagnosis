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
PREV={'v14r7':os.path.join(HERE,'盲法v14r7','_blind93v14r7_results.json'),
      'v14r1':os.path.join(HERE,'盲法v14r1','_blind93v14r1_results.json')}
BL={k:json.load(open(p,encoding='utf-8')) for k,p in PREV.items()}
def s(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));return per_case_metrics(G,P),sorted(P)
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:s(BL[k][c],c) for k in PREV}
SC=list(PER);CORE=[c for c in SC if c not in EXCLUDE]
fu=[c for c in SC if vt.get(c,'').startswith('复诊')];fs=[c for c in SC if c not in fu]
def macro(k,sub,m,cids):
    if m in('tp','fp','fn'):return sum(PER[c][k][0][m] for c in cids)
    v=[PER[c][k][0][m] for c in cids if PER[c][k][0][m] is not None]
    return round(statistics.mean(v),4)
def blk(k,cids):return dict(TP=macro(k,None,'tp',cids),FP=macro(k,None,'fp',cids),FN=macro(k,None,'fn',cids),
    R=macro(k,None,'recall',cids),P=macro(k,None,'prec',cids),F1=macro(k,None,'f1',cids),Jac=macro(k,None,'jac',cids))
out={nm:{k:blk(k,cids) for k in PREV} for nm,cids in [('全量86',SC),('核心集64',CORE),('M1_28',[c for c in SC if c in M1]),('未M1_58',[c for c in SC if c not in M1]),('复诊',fu),('首诊',fs)]}
diff=[]
for c in SC:
    a=set(PER[c]['v14r7'][1]);b=set(PER[c]['v14r1'][1])
    if a!=b:diff.append((c,sorted(b-a),sorted(a-b),PER[c]['v14r1'][0]['tp']-PER[c]['v14r7'][0]['tp'],PER[c]['v14r1'][0]['fp']-PER[c]['v14r7'][0]['fp']))
json.dump(out,open(os.path.join(HERE,'判分汇总v14r1.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('差异案:',diff)
with open(os.path.join(HERE,'判分明细v14r1.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','核心集','TP','FP','FN','R','P','F1','Jac'])
    for c in SC:
        m=PER[c]['v14r1'][0];w.writerow([c,'核心集' if c not in EXCLUDE else '排除',m['tp'],m['fp'],m['fn'],round(m['recall'],4),round(m['prec'],4),round(m['f1'],4),round(m['jac'],4)])
