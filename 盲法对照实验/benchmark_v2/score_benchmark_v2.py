# -*- coding: utf-8 -*-
"""score_benchmark_v2.py — 统一评分器（BENCHMARK-AUDIT-01 工作项 B）

相对旧版 score93v9.py 的变更：
1. 所有轮次与 gold 共用同一 normalize_acupoints（无版本分支）
2. 指标改为点级 precision / recall / F1 / Jaccard，宏平均与微平均分别报告
3. 每案输出 TP/FP/FN、预测点集、gold 点集、归一化审计日志
4. 单元数（原始输出单元）与点数（规范化穴位）分开报告，禁止混用
5. 复诊链分层（锚案/首诊 vs 复诊跟随）单独汇总
6. 精确率不可能超过 100%（分子分母同粒度）

同时内嵌"旧口径复算"（旧 gold pkl + 旧 expand_pre/expand_post + 旧公式），
用于核对旧判分汇总.json 并生成新旧差异归因。
"""
import json, os, sys, csv, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from normalize_acupoints import normalize_acupoints

ROOT = os.path.dirname(HERE)  # 盲法对照实验目录（由脚本位置推导）
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
ORDER = ["v140", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9"]

gold_new = pickle_load = None
import pickle
with open(os.path.join(HERE, "_gold_results93v2.pkl"), "rb") as f:
    gold_new = pickle.load(f)
NEW_RESULTS = gold_new["results"]; CASE_IDS = gold_new["case_ids"]; SUMMARY = gold_new["summary"]

# ---- 旧 gold（用于旧口径复算与差异归因）----
OLD_PKL = os.path.join(ROOT, "盲法93_v9", "_gold_results93v9.pkl")
with open(OLD_PKL, "rb") as f:
    gold_old = pickle.load(f)
OLD_RESULTS = gold_old["results"]

BLIND = {}
for lab in ORDER:
    with open(FILES[lab], encoding="utf-8") as f:
        BLIND[lab] = json.load(f)

# ---- 旧预测归一化（仅用于旧口径复算，非新评分路径）----
def expand_pre(u):
    u = u.strip()
    u = u.replace('天应隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u = u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u = u.replace('膀胱募','中极')
    if u == '心脏点': return {'耳心点'}
    if u == '耳针埋心的压痛点': return {'耳心点'}
    if '透' in u:
        a, b = u.split('透', 1); return {a, b}
    if '+' in u:
        return set(x.strip() for x in u.split('+'))
    return {u}

EAR = {'耳针肾膀胱区压痛点':'耳肾点','耳针肾点':'耳肾点','耳针埋心的压痛点':'耳心点','耳针心的压痛点':'耳心点',
       '耳胆石点':'耳胆点','耳针胆点':'耳胆点','埋耳针<胆>':'耳胆点','耳针埋肝点':'耳肝点','耳穴肝点':'耳肝点'}
def expand_post(u):
    u = u.strip()
    u = u.replace('天应隔姜灸','天应').replace('天應隔姜灸','天应').replace('灸关元','关元').replace('灸中脘','中脘').replace('灸天枢','天枢')
    u = u.replace('上星米粒灸','上星').replace('耳尖放血','耳尖').replace('委中放血','委中').replace('少商放血','少商').replace('商阳放血','商阳')
    u = u.replace('膀胱募','中极')
    if u in EAR: return {EAR[u]}
    if u == '心脏点': return {'耳心点'}
    if '透' in u:
        a, b = u.split('透', 1); return {a, b}
    if '+' in u:
        return set(x.strip() for x in u.split('+'))
    return {u}

OLD_EX = {"v140": expand_pre, "v2": expand_pre, "v3": expand_post, "v4": expand_post,
          "v5": expand_post, "v6": expand_post, "v7": expand_post, "v8": expand_post, "v9": expand_post}


def per_case_metrics(gold_set, pred_set):
    """点级指标。gold_set/pred_set 为规范穴集。"""
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    recall = tp / len(gold_set) if gold_set else None
    prec = tp / len(pred_set) if pred_set else None
    if prec is not None and recall is not None and (prec + recall) > 0:
        f1 = 2 * prec * recall / (prec + recall)
    else:
        f1 = 0.0 if (tp == 0) else None
    jac = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=recall, prec=prec, f1=f1, jac=jac)


def score_case(cid):
    """对一案计算新口径全部轮次指标 + 旧口径复算。"""
    G = set(NEW_RESULTS[cid]['gold_members'])
    gc = len(G)
    d = {}
    for lab in ORDER:
        rec = BLIND[lab].get(cid)
        if rec is None:
            d[lab] = None
            continue
        main_units = rec.get('主穴', [])
        aux_units = rec.get('佐穴', [])
        Pm = normalize_acupoints(main_units)
        Pa = normalize_acupoints(main_units + aux_units)
        m = per_case_metrics(G, Pm)
        a = per_case_metrics(G, Pa)
        d[lab] = dict(
            units_main=len(main_units), units_aux=len(aux_units),
            points_main=len(Pm), points_all=len(Pa),
            main=m, all=a,
            pred_main=sorted(Pm), pred_all=sorted(Pa),
            layers=rec.get('主穴分层', {}),
        )
    # ---- 旧口径复算（仅 v9 用于差异归因；gold 用旧 pkl）----
    G_old = set(OLD_RESULTS[cid]['gold_members']); gc_old = len(G_old)
    old = {}
    for lab in ORDER:
        rec = BLIND[lab].get(cid)
        if rec is None:
            old[lab] = None
            continue
        mp = set(); ap = set()
        for u in rec.get('主穴', []): mp |= OLD_EX[lab](u)
        for u in rec.get('佐穴', []): ap |= OLD_EX[lab](u)
        hm = mp & G_old; hma = (mp | ap) & G_old
        if gc_old > 0:
            old[lab] = dict(r_main=len(hm) / gc_old, r_ma=len(hma) / gc_old,
                            prec=len(hm) / len(rec.get('主穴', [])) if rec.get('主穴') else 0.0,
                            mc=len(rec.get('主穴', [])), hm=len(hm), gc_old=gc_old)
        else:
            old[lab] = dict(r_main=None, r_ma=None, prec=None, mc=len(rec.get('主穴', [])), hm=0, gc_old=gc_old)
    return dict(cid=cid, gold=sorted(G), gold_count=gc, gold_old_count=gc_old, new=d, old=old,
                chain=SUMMARY['chain_map'].get(cid, 'first_visit'),
                note=NEW_RESULTS[cid]['note'])


PER = {c: score_case(c) for c in CASE_IDS}
SCORED = [c for c in CASE_IDS if PER[c]['gold_count'] > 0]
UNSCORED = [c for c in CASE_IDS if PER[c]['gold_count'] == 0]


def macro(key, cids=None, subset='main', metric='recall'):
    """宏平均：逐案先算再平均。subset: main/all。metric: recall/prec/f1/jac。"""
    cids = cids or SCORED
    vals = []
    for c in cids:
        d = PER[c]['new']
        if d.get(key) is None:
            continue
        v = d[key][subset][metric]
        if v is not None:
            vals.append(v)
    return statistics.mean(vals) if vals else None


def micro(key, cids=None, subset='main', metric='recall'):
    """微平均：全案 TP/分母 求和再算。"""
    cids = cids or SCORED
    tp = fp = fn = 0
    for c in cids:
        d = PER[c]['new'].get(key)
        if d is None:
            continue
        m = d[subset]
        tp += m['tp']; fp += m['fp']; fn += m['fn']
    if metric == 'recall':
        return tp / (tp + fn) if (tp + fn) else None
    if metric == 'prec':
        return tp / (tp + fp) if (tp + fp) else None
    if metric == 'f1':
        r = tp / (tp + fn) if (tp + fn) else 0
        p = tp / (tp + fp) if (tp + fp) else 0
        return 2 * p * r / (p + r) if (p + r) else 0.0
    if metric == 'jac':
        return tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    return None


def dist(vals):
    b = {'100%': 0, '80-99%': 0, '60-79%': 0, '40-59%': 0, '<40%': 0}
    for x in vals:
        if x is None:
            continue
        if x >= 0.999: b['100%'] += 1
        elif x >= 0.8: b['80-99%'] += 1
        elif x >= 0.6: b['60-79%'] += 1
        elif x >= 0.4: b['40-59%'] += 1
        else: b['<40%'] += 1
    return b


LAYERS = ['对症', '俞募背俞', '八脉交会', '特效奇穴']

def layer_stats(lab):
    out = {}
    for L in LAYERS:
        u = 0; hc = 0
        for c in SCORED:
            d = PER[c]['new'].get(lab)
            if d is None:
                continue
            lu = d['layers'].get(L, [])
            u += len(lu)
            p = normalize_acupoints(lu)
            if p & set(NEW_RESULTS[c]['gold_members']):
                hc += 1
        out[L] = dict(出单元=u, 命中案=hc)
    return out


def round_or(x, nd=4):
    return None if x is None else round(x, nd)


def build_summary():
    S = dict(n_cases=len(CASE_IDS), n_scorable=len(SCORED), n_unscored=len(UNSCORED),
             unscored={c: PER[c]['note'] for c in UNSCORED})
    # 每轮：宏/微、点/单元
    for lab in ORDER:
        ms = dict()
        for subset in ('main', 'all'):
            ms[subset] = dict(
                macro=dict(recall=round_or(macro(lab, subset=subset, metric='recall')),
                           prec=round_or(macro(lab, subset=subset, metric='prec')),
                           f1=round_or(macro(lab, subset=subset, metric='f1')),
                           jac=round_or(macro(lab, subset=subset, metric='jac'))),
                micro=dict(recall=round_or(micro(lab, subset=subset, metric='recall')),
                           prec=round_or(micro(lab, subset=subset, metric='prec')),
                           f1=round_or(micro(lab, subset=subset, metric='f1')),
                           jac=round_or(micro(lab, subset=subset, metric='jac'))),
            )
        units = [PER[c]['new'][lab]['units_main'] for c in SCORED if PER[c]['new'].get(lab)]
        points = [PER[c]['new'][lab]['points_main'] for c in SCORED if PER[c]['new'].get(lab)]
        S[lab] = dict(
            metrics=ms,
            mean_units_main=statistics.mean(units) if units else None,
            mean_points_main=statistics.mean(points) if points else None,
            sum_points_main=sum(points), sum_points_all=sum(PER[c]['new'][lab]['points_all'] for c in SCORED if PER[c]['new'].get(lab)),
            sum_tp_main=sum(PER[c]['new'][lab]['main']['tp'] for c in SCORED if PER[c]['new'].get(lab)),
            sum_tp_all=sum(PER[c]['new'][lab]['all']['tp'] for c in SCORED if PER[c]['new'].get(lab)),
        )
    # 分布（v9 recall_main 宏）
    S['dist_v9_recall_main'] = dist([PER[c]['new']['v9']['main']['recall'] for c in SCORED])
    S['dist_v9_jac_main'] = dist([PER[c]['new']['v9']['main']['jac'] for c in SCORED])
    S['层_v9'] = layer_stats('v9')
    # 复诊链分层（v9 recall_main 宏）
    follow = [c for c in SCORED if PER[c]['chain'].startswith('followup')]
    anchor_first = [c for c in SCORED if PER[c]['chain'] in ('first_visit',) or PER[c]['chain'].startswith('anchor')]
    S['分层_v9'] = dict(
        followup=dict(n=len(follow), macro_recall=round_or(macro('v9', follow, 'main', 'recall')),
                      macro_prec=round_or(macro('v9', follow, 'main', 'prec'))),
        anchor_first=dict(n=len(anchor_first), macro_recall=round_or(macro('v9', anchor_first, 'main', 'recall')),
                          macro_prec=round_or(macro('v9', anchor_first, 'main', 'prec'))),
        chain_names=sorted({PER[c]['chain'] for c in SCORED}),
    )
    # 零命中（v9）
    S['v9零命中_recall'] = [c for c in SCORED if PER[c]['new']['v9']['main']['tp'] == 0]
    # 新旧差异（v9）：旧 r_main vs 新 recall_main；旧 prec vs 新 prec_main
    diffs = []
    for c in SCORED:
        o = PER[c]['old']['v9']; n = PER[c]['new']['v9']
        diffs.append(dict(case_id=c, old_r_main=round_or(o['r_main']), new_recall=round_or(n['main']['recall']),
                          old_prec=round_or(o['prec']), new_prec=round_or(n['main']['prec']),
                          old_gc=o['gc_old'], new_gc=PER[c]['gold_count']))
    S['新旧差异_v9'] = diffs
    S['旧口径汇总_v9'] = dict(
        macro_r_main=statistics.mean([d['old_r_main'] for d in diffs if d['old_r_main'] is not None]),
        macro_new_recall=statistics.mean([d['new_recall'] for d in diffs if d['new_recall'] is not None]),
        sum_hm=sum(PER[c]['old']['v9']['hm'] for c in SCORED),
        sum_mc_units=sum(PER[c]['old']['v9']['mc'] for c in SCORED),
        sum_new_points=sum(PER[c]['new']['v9']['points_main'] for c in SCORED),
        sum_new_tp=sum(PER[c]['new']['v9']['main']['tp'] for c in SCORED),
    )
    # 重点案
    for c in ['107_01', '156_05', '311_01', '60_01', '340_01', '201_01', '207_01', '318_01', '216_04']:
        n = PER[c]['new']['v9']
        S.setdefault('重点', {})[c] = dict(gold=PER[c]['gold'], recall=round_or(n['main']['recall']),
                                           prec=round_or(n['main']['prec']), tp=n['main']['tp'],
                                           命中=n['pred_main'])
    return S


S = build_summary()

# ---- 逐案明细 CSV ----
header = ['case_id', 'chain', 'gold穴数', '新gold穴数', 'v9单元数', 'v9点数',
          'v9_tp', 'v9_recall_main', 'v9_prec_main', 'v9_f1_main', 'v9_jac_main',
          '旧gc', '旧r_main', '旧prec', '新recall_diff', '命中清单', '备注']
rows = []
for c in SCORED:
    n = PER[c]['new']['v9']; o = PER[c]['old']['v9']
    rows.append([c, PER[c]['chain'], PER[c]['gold_count'], PER[c]['gold_count'], n['units_main'], n['points_main'],
                 n['main']['tp'], f"{n['main']['recall']:.4f}" if n['main']['recall'] is not None else '',
                 f"{n['main']['prec']:.4f}" if n['main']['prec'] is not None else '',
                 f"{n['main']['f1']:.4f}", f"{n['main']['jac']:.4f}",
                 o['gc_old'], f"{o['r_main']:.4f}" if o['r_main'] is not None else '',
                 f"{o['prec']:.4f}" if o['prec'] is not None else '',
                 f"{n['main']['recall'] - o['r_main']:+.4f}" if o['r_main'] is not None else '',
                 ';'.join(n['pred_main']), PER[c]['note']])
for c in UNSCORED:
    rows.append([c, PER[c]['chain'], 0, 0, '', '', '', '', '', '', '', '', '', '', '', '', PER[c]['note']])
csv.writer(open(os.path.join(HERE, '判分明细v2.csv'), 'w', newline='', encoding='utf-8-sig')).writerows([header] + rows)

with open(os.path.join(HERE, '判分汇总v2.json'), 'w', encoding='utf-8') as f:
    json.dump(S, f, ensure_ascii=False, indent=2)

# ---- 审计日志（per-case 归一化展开明细）----
audit = {}
for c in SCORED:
    rec = BLIND['v9'][c]
    audit[c] = dict(
        gold=PER[c]['gold'], gold_count=PER[c]['gold_count'],
        main_units=rec.get('主穴', []), main_points=PER[c]['new']['v9']['pred_main'],
        aux_units=rec.get('佐穴', []), all_points=PER[c]['new']['v9']['pred_all'],
        chain=PER[c]['chain'], note=PER[c]['note'])
with open(os.path.join(HERE, '审计日志v2.json'), 'w', encoding='utf-8') as f:
    json.dump(audit, f, ensure_ascii=False, indent=2)

# ---- 控制台输出 ----
print('=== 统一评分器 v2（新口径，宏平均）===')
for lab in ORDER:
    m = S[lab]['metrics']['main']['macro']
    print(f"{lab}: recall={m['recall']} prec={m['prec']} f1={m['f1']} jac={m['jac']} "
          f"点数均={S[lab]['mean_points_main']:.2f} 单元均={S[lab]['mean_units_main']:.2f}")
print('--- 主+佐（宏） ---')
for lab in ORDER:
    m = S[lab]['metrics']['all']['macro']
    print(f"{lab}: recall={m['recall']} prec={m['prec']} f1={m['f1']} jac={m['jac']}")
print('--- 微平均 v9 ---')
for subset in ('main', 'all'):
    m = S['v9']['metrics'][subset]['micro']
    print(f"v9 {subset}: recall={m['recall']} prec={m['prec']} f1={m['f1']} jac={m['jac']}")
print('分布 v9 recall_main:', S['dist_v9_recall_main'])
print('分布 v9 jac_main:', S['dist_v9_jac_main'])
print('零命中 v9:', S['v9零命中_recall'])
print('分层 v9:', S['分层_v9'])
print('旧口径 v9: r_main宏=', round(S['旧口径汇总_v9']['macro_r_main'], 4), ' sum_hm/sum_mc=', S['旧口径汇总_v9']['sum_hm'], '/', S['旧口径汇总_v9']['sum_mc_units'])
print('新口径 v9: recall宏=', round(S['旧口径汇总_v9']['macro_new_recall'], 4), ' sum_tp/sum_points=', S['旧口径汇总_v9']['sum_new_tp'], '/', S['旧口径汇总_v9']['sum_new_points'])
