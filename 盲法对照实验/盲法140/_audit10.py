# -*- coding: utf-8 -*-
import json, pickle, os
BASE=r"D:\projectAGI\nhx\盲法对照实验\盲法140"
blind=json.load(open(os.path.join(BASE,'_blind140_results.json'),encoding='utf-8'))
g=pickle.load(open(os.path.join(BASE,'_gold_results.pkl'),'rb'))
results=g['results']; case_ids=g['case_ids']
idxs=[0,15,30,45,60,75,90,105,120,135]
for i in idxs:
    c=case_ids[i]
    r=results[c]
    print(f"===== [{i}] {c} =====")
    print("原文:", r['raw'].strip())
    print("机器解析gold:", r['gold_members'], "count=", r['gold_count'])
    rec=blind[c]
    print("盲法主穴:", rec.get('主穴'))
    print("盲法佐穴:", rec.get('佐穴'))
    print()
