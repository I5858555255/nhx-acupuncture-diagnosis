# -*- coding: utf-8 -*-
import json, os, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)

# 查高频FP穴的触发规则
targets = ['肘尖','膻中','大包','心俞','肺俞','太溪','痞根','间使']
agg = {t: Counter() for t in targets}
for cid,c in cons.items():
    for p in c['FP']:
        if p in targets:
            for r in c['pointmap'].get(p,[]):
                agg[p][r['直接规则']] += 1
for t in targets:
    print(t, dict(agg[t]))
