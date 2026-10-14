# -*- coding: utf-8 -*-
import json, os, csv
ROOT=r'D:\projectAGI\nhx\盲法对照实验'
# v11
v11=json.load(open(os.path.join(ROOT,'盲法93_v11','_blind93v11_results.json'),encoding='utf-8'))
print('v11 n=',len(v11),'keys=',list(v11['107_01'].keys()))
print('v11 107_01 主穴=',v11['107_01'].get('主穴'))
# 排除清单
ex=os.path.join(ROOT,'sf10_核心集','排除清单.csv')
print('排除清单 exists=',os.path.exists(ex))
if os.path.exists(ex):
    rows=list(csv.reader(open(ex,encoding='utf-8-sig')))
    print('排除清单 rows=',len(rows),'header=',rows[0])
    print('body=',[r[0] for r in rows[1:]])
# visit_type
vt=os.path.join(ROOT,'sf10_阶段D','组装清单.csv')
print('组装 exists=',os.path.exists(vt))
vrows=list(csv.DictReader(open(vt,encoding='utf-8-sig')))
print('visit_type 取值=',set(r['visit_type'] for r in vrows))
# 改动评估
ce=os.path.join(ROOT,'sf10_阶段E','候选规则改动评估表.csv')
print('改动评估 exists=',os.path.exists(ce))
if os.path.exists(ce):
    for r in csv.reader(open(ce,encoding='utf-8-sig')):
        print('  ',r)
