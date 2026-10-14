# -*- coding: utf-8 -*-
import json, os, sys
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)

# 全局: point -> layer counter (from v10 主穴记录)
pt_layer = defaultdict(Counter)
layers_seen = Counter()
for cid, c in cons.items():
    for p, recs in c['pointmap'].items():
        for r in recs:
            pt_layer[p][r['层']] += 1
            layers_seen[r['层']] += 1

print("=== v10 出现过的层 ===")
for l, n in layers_seen.most_common():
    print(f"  {l}: {n}")

print("\n=== 点->层 映射 (全局) ===")
for p in sorted(pt_layer):
    top = pt_layer[p].most_common(1)[0]
    print(f"  {p}: {top[0]} ({dict(pt_layer[p])})")

# FN / FP 频次
fn_freq = Counter(); fp_freq = Counter()
fn_cases = defaultdict(list); fp_cases = defaultdict(list)
for cid, c in cons.items():
    for p in c['FN']:
        fn_freq[p] += 1; fn_cases[p].append(cid)
    for p in c['FP']:
        fp_freq[p] += 1; fp_cases[p].append(cid)

print("\n=== FN 频次 (漏穴) ===")
for p, n in fn_freq.most_common(30):
    print(f"  {p}: {n}  e.g. {fn_cases[p][:6]}")

print("\n=== FP 频次 (误加) ===")
for p, n in fp_freq.most_common(30):
    print(f"  {p}: {n}  e.g. {fp_cases[p][:6]}")

# 每案 FN/FP 数量概览
print("\n=== 有FN或FP的案 ===")
for cid, c in cons.items():
    if c['FN'] or c['FP']:
        print(f"{cid} [{c['visit_type'][:2]}] TP={len(c['TP'])} gold={c['gold_n_csv']} FN={c['FN']} FP={c['FP']}")
