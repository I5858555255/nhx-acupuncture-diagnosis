# -*- coding: utf-8 -*-
import json
v8=json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v8\_blind93v8_results.json',encoding='utf-8'))
# 86可判分案
scored=[c for c in v8 if c not in ('80_01','178_01','278_01','284_01','285_01','268_01','116_01')]
scored=sorted(scored)
# 均匀抽20案
step=len(scored)/20
sample=[scored[int(i*step)] for i in range(20)]
print('抽样20案:',sample)
MISS=[]
tot=0;ok=0
for c in sample:
    rec=v8[c]
    rp=rec.get('推理要点','')
    for pt in rec.get('主穴',[]):
        # 组分: 透/X+Y 拆
        parts=set()
        if '透' in pt:
            parts=set(pt.split('透'))
        elif '+' in pt:
            parts=set(x.strip() for x in pt.split('+'))
        else:
            parts={pt}
        for p in parts:
            tot+=1
            # 该穴名是否出现在推理要点
            if p in rp:
                ok+=1
            else:
                MISS.append((c,pt,p))
print(f'总组分 {tot}, 推理要点中出现 {ok}, 缺失 {tot-ok}')
for m in MISS:print('  缺失:',m)
