# -*- coding: utf-8 -*-
import json
s=json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v3\判分汇总.json',encoding='utf-8'))
pc=s['逐案变化']
# print compact rows: case v140 v2 v3 dv
for p in pc:
    print(f"{p['case_id']:9s} {p['v140']:.3f} {p['v2']:.3f} {p['v3']:.3f} {p['dv3_v2']:+.3f}")
