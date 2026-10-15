# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
v14=json.load(open(os.path.join(HERE,'盲法v14r7','_blind93v14r7_results.json'),encoding='utf-8'))
cfA=json.load(open(os.path.join(HERE,'_r6cfA_results.json'),encoding='utf-8'))
cfB=json.load(open(os.path.join(HERE,'_r6cfB_results.json'),encoding='utf-8'))
print('cfA keys',len(cfA),'sample 199=',cfA.get('199_01'))
print('cfB 199=',cfB.get('199_01'))
print('v14 199 主穴=',v14['199_01'].get('主穴'))
