# -*- coding: utf-8 -*-
import json
v9=json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v9\_blind93v9_results.json',encoding='utf-8'))
scored=[c for c in v9 if c not in ('80_01','178_01','278_01','284_01','285_01','268_01','116_01')]
scored=sorted(scored)
step=len(scored)/20
sample=[scored[int(i*step)] for i in range(20)]
print('抽样20案:',sample)
tot=0;ok=0;miss=[]
markers=['指南','特效库','治则库','知识条目','条目','库','经']
for c in sample:
    rec=v9[c];rp=rec.get('推理要点','')
    for pt in rec.get('主穴',[]):
        parts=set(pt.split('透')) if '透' in pt else (set(x.strip() for x in pt.split('+')) if '+' in pt else {pt})
        for p in parts:
            tot+=1
            if p in rp:ok+=1
            else:miss.append((c,pt,p))
    if not any(m in rp for m in markers):miss.append((c,'<案级无出处标记>',''))
print(f'主穴组分 {tot}, 推理要点出现 {ok}, 缺失 {tot-ok}')
for m in miss:print('  缺失:',m)
