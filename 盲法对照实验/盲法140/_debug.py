# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r"D:\projectAGI\nhx\盲法对照实验\盲法140")
from gold_parse import extract_tokens, t2s, CANON

for cid in ['63_01','249_01','194_01','1_01','346_01','209_01']:
    p = rf"D:\projectAGI\nhx\盲法对照实验\全集针灸首诊\prescriptions\{cid}_prescription.txt"
    raw = open(p, encoding='utf-8').read()
    lines = [ln for ln in raw.splitlines() if not __import__('re').match(r'^\s*doc\(', ln)]
    body = ' '.join(lines)
    body = t2s(body)
    print(f"===== {cid} =====")
    print("BODY:", body[:200])
    toks = extract_tokens(raw)
    print("TOKENS:", toks)
    print()

# check membership
for name in ['天突','太冲','行间','曲池','神门','承山','肩髃','肩禺','膝关','三里','腿腰点','第十椎']:
    print(f"CANON has {name}: {name in CANON}")
