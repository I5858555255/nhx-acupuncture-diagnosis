# -*- coding: utf-8 -*-
import json, pickle, os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"

with open(os.path.join(BASE, r"benchmark_v2\_gold_results93v2.pkl"), 'rb') as f:
    gold = pickle.load(f)
print("=== gold type:", type(gold))
if isinstance(gold, dict):
    print("keys:", list(gold.keys())[:20])
    # maybe keyed by case
    import pprint
    k = '107_01'
    if k in gold:
        v = gold[k]
        print("--- gold[107_01] type:", type(v))
        pprint.pprint(v, depth=5, width=140)
    else:
        # maybe it's a dict of lists
        k0 = list(gold.keys())[0]
        print("first key:", k0)
        pprint.pprint(gold[k0], depth=5, width=140)
