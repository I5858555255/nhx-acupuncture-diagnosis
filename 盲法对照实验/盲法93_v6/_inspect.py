# -*- coding: utf-8 -*-
import json
s=json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v6\判分汇总.json',encoding='utf-8'))
for c in ['60_01','62_01','63_01','117_01','118_01','274_01','340_01','312_01','201_01','207_01','318_01','107_01','216_04']:
    v=s['重点'][c]
    print(c,'v5=',v['v5'],'v6=',v['v6'],'命中=',v['v6命中'])
print('---层间 出单元/命中案---')
for L in ['对症','俞募背俞','八脉交会','特效奇穴']:
    print(L,'v5',s['层_v5'][L]['出单元'],s['层_v5'][L]['命中案'],'| v6',s['层_v6'][L]['出单元'],s['层_v6'][L]['命中案'])
print('特效 v5:',s['特效_v5'],'v6:',s['特效_v6'])
print('上升:',json.dumps(s['v6较v5上升'],ensure_ascii=False))
print('教程未录:',json.dumps(s['教程未录_v6'],ensure_ascii=False))
