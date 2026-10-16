# -*- coding: utf-8 -*-
import json,glob,os
HERE=r'D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收\盲法v14r1'
files=sorted(glob.glob(os.path.join(HERE,'_blind93v14r1_part*.json')))
print('片数',len(files))
m={}
for p in files:
    for rec in json.load(open(p,encoding='utf-8')):m[rec['case_id']]=rec
print('合并案数',len(m))
json.dump(m,open(os.path.join(HERE,'_blind93v14r1_results.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('208_01 主穴=',m['208_01'].get('主穴'))
print('221_01 主穴=',m['221_01'].get('主穴'))
