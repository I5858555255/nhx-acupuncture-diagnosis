# -*- coding: utf-8 -*-
"""任务2/3 构建公共：清洗泄漏段、生成 inputB/inputC、外伤扫描。"""
import os, re, json, io, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _commons import (SYM_V2_DIR, FULL_DIR, OUT_DIR, BIZ_FIELDS, MISSING_MARK,
                      scan_text, field_frag, is_missing)

ASSEMBLE_CSV = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段D\组装清单.csv"
OLD_SYM_DIR = r"D:\projectAGI\nhx\盲法对照实验\盲法93\symptoms"

# 强处方标记（命中即整段剔除）
STRONG_MARKERS = ["針灸處方","针灸处方","針處方","中藥處方","中药处方","下針","下针",
    "取穴","配穴","埋針","埋针","埋耳針","放血","隔薑灸","隔姜灸","溫灸","温灸",
    "補瀉","补泻","同前穴","針同前","針同","同穴","開四關","膝五針","三皇穴","眼四針",
    "處方","处方","針灸","针灸","透頰車","透頬車","透魚腰","透率谷","透內迎香",
    "透間使","透後谿","透后溪","開四關","HT-","加埋","穴：","穴位"]
# 注意：'處方/針灸' 作为强标记，凡含即剔除（既往字段中出现即视为引用了治疗方案）

def load_assemble():
    rows = {}
    with io.open(ASSEMBLE_CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows[r["case_id"]] = r
    return rows

def iter_segments(field_val):
    """既往字段可能是 dict{片段} 或 list[dict{片段}]。返回 [片段str,...]。"""
    out = []
    if isinstance(field_val, list):
        for it in field_val:
            if isinstance(it, dict):
                out.append(it.get("片段","") or "")
            elif isinstance(it, str):
                out.append(it)
    elif isinstance(field_val, dict):
        out.append(field_val.get("片段","") or "")
    elif isinstance(field_val, str):
        out.append(field_val)
    return [s for s in out if s and s != MISSING_MARK]

def split_sub(text):
    """按句读切段。"""
    parts = re.split(r"[；;。\n]", text)
    return [p.strip() for p in parts if p.strip()]

def clean_history_field(field_val):
    """返回 (kept_text, stripped_list)。stripped_list=[(sub, reason)]。"""
    kept, stripped = [], []
    # 额外正则：针刺方向动词、穴名枚举列表
    rx_needle_dir = re.compile(r"針\s*[左右雙患]")
    for seg in iter_segments(field_val):
        for sub in split_sub(seg):
            hit_markers = [m for m in STRONG_MARKERS if m in sub]
            hit_dir = bool(rx_needle_dir.search(sub))
            # 穴名枚举：含 >=2 个穴名且以 、 连接
            acu_hits = [w for (k,w,_) in scan_text(sub) if k=="穴名"]
            acu_list = ("、" in sub) and len(set(acu_hits)) >= 2
            if hit_markers or hit_dir or acu_list:
                reason = []
                if hit_markers: reason.append("强处方标记:"+"/".join(sorted(set(hit_markers))))
                if hit_dir: reason.append("针刺方位动词(針左/右/雙)")
                if acu_list: reason.append("穴名枚举("+"/".join(sorted(set(acu_hits))) + ")")
                stripped.append((sub, "；".join(reason)))
            else:
                kept.append(sub)
    return "；".join(kept), stripped

def get_field_raw(d, key):
    v = d.get(key)
    if isinstance(v, dict):
        return v.get("片段","") or ""
    if isinstance(v, list):
        return "；".join((it.get("片段","") if isinstance(it,dict) else str(it)) for it in v)
    return v if isinstance(v,str) else ""
