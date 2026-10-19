#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-B 全量：为**其余**折生成盲包（已完成的 10 折不覆盖其预测）。"""
import csv
import io
import json
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
G = os.path.join(EXP, "sf10_阶段M5", "G_验收")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
sys.path.insert(0, BENCH)
from canonical_scorer import normalize_units  # noqa: E402

gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
NEW = gold["results"]
SC = [c for c in gold["case_ids"] if len(NEW[c]["gold_members"]) > 0]
GOLD = {c: sorted(normalize_units(NEW[c]["gold_members"])) for c in SC}
CHAINS = {}
for r in csv.DictReader(io.open(os.path.join(G, "M9-链分组表.csv"), encoding="utf-8-sig")):
    if not str(r.get("在86判分", "")).strip().isdigit() or int(str(r["在86判分"]).strip()) <= 0:
        continue
    ids = [x for x in str(r["案号列表"]).split() if x in set(SC)]
    if ids:
        CHAINS[r["链ID"]] = ids


def sym(c):
    d = json.load(io.open(os.path.join(SD, "%s_symptoms_v2.json" % c), encoding="utf-8"))
    b = []
    for k, v in d.items():
        if isinstance(v, dict) and "片段" in v:
            b.append(str(v["片段"]))
        elif isinstance(v, str):
            b.append(v)
    return "".join(b)


SYM = {c: sym(c) for c in SC}
DONE = json.load(io.open(os.path.join(HERE, "PN_folds.json"), encoding="utf-8"))["folds"]
ALL = sorted(CHAINS)
TODO = [f for f in ALL if f not in DONE]

for fid in TODO:
    ids = CHAINS[fid]
    train = [c for c in SC if c not in set(ids)]
    d = os.path.join(HERE, "packets", fid)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, "训练案.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for c in train:
            f.write(json.dumps({"case_id": c, "症状": SYM[c], "主穴": GOLD[c]}, ensure_ascii=False) + "\n")
    json.dump({"case_ids": ids, "症状": {c: SYM[c] for c in ids}},
              io.open(os.path.join(d, "留出案输入.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    pj = os.path.join(d, "留出案预测.json")
    if not os.path.exists(pj):
        io.open(pj, "w", encoding="utf-8", newline="\n").write("{}\n")
    NOTES = io.open(os.path.join(HERE, "packets", DONE[0], "说明.md"), encoding="utf-8").read()
    io.open(os.path.join(d, "说明.md"), "w", encoding="utf-8", newline="\n").write(NOTES)

json.dump({"total_folds": len(ALL), "done": DONE, "todo": TODO},
          io.open(os.path.join(HERE, "PN_folds_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("total scored folds=%d ; done=%d ; TODO=%d" % (len(ALL), len(DONE), len(TODO)))
print(" ".join(TODO))
