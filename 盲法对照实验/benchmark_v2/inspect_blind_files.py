# -*- coding: utf-8 -*-
"""inspect_blind_files.py — 探查 9 轮盲法结果 JSON 的结构与字段一致性"""
import json, os

ROOT = r"D:\projectAGI\nhx\盲法对照实验"
FILES = {
    "v140": os.path.join(ROOT, "盲法140", "_blind140_results.json"),
    "v2":   os.path.join(ROOT, "盲法93", "_blind93_results.json"),
    "v3":   os.path.join(ROOT, "盲法93_v3", "_blind93v3_results.json"),
    "v4":   os.path.join(ROOT, "盲法93_v4", "_blind93v4_results.json"),
    "v5":   os.path.join(ROOT, "盲法93_v5", "_blind93v5_results.json"),
    "v6":   os.path.join(ROOT, "盲法93_v6", "_blind93v6_results.json"),
    "v7":   os.path.join(ROOT, "盲法93_v7", "_blind93v7_results.json"),
    "v8":   os.path.join(ROOT, "盲法93_v8", "_blind93v8_results.json"),
    "v9":   os.path.join(ROOT, "盲法93_v9", "_blind93v9_results.json"),
}

for lab, f in FILES.items():
    if not os.path.exists(f):
        print(f"{lab}: MISSING {f}")
        continue
    with open(f, encoding="utf-8") as fh:
        data = json.load(fh)
    ids = list(data.keys())
    rec = data[ids[0]]
    fields = list(rec.keys()) if isinstance(rec, dict) else type(rec).__name__
    main_type = type(rec.get("主穴")).__name__ if isinstance(rec, dict) else "?"
    n_main = len(rec.get("主穴", [])) if isinstance(rec.get("主穴"), list) else "?"
    aux_type = type(rec.get("佐穴")).__name__ if isinstance(rec, dict) else "?"
    print(f"{lab}: cases={len(ids)} fields={fields}")
    print(f"   main_type={main_type} n_main(first)={n_main} aux_type={aux_type} layers={'主穴分层' in fields}")
    # 统计主穴含透/+ 的案数
    n_tou = n_plus = n_zu = 0
    for cid in ids:
        for u in data[cid].get("主穴", []):
            if "透" in u: n_tou += 1
            if "+" in u: n_plus += 1
        for u in data[cid].get("佐穴", []):
            if "透" in u: n_tou += 1
            if "+" in u: n_plus += 1
    print(f"   units with 透={n_tou}, with += {n_plus}")
    # 组穴名出现情况（膝五针/三皇穴/开四关）
    for kw in ["膝五针", "三皇穴", "开四关"]:
        hit = [cid for cid in ids for u in data[cid].get("主穴", []) + data[cid].get("佐穴", []) if kw in u]
        if hit:
            print(f"   {kw}: {len(hit)} cases e.g. {hit[:5]}")
