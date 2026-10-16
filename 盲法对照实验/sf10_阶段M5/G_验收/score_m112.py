# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
v14r2=json.load(open(os.path.join(HERE,'盲法v14r2','_blind93v14r2_results.json'),encoding='utf-8'))
# cfA = v14r2 - 194_01 R7b 商丘透丘墟
cfA=json.loads(json.dumps(v14r2))
cfA['194_01']['主穴']=[u for u in cfA['194_01']['主穴'] if u!='商丘透丘墟']
json.dump(cfA,open(os.path.join(HERE,'_r7bcfA_results.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
SC=[c for c in CASE_IDS if len(NEW[c]['gold_members'])>0]
CORE=[c for c in SC if c not in EXCLUDE]
def score(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));return per_case_metrics(G,P)
def agg(d,cids):
    tp=fp=fn=0;f1s=[]
    for c in cids:
        m=score(d[c],c);tp+=m['tp'];fp+=m['fp'];fn+=m['fn']
        if m['f1'] is not None:f1s.append(m['f1'])
    return dict(TP=tp,FP=fp,FN=fn,F1=round(statistics.mean(f1s),4),Jac=round(tp/(tp+fp+fn),4) if tp+fp+fn else 0)
out={'v14r2':{},'cfA':{}}
for nm,cids in [('全量86',SC),('核心集64',CORE)]:
    out['v14r2'][nm]=agg(v14r2,cids);out['cfA'][nm]=agg(cfA,cids)
json.dump(out,open(os.path.join(HERE,'判分汇总cfA.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=1))
print('194 cfA P∩gold=',sorted(set(NEW['194_01']['gold_members'])&normalize_units(cfA['194_01'].get('主穴',[]))))
