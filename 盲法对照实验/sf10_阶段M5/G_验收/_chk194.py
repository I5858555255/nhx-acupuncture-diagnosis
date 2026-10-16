# -*- coding: utf-8 -*-
import json,os,sys,pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results']
v14r2=json.load(open(os.path.join(HERE,'盲法v14r2','_blind93v14r2_results.json'),encoding='utf-8'))
for c in ['194_01','207_01']:
    P=normalize_units(v14r2[c].get('主穴',[]));G=set(NEW[c]['gold_members'])
    print(c,'主穴=',v14r2[c].get('主穴'))
    print('  规范化P=',sorted(P),'gold=',sorted(G))
    print('  P∩gold=',sorted(P&G),'P-gold=',sorted(P-G))
