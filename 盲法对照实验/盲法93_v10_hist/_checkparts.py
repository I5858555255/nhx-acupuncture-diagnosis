# -*- coding: utf-8 -*-
import json, os
d=r'D:\projectAGI\nhx\盲法对照实验\盲法93_v10_hist'
allids=[]
for i in range(1,6):
    fp=os.path.join(d,f'_blind93v10_hist_part{i}.json')
    o=json.load(open(fp,encoding='utf-8'))
    print(f'part{i}: type={type(o).__name__} len={len(o)}')
    if isinstance(o,list):
        for e in o:
            cid=e.get('case_id') if isinstance(e,dict) else None
            allids.append(cid)
print('合计案=',len(allids),'唯一=',len(set(allids)))
print('缺案 vs 93全集:')
import pickle
g=pickle.load(open(r'D:\projectAGI\nhx\盲法对照实验\benchmark_v2\_gold_results93v2.pkl','rb'))
full=set(g['case_ids'])
have=set(x for x in allids if x)
print('缺失:',sorted(full-have))
