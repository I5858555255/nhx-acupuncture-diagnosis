# -*- coding: utf-8 -*-
import json,os,glob
HERE=r'D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收'
files=glob.glob(os.path.join(HERE,'M9-fold_*_pred.json'))
print('折文件数',len(files))
allc=set()
for p in files:
    d=json.load(open(p,encoding='utf-8'))
    allc|=set(d.keys())
print('并集案数',len(allc))
print('样例',os.path.basename(files[0]),list(json.load(open(files[0],encoding='utf-8')).items())[:2])
# 链分组表
import csv
gp=os.path.join(HERE,'M9-链分组表.csv')
print('分组表存在',os.path.exists(gp))
if os.path.exists(gp):
    for r in list(csv.reader(open(gp,encoding='utf-8-sig')))[:5]:print(r)
