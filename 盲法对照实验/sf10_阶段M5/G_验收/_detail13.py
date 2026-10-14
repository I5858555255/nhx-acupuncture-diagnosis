# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
# visit_type 组装清单
vt={}
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段D','组装清单.csv'),encoding='utf-8-sig')):
    vt[r['case_id']]=r.get('visit_type','')
v13=json.load(open(os.path.join(HERE,'盲法v13','_blind93v13_results.json'),encoding='utf-8'))
rows=[]
for c in CASE_IDS:
    rec=v13[c]
    if len(NEW[c]['gold_members'])==0:
        rows.append([c,vt.get(c,''),SUMMARY['chain_map'].get(c,''),'不可判分',len(NEW[c]['gold_members']),len(rec.get('主穴',[])),'','','','','','','']);continue
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]))
    m=per_case_metrics(G,P)
    rows.append([c,vt.get(c,''),SUMMARY['chain_map'].get(c,''),'核心集' if c not in EXCLUDE else '排除',
                 len(G),len(rec.get('主穴',[])),m['tp'],m['fp'],m['fn'],
                 round(m['recall'],4),round(m['prec'],4),round(m['f1'],4),round(m['jac'],4)])
with open(os.path.join(HERE,'判分明细v13.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','visit_type','chain','核心集','gold穴数','主穴数','TP','FP','FN','R','P','F1','Jac']);w.writerows(rows)
print('rows',len(rows))
