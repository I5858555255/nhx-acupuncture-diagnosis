#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P-N-B：生成 LLM 开放重提炼的**盲包**（每折一份，含训练数据 + 留出输入，绝不含留出 gold）。

每份 packet：
  说明.md         —— 任务与被禁文件（防泄漏控制）
  训练案.jsonl    —— {case_id, 症状, 主穴}（训练链，来自 gold）
  留出案输入.json —— {case_ids, 症状}（**无 gold、无基线预测**）
  留出案预测.json —— 由子代理写入（初始为空占位）

只读输入；只写 packets/。
"""
import csv
import io
import json
import os
import pickle

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
import sys
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

FOLDS = ["followup_66", "followup_198", "followup_146", "followup_216",
         "S_221_01", "S_160_01", "S_303_01", "S_195_01", "S_216_04", "S_13_01"]

NOTES = """# 盲法开放重提炼任务（P-N-B）

你是**独立盲法执行者**。禁止读取既有技能/规则/判分产物，只能读本目录 + 原书。

## 允许读
- 本目录 `训练案.jsonl`（该折的**训练链**：症状 → 主穴）
- 本目录 `留出案输入.json`（留出案的**症状**，**无答案**）
- 原书：`doubao-acupuncture-diagnosis/教程_utf8.txt`、`doubao-acupuncture-diagnosis/诊断与针灸实施指南.md`、
  `doubao-acupuncture-diagnosis/针灸篇-知识条目整理.md`、`doubao-acupuncture-diagnosis/references/`（可用 grep 检索）

## 严禁读（防泄漏）
- 任何 **gold / 答案 / 判分** 文件：`_gold_results93v2.pkl`、`判分汇总*.json`、任何含答案的 csv/json
- `doubao-acupuncture-diagnosis/SKILL.md`（既有规则）
- `blind法对照实验/`、`盲法对照实验/` 下的**既有规则池、归因、候选、复核**产物（避免借用既有结论）

## 任务
1. **从零开放重提炼**：只用 `训练案.jsonl`（必要时配合原书），自由提出你认为能解释
   「症状 → 主穴」的**规则/框架/模式**（不限于任何既有规则族；可自创特征、分层、配伍逻辑）。
2. **天真全案再推理**：对 `留出案输入.json` 中的每个留出案，**按其症状从零推理**出你预测的**主穴集合**
   （不要照搬训练案；允许跨经、配伍、层级取舍）。
3. **产出**：把预测写入本目录 `留出案预测.json`，格式严格为：
   `{"<案号>": ["穴1", "穴2", ...], ...}`（穴名为规范中文名；不含分层字段；不要输出解释）。

## 输出要求
- 只写 `留出案预测.json`，UTF-8，合法 JSON。
- 每案主穴数量自定（依据你的推理）。
- 不要读取或推断留出案的 gold。
"""

os.makedirs(os.path.join(HERE, "packets"), exist_ok=True)
for fid in FOLDS:
    ids = CHAINS[fid]
    train = [c for c in SC if c not in set(ids)]
    d = os.path.join(HERE, "packets", fid)
    os.makedirs(d, exist_ok=True)
    with io.open(os.path.join(d, "训练案.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for c in train:
            f.write(json.dumps({"case_id": c, "症状": SYM[c], "主穴": GOLD[c]}, ensure_ascii=False) + "\n")
    json.dump({"case_ids": ids, "症状": {c: SYM[c] for c in ids}},
              io.open(os.path.join(d, "留出案输入.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    io.open(os.path.join(d, "留出案预测.json"), "w", encoding="utf-8", newline="\n").write("{}\n")
    io.open(os.path.join(d, "说明.md"), "w", encoding="utf-8", newline="\n").write(NOTES)
    print("%-14s train=%2d holdout=%d (total cases=%d)" % (fid, len(train), len(ids), len(SC)))

json.dump({"folds": FOLDS, "total_cases": len(SC)},
          io.open(os.path.join(HERE, "PN_folds.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote packets/ for %d folds" % len(FOLDS))
