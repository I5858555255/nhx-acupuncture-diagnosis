# -*- coding: utf-8 -*-
import json, pickle, os, csv, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"D:\projectAGI\nhx\盲法对照实验"

# 1. blind results json
with open(os.path.join(BASE, r"盲法93_v10\_blind93v10_results.json"), encoding='utf-8') as f:
    blind = json.load(f)
print("=== blind json type:", type(blind))
if isinstance(blind, dict):
    print("keys:", list(blind.keys())[:10])
    # find cases
    cases = blind.get('results') or blind.get('cases') or blind
else:
    cases = blind
print("n cases:", len(cases))
# print first case structure
import pprint
c0 = cases[0] if isinstance(cases, list) else list(cases.items())[0]
if isinstance(cases, dict):
    k0, v0 = c0
    print("case key:", k0)
    pprint.pprint(v0, depth=4, width=120)
else:
    pprint.pprint(c0, depth=4, width=120)
