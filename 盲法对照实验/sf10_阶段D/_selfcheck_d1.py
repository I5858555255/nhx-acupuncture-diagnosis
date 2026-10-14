# -*- coding: utf-8 -*-
import json, os, pickle, random

BASE = r"D:\projectAGI\nhx\盲法对照实验"
SRC = os.path.join(BASE, "sf10_阶段C", "symptoms_v2")
OUT = os.path.join(BASE, "sf10_阶段D", "inputs_hist")
PKL = os.path.join(BASE, "benchmark_v2", "_gold_results93v2.pkl")

gold = pickle.load(open(PKL, "rb"))
chain_map = gold["summary"]["chain_map"]

FIELDS = ["來診日期", "病程", "來診原因", "主诉变化", "問診",
          "望诊", "舌象", "脉象", "触诊压痛", "耳穴", "西醫診斷", "備註"]

def frag(v):
    if isinstance(v, dict):
        s = v.get("片段", "原文未记录")
        return s if isinstance(s, str) else "原文未记录"
    if isinstance(v, list):
        parts = []
        for it in v:
            s = it.get("片段", "") if isinstance(it, dict) else str(it)
            if s and s != "原文未记录":
                parts.append(s)
        return "\n".join(parts) if parts else "原文未记录"
    return v if isinstance(v, str) else "原文未记录"

files = sorted(os.listdir(OUT))
print("① txt count:", len(files))

# ③ leak: 本次 section 不得含任何處方节头；既往 section 命中须全为锚案/更早块来源
PATS = ["針灸處方", "中藥處方", "處方："]
FIXED = "【本次處方排除确认】本次就診的診斷/針灸處方/中藥處方未包含于本输入。"
cur_hits, hist_hits = [], []
for fn in files:
    t = open(os.path.join(OUT, fn), encoding="utf-8").read()
    t = t.replace(FIXED, "")  # 排除固定确认行本身
    cur = t.split("【既往就診")[0]
    hist = "【既往就診" + t.split("【既往就診", 1)[1] if "【既往就診" in t else ""
    for p in PATS:
        if p in cur:
            cur_hits.append((fn, p))
        if p in hist:
            hist_hits.append((fn, p))
print("③ 本次节内含處方节头:", cur_hits if cur_hits else "NONE")
print("③ 既往节内含處方字样(应均为锚案既往处方,允许):", sorted(set(hist_hits)))

# ④ followup chain cases must have non-empty 既往
followup_no_hist = []
for cid, ch in chain_map.items():
    if ch.startswith("followup"):
        d = json.load(open(os.path.join(SRC, f"{cid}_symptoms_v2.json"), encoding="utf-8"))
        h = frag(d.get("既往就诊及治疗反馈"))
        if h == "原文未记录" or not h.strip():
            followup_no_hist.append(cid)
print("④ followup cases:", sum(1 for v in chain_map.values() if v.startswith("followup")),
      "| followup w/o 既往:", followup_no_hist if followup_no_hist else "NONE")

# ② random 10 verbatim
random.seed(42)
sample = random.sample(sorted(os.listdir(SRC)), 10)
bad = []
for fn in sample:
    cid = fn.replace("_symptoms_v2.json", "")
    d = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
    t = open(os.path.join(OUT, f"{cid}_hist.txt"), encoding="utf-8").read()
    for fld in FIELDS:
        s = frag(d.get(fld))
        for piece in s.split("\n"):
            if piece != "原文未记录" and piece.strip() and piece not in t:
                bad.append((cid, fld, piece[:30]))
    h = frag(d.get("既往就诊及治疗反馈"))
    if h != "原文未记录" and h.strip():
        for piece in h.split("\n"):
            if piece not in t:
                bad.append((cid, "既往", piece[:30]))
print("② sampled:", [f.replace('_symptoms_v2.json','') for f in sample])
print("② mismatches:", bad if bad else "NONE (10/10 OK)")

# stats
n_复诊 = n_首诊 = n_followup = n_anchor = n_unscored = n_hist = 0
mm = []
for fn in files:
    cid = fn.replace("_hist.txt", "")
    d = json.load(open(os.path.join(SRC, f"{cid}_symptoms_v2.json"), encoding="utf-8"))
    vt = d.get("visit_type", "")
    ch = chain_map[cid]
    h = frag(d.get("既往就诊及治疗反馈"))
    if vt.startswith("复诊"): n_复诊 += 1
    elif vt.startswith("首诊"): n_首诊 += 1
    if ch.startswith("followup"): n_followup += 1
    if ch.startswith("anchor"): n_anchor += 1
    if ch == "unscored": n_unscored += 1
    if h != "原文未记录" and h.strip(): n_hist += 1
    if ch == "first_visit" and vt.startswith("复诊"):
        mm.append((cid, vt, h[:50].replace("\n"," / ")))
print("stats: 阶段C复诊=%d 首诊=%d 其他=%d | 有既往=%d | followup链=%d anchor=%d unscored=%d"
      % (n_复诊, n_首诊, 93-n_复诊-n_首诊, n_hist, n_followup, n_anchor, n_unscored))
print("chain_map=first_visit 但阶段C判复诊:")
for m in mm: print("  ", m)

# reverse mismatch: chain followup but stageC says 首诊?
rev = []
for fn in files:
    cid = fn.replace("_hist.txt", "")
    d = json.load(open(os.path.join(SRC, f"{cid}_symptoms_v2.json"), encoding="utf-8"))
    if chain_map[cid].startswith("followup") and d.get("visit_type","").startswith("首诊"):
        rev.append(cid)
print("chain_map=followup 但阶段C判首诊:", rev if rev else "NONE")
