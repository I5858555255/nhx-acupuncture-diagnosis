# -*- coding: utf-8 -*-
"""verify_benchmark_v2.py — 验收自验（BENCHMARK-AUDIT-01 工作项 B 验收）

1. 点级 precision 不可能超过 100%：扫描全部案/轮次
2. 宏/微平均独立复算：与判分汇总v2.json 交叉核对
3. 关键案抽查：107_01(满分)、60_01、8_01(膝五针)、340_01(单操作耳穴)
4. 复诊链分层复算
"""
import json, os, sys, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from normalize_acupoints import normalize_acupoints

with open(os.path.join(HERE, '_gold_results93v2.pkl'), 'rb') as f:
    import pickle
    GOLD = pickle.load(f)
RESULTS = GOLD['results']; CASE_IDS = GOLD['case_ids']; SUMMARY = GOLD['summary']

ROOT = os.path.dirname(HERE)  # 盲法对照实验目录（由脚本位置推导）
import json as _j
BLIND = {lab: _j.load(open(os.path.join(ROOT, d, f), encoding='utf-8'))
         for lab, d, f in [
             ("v140", "盲法140", "_blind140_results.json"),
             ("v2", "盲法93", "_blind93_results.json"),
             ("v3", "盲法93_v3", "_blind93v3_results.json"),
             ("v4", "盲法93_v4", "_blind93v4_results.json"),
             ("v5", "盲法93_v5", "_blind93v5_results.json"),
             ("v6", "盲法93_v6", "_blind93v6_results.json"),
             ("v7", "盲法93_v7", "_blind93v7_results.json"),
             ("v8", "盲法93_v8", "_blind93v8_results.json"),
             ("v9", "盲法93_v9", "_blind93v9_results.json"),
         ]}

SCORED = [c for c in CASE_IDS if len(RESULTS[c]['gold_members']) > 0]

# ---- 1. 精确率 <= 100% 扫描 ----
viol = []
for c in SCORED:
    G = set(RESULTS[c]['gold_members'])
    for lab in BLIND:
        rec = BLIND[lab].get(c)
        if not rec:
            continue
        Pm = normalize_acupoints(rec.get('主穴', []))
        Pa = normalize_acupoints(rec.get('主穴', []) + rec.get('佐穴', []))
        if Pm and len(Pm & G) / len(Pm) > 1.0 + 1e-9:
            viol.append((c, lab, 'main', len(Pm & G), len(Pm)))
        if Pa and len(Pa & G) / len(Pa) > 1.0 + 1e-9:
            viol.append((c, lab, 'all', len(Pa & G), len(Pa)))
print('1) 精确率>100% 违规案数:', len(viol), viol[:5])

# ---- 2. 宏/微平均独立复算（v9）----
def metrics(G, P):
    tp = len(P & G); fp = len(P - G); fn = len(G - P)
    r = tp / len(G) if G else None
    p = tp / len(P) if P else None
    f1 = (2 * p * r / (p + r)) if (p and r and p + r > 0) else (0.0 if tp == 0 else None)
    j = tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=r, prec=p, f1=f1, jac=j)

macro_r, macro_p, micro_tp, micro_pn, micro_gn, micro_fp = [], [], 0, 0, 0, 0
for c in SCORED:
    G = set(RESULTS[c]['gold_members'])
    Pm = normalize_acupoints(BLIND['v9'][c].get('主穴', []))
    m = metrics(G, Pm)
    if m['recall'] is not None: macro_r.append(m['recall'])
    if m['prec'] is not None: macro_p.append(m['prec'])
    micro_tp += m['tp']; micro_pn += len(Pm); micro_gn += len(G); micro_fp += m['fp']
print('2) v9 宏 recall 独立复算:', round(statistics.mean(macro_r), 4), ' 宏 prec:', round(statistics.mean(macro_p), 4))
print('   v9 微 recall:', round(micro_tp / micro_gn, 4), ' 微 prec:', round(micro_tp / micro_pn, 4))

# ---- 3. 关键案抽查 ----
print('3) 关键案抽查:')
for c in ['107_01', '60_01', '8_01', '340_01', '201_01']:
    G = set(RESULTS[c]['gold_members'])
    Pm = normalize_acupoints(BLIND['v9'][c].get('主穴', []))
    m = metrics(G, Pm)
    print(f"   {c}: gold={len(G)} 命中={sorted(Pm & G)} recall={m['recall']:.3f} prec={m['prec']:.3f}")

# ---- 4. 复诊链分层复算 ----
follow = [c for c in SCORED if SUMMARY['chain_map'].get(c, '').startswith('followup')]
anchor_first = [c for c in SCORED if SUMMARY['chain_map'].get(c, 'first_visit') == 'first_visit' or SUMMARY['chain_map'].get(c, '').startswith('anchor')]
def macro_recall_of(cids):
    v = []
    for c in cids:
        G = set(RESULTS[c]['gold_members'])
        Pm = normalize_acupoints(BLIND['v9'][c].get('主穴', []))
        r = len(Pm & G) / len(G)
        v.append(r)
    return round(statistics.mean(v), 4)
print('4) 分层复算: followup n=', len(follow), 'recall=', macro_recall_of(follow),
      ' anchor_first n=', len(anchor_first), 'recall=', macro_recall_of(anchor_first))

# ---- 与判分汇总v2.json 核对 ----
S = json.load(open(os.path.join(HERE, '判分汇总v2.json'), encoding='utf-8'))
print('5) 与判分汇总v2.json 核对:')
print('   汇总v9 macro recall:', S['v9']['metrics']['main']['macro']['recall'],
      ' prec:', S['v9']['metrics']['main']['macro']['prec'])
print('   独立复算 macro recall:', round(statistics.mean(macro_r), 4),
      ' prec:', round(statistics.mean(macro_p), 4))
ok1 = abs(S['v9']['metrics']['main']['macro']['recall'] - statistics.mean(macro_r)) < 1e-3
ok2 = abs(S['v9']['metrics']['main']['macro']['prec'] - statistics.mean(macro_p)) < 1e-3
ok3 = abs(S['v9']['metrics']['main']['micro']['recall'] - micro_tp / micro_gn) < 1e-3
ok4 = abs(S['v9']['metrics']['main']['micro']['prec'] - micro_tp / micro_pn) < 1e-3
print('   核对:', 'PASS' if (ok1 and ok2 and ok3 and ok4) else 'FAIL',
      '(宏r, 宏p, 微r, 微p =', ok1, ok2, ok3, ok4, ')')
