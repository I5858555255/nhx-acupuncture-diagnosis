# -*- coding: utf-8 -*-
import json,os,sys,pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results']
v12=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
v13=json.load(open(os.path.join(ROOT,'sf10_阶段M5','G_验收','盲法v13','_blind93v13_results.json'),encoding='utf-8'))
RULES={'R2(肺积水分型:复溜水泉照海公孙内关巨阙关元)':{'复溜','水泉','照海','公孙','内关','巨阙','关元'},
 'R3(五十肩曲池足三里)':{'曲池','足三里'},
 'RC-5(神门大陵)':{'神门','大陵'},
 'RC-6(委中承山腰腿点)':{'委中','承山','腰腿点'}}
for nm,pset in RULES.items():
    trig=[];tp_new=0;fp_new=0
    for c in v13:
        if len(NEW[c]['gold_members'])==0:continue
        p13=normalize_acupoints(v13[c].get('主穴',[]));p12=normalize_acupoints(v12[c].get('主穴',[]))
        newpts=p13-p12
        hit=newpts&pset
        if hit:
            G=set(NEW[c]['gold_members'])
            trig.append(c)
            tp_new+=len(hit&G);fp_new+=len(hit-G)
    print(nm,'触发案',len(trig),'新增TP',tp_new,'新增FP',fp_new,'净',tp_new-fp_new)
    print('  案:',trig)
