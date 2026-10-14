# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
M1=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M5','A_迁移核验','迁移核验逐案表.csv'),encoding='utf-8-sig')) if r['M1审计案']=='Y')
PREV={'v13rc1':os.path.join(HERE,'盲法v13rc1','_blind93v13rc1_results.json'),
      'v14r7':os.path.join(HERE,'盲法v14r7','_blind93v14r7_results.json')}
BL={k:json.load(open(p,encoding='utf-8')) for k,p in PREV.items()}
def s(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));Pa=normalize_units(rec.get('主穴',[])+rec.get('佐穴',[]))
    return dict(main=per_case_metrics(G,P),all=per_case_metrics(G,Pa),pred=sorted(P))
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:s(BL[k][c],c) for k in PREV}
SCORED=list(PER);CORE=[c for c in SCORED if c not in EXCLUDE]
follow=[c for c in SCORED if SUMMARY['chain_map'].get(c,'').startswith('followup')]
def macro(k,subset,m,cids):
    v=[PER[c][k][subset][m] for c in cids if PER[c][k][subset][m] is not None]
    return statistics.mean(v) if v else None
def blk(k,cids):
    return dict(R=round(macro(k,'main','recall',cids),4),P=round(macro(k,'main','prec',cids),4),
                F1=round(macro(k,'main','f1',cids),4),Jac=round(macro(k,'main','jac',cids),4),
                tp=sum(PER[c][k]['main']['tp'] for c in cids),fp=sum(PER[c][k]['main']['fp'] for c in cids),
                fn=sum(PER[c][k]['main']['fn'] for c in cids))
out={nm:{k:blk(k,cids) for k in PREV} for nm,cids in [('全量86',SCORED),('核心集64',CORE),('M1_28',[c for c in SCORED if c in M1]),('未M1_58',[c for c in SCORED if c not in M1]),('复诊跟随',follow)]}
diff=[]
for c in SCORED:
    a=set(PER[c]['v13rc1']['pred']);b=set(PER[c]['v14r7']['pred'])
    if a!=b:diff.append((c,sorted(b-a),sorted(a-b),PER[c]['v14r7']['main']['tp']-PER[c]['v13rc1']['main']['tp'],PER[c]['v14r7']['main']['fp']-PER[c]['v13rc1']['main']['fp']))
json.dump(out,open(os.path.join(HERE,'判分汇总v14r7.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('v14r7 vs v13rc1 差异案:',diff)
with open(os.path.join(HERE,'判分明细v14r7.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','chain','核心集','gold穴数','TP','FP','FN','R','P','F1','Jac'])
    for c in CASE_IDS:
        rec=BL['v14r7'][c]
        if len(NEW[c]['gold_members'])==0:w.writerow([c,'','不可判分',0,'','','','','','','']);continue
        G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));m=per_case_metrics(G,P)
        w.writerow([c,SUMMARY['chain_map'].get(c,''),'核心集' if c not in EXCLUDE else '排除',len(G),m['tp'],m['fp'],m['fn'],round(m['recall'],4),round(m['prec'],4),round(m['f1'],4),round(m['jac'],4)])
