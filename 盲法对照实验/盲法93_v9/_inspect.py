# -*- coding: utf-8 -*-
import json
s=json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v9\判分汇总.json',encoding='utf-8'))
print('---层间 v6/v8/v9 出单元/命中案---')
for L in ['对症','俞募背俞','八脉交会','特效奇穴']:
    print(L,'v6',s['层_v6'][L]['出单元'],s['层_v6'][L]['命中案'],
          '| v8',s['层_v8'][L]['出单元'],s['层_v8'][L]['命中案'],
          '| v9',s['层_v9'][L]['出单元'],s['层_v9'][L]['命中案'])
print('v9较v6下降:',json.dumps(s['v9较v6下降'],ensure_ascii=False))
print('v9较v8上升:',json.dumps(s['v9较v8上升'],ensure_ascii=False))
for c in ['107_01','156_05','311_01','60_01','340_01']:
    v=s['重点'][c];print(c,'v6=',v['v6'],'v8=',v['v8'],'v9=',v['v9'],'命中=',v['v9命中'])
