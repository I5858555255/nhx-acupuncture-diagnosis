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
PREV={'v12':os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),
      'v13':os.path.join(HERE,'盲法v13','_blind93v13_results.json'),
      'v13rc1':os.path.join(HERE,'盲法v13rc1','_blind93v13rc1_results.json')}
BL={k:json.load(open(p,encoding='utf-8')) for k,p in PREV.items()}
def score(rec,c):
    G=set(NEW[c]['gold_members']);Pm=normalize_units(rec.get('主穴',[]));Pa=normalize_units(rec.get('主穴',[])+rec.get('佐穴',[]))
    return dict(main=per_case_metrics(G,Pm),all=per_case_metrics(G,Pa),points_main=len(Pm),pred=sorted(Pm))
PER={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    PER[c]={k:score(BL[k][c],c) for k in PREV}
SCORED=list(PER);CORE=[c for c in SCORED if c not in EXCLUDE]
follow=[c for c in SCORED if SUMMARY['chain_map'].get(c,'').startswith('followup')]
fu66=[c for c in SCORED if SUMMARY['chain_map'].get(c,'').startswith('followup_66')]
def macro(k,subset,m,cids):
    v=[PER[c][k][subset][m] for c in cids if PER[c][k][subset][m] is not None]
    return statistics.mean(v) if v else None
def blk(k,cids):
    return dict(R=round(macro(k,'main','recall',cids),4),P=round(macro(k,'main','prec',cids),4),
                F1=round(macro(k,'main','f1',cids),4),Jac=round(macro(k,'main','jac',cids),4),
                allR=round(macro(k,'all','recall',cids),4),allF1=round(macro(k,'all','f1',cids),4),
                tp=sum(PER[c][k]['main']['tp'] for c in cids),fp=sum(PER[c][k]['main']['fp'] for c in cids),
                fn=sum(PER[c][k]['main']['fn'] for c in cids),
                mp=round(statistics.mean([PER[c][k]['points_main'] for c in cids]),2))
out={}
for nm,cids in [('全量86',SCORED),('核心集64',CORE),('复诊跟随',follow),('乳癌链66',fu66),('M1_28',[c for c in SCORED if c in M1]),('未M1_58',[c for c in SCORED if c not in M1])]:
    out[nm]={k:blk(k,cids) for k in PREV}
# 逐案 v13rc1 vs v13 差异
diff=[]
for c in SCORED:
    p13=set(PER[c]['v13']['pred']);pr=set(PER[c]['v13rc1']['pred'])
    if p13!=pr:diff.append((c,sorted(pr-p13),sorted(p13-pr),PER[c]['v13rc1']['main']['tp']-PER[c]['v13']['main']['tp'],PER[c]['v13rc1']['main']['fp']-PER[c]['v13']['main']['fp']))
json.dump(out,open(os.path.join(HERE,'判分汇总v13rc1.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('v13rc1 vs v13 差异案:',diff)
# 明细csv
with open(os.path.join(HERE,'判分明细v13rc1.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','chain','核心集','gold穴数','主穴数','TP','FP','FN','R','P','F1','Jac'])
    for c in CASE_IDS:
        rec=BL['v13rc1'][c]
        if len(NEW[c]['gold_members'])==0:w.writerow([c,SUMMARY['chain_map'].get(c,''),'不可判分',0,len(rec.get('主穴',[])),'','','','','','','']);continue
        G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));m=per_case_metrics(G,P)
        w.writerow([c,SUMMARY['chain_map'].get(c,''),'核心集' if c not in EXCLUDE else '排除',len(G),len(rec.get('主穴',[])),m['tp'],m['fp'],m['fn'],round(m['recall'],4),round(m['prec'],4),round(m['f1'],4),round(m['jac'],4)])
