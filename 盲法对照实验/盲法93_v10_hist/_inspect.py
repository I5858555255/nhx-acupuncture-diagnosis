# -*- coding: utf-8 -*-
import re, json
import re, json
p=r'D:\projectAGI\nhx\盲法对照实验\盲法93_v10_hist\_blind93v10_hist_results.json'
txt=open(p,encoding='utf-8').read()
ids=re.findall(r'"(\d+_\d+)":\s*\{', txt)
print('全部案键:',ids)
print('n=',len(ids))
