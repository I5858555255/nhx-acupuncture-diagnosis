# -*- coding: utf-8 -*-
import csv,os
HERE=r'D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收'
m6={r['链']:float(r['v13_F1']) for r in csv.DictReader(open(os.path.join(HERE,'按链留出验证表.csv'),encoding='utf-8-sig'))}
m9rows=list(csv.DictReader(open(os.path.join(HERE,'M9-每折结果.csv'),encoding='utf-8-sig')))
def norm(k):
    return k.replace('followup_','') if k.startswith('followup_') else k
up=down=eq=0;detail=[]
for r in m9rows:
    a=m6.get(norm(r['链']))
    b=float(r['F1'])
    if a is None:continue
    d=round(b-a,4)
    if d>0.001:up+=1
    elif d<-0.001:down+=1
    else:eq+=1
    if abs(d)>0.05:detail.append((r['链'],a,b,d))
print('升',up,'降',down,'持平',eq,'对照数',up+down+eq)
print('大变(>0.05):',detail)
