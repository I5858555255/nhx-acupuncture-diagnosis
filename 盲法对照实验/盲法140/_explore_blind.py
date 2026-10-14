# -*- coding: utf-8 -*-
import json, collections

BASE = r"D:\projectAGI\nhx\盲法对照实验\盲法140"
with open(BASE + r"\_blind140_results.json", encoding="utf-8") as f:
    data = json.load(f)

print("cases:", len(data))
main_pts = collections.Counter()
aux_pts = collections.Counter()
alt_pts = collections.Counter()
layer_pts = collections.defaultdict(collections.Counter)
empty_gold_needed = []
for cid, rec in data.items():
    for p in rec.get("主穴", []):
        main_pts[p] += 1
    for p in rec.get("佐穴", []):
        aux_pts[p] += 1
    for p in rec.get("备选", []):
        alt_pts[p] += 1
    for layer, pts in rec.get("主穴分层", {}).items():
        for p in pts:
            layer_pts[layer][p] += 1

print("\n=== 主穴 unique units (%d) ===" % len(main_pts))
for p, n in sorted(main_pts.items(), key=lambda x: -x[1]):
    print(f"{n:3d}  {p}")

print("\n=== 佐穴 unique (%d) ===" % len(aux_pts))
for p, n in sorted(aux_pts.items(), key=lambda x: -x[1]):
    print(f"{n:3d}  {p}")

print("\n=== 备选 unique (%d) ===" % len(alt_pts))
for p, n in sorted(alt_pts.items(), key=lambda x: -x[1]):
    print(f"{n:3d}  {p}")

print("\n=== 分层 ===")
for layer, ctr in layer_pts.items():
    print(f"--- {layer} ({sum(ctr.values())} occurrences, {len(ctr)} unique) ---")
    for p, n in sorted(ctr.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {p}")

# check layers union == main
bad = []
for cid, rec in data.items():
    main = set(rec.get("主穴", []))
    layers = set()
    for pts in rec.get("主穴分层", {}).values():
        layers |= set(pts)
    if main != layers:
        bad.append((cid, main, layers))
print("\nlayers union != main cases:", len(bad))
for b in bad[:10]:
    print(b)
