# -*- coding: utf-8 -*-
import json, os
ROOT=r'D:\projectAGI\nhx\盲法对照实验'
for name,p in [('B',os.path.join(ROOT,'sf10_阶段M5','B_输入实验','盲法B','_blind93v12b_results.json')),
               ('C',os.path.join(ROOT,'sf10_阶段M5','B_输入实验','盲法C','_blind93v12c_results.json'))]:
    try:
        o=json.load(open(p,encoding='utf-8'))
        ks=list(o.keys())
        print(name,'n=',len(ks),'107 keys=',list(o['107_01'].keys())[:6])
        print('  107 主穴=',o['107_01'].get('主穴'))
    except Exception as e:
        print(name,'ERR',e)
# canonical scorer
cs=os.path.join(ROOT,'benchmark_v2','canonical_scorer.py')
print('canonical exists=',os.path.exists(cs))
if os.path.exists(cs):print(open(cs,encoding='utf-8').read()[:1500])
