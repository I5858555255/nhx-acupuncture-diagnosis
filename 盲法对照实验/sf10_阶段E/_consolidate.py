# -*- coding: utf-8 -*-
"""整合93案数据，导出 _consolidated.json 与供人工归类的文本。"""
import json, pickle, os, sys, csv
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
sys.path.insert(0, os.path.join(BASE, "benchmark_v2"))
from normalize_acupoints import expand_composite_point

# 1) 判分明细 v10
rows = {}
order = []
with open(os.path.join(BASE, r"盲法93_v10\判分明细v10.csv"), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        cid = r['case_id']
        order.append(cid)
        def ii(k):
            v = r.get(k,'').strip()
            return int(v) if v else 0
        rows[cid] = {
            'chain_csv': r['chain'],
            'gold_n_csv': ii('gold穴数'),
            'v10_units': ii('v10单元数'),
            'v10_points': ii('v10点数'),
            'tp_n': ii('v10_tp'),
            'TP': [x for x in r['命中清单'].split(';') if x],
            'FN': [x for x in r['漏穴清单'].split(';') if x],
            'FP': [x for x in r['未命中清单'].split(';') if x],
            '备注': r.get('备注',''),
        }
print("明细行数:", len(order))

# 2) blind json
with open(os.path.join(BASE, r"盲法93_v10\_blind93v10_results.json"), encoding='utf-8') as f:
    blind = json.load(f)

# 每案: point -> list of (层,直接规则,依据,推断)
def build_pointmap(rec):
    pm = {}
    for m in rec.get('主穴记录', []):
        pts = expand_composite_point(m['穴'])
        for p in pts:
            pm.setdefault(p, []).append({'层': m.get('层',''), '直接规则': m.get('直接规则',''),
                                          '依据': m.get('依据',''), '推断': m.get('推断',''), '单元': m['穴']})
    return pm

# 3) gold
with open(os.path.join(BASE, r"benchmark_v2\_gold_results93v2.pkl"), 'rb') as f:
    gold = pickle.load(f)
gold_res = gold['results']

# 4) 组装清单 visit_type
visit = {}
with open(os.path.join(BASE, r"sf10_阶段D\组装清单.csv"), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        visit[r['case_id']] = {'visit_type': r['visit_type'], 'chain': r['chain'],
                               '有既往': r['有既往(Y/N)'], '既往说明': r['既往来源块说明']}

# 5) hist 明细
hist = {}
with open(os.path.join(BASE, r"sf10_阶段D\判分明细v10_hist.csv"), encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        hist[r['case_id']] = {'TP': [x for x in r['命中清单'].split(';') if x],
                              'FN': [x for x in r['漏穴清单'].split(';') if x],
                              'FP': [x for x in r['未命中清单'].split(';') if x]}

# 6) symptoms_v2
def load_sym(cid):
    p = os.path.join(BASE, rf"sf10_阶段C\symptoms_v2\{cid}_symptoms_v2.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)

cons = {}
for cid in order:
    rec = blind.get(cid, {})
    g = gold_res.get(cid, {})
    sv = load_sym(cid) or {}
    layermap = build_pointmap(rec)
    # 來診原因片段
    ly = sv.get('來診原因')
    if isinstance(ly, dict):
        cause = ly.get('片段','')
    else:
        cause = ly or ''
    missing = sv.get('缺失字段清单', [])
    cons[cid] = {
        **rows[cid],
        '主穴分层': rec.get('主穴分层', {}),
        'pointmap': layermap,
        'gold_members': g.get('gold_members', []),
        'gold_note': g.get('note', ''),
        'gold_raw': g.get('raw', ''),
        'gold_expand': g.get('expand_log', []),
        'visit_type': visit.get(cid, {}).get('visit_type', ''),
        'chain': visit.get(cid, {}).get('chain', ''),
        '有既往': visit.get(cid, {}).get('有既往', ''),
        '既往说明': visit.get(cid, {}).get('既往说明', ''),
        'n_missing': len(missing),
        'missing': missing,
        'cause': cause,
        'hist': hist.get(cid, {}),
        '推理要点': rec.get('推理要点', ''),
        '佐穴': rec.get('佐穴', []),
        '临床参考建议': rec.get('临床参考建议', {}),
    }

with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), 'w', encoding='utf-8') as f:
    json.dump(cons, f, ensure_ascii=False, indent=1)

# 打印供主诉归类的清单
print("\n=== 主诉归类清单 (case_id | visit | 缺字段 | 來診原因) ===")
for cid in order:
    c = cons[cid]
    print(f"{cid} [{c['visit_type']}|缺{c['n_missing']}] {c['cause'][:90]}")
