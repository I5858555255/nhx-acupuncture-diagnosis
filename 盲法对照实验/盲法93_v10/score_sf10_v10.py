# -*- coding: utf-8 -*-
"""score_sf10_v10.py — v10 (symptom-only) 统一评分，沿用 benchmark_v2 口径。
import normalize_acupoints + _gold_results93v2.pkl；ORDER=v140..v9 + v10。
输出：判分明细v10.csv / 判分汇总v10.json / 审计日志v10.json。"""
import json, os, sys, csv, statistics, pickle

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints

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
    "v10":  os.path.join(ROOT, "盲法93_v10", "_blind93v10_results.json"),
}
ORDER = ["v140","v2","v3","v4","v5","v6","v7","v8","v9","v10"]
CMP = ["v5","v6","v9","v10"]  # 横向对照四轮

with open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb") as f:
    g = pickle.load(f)
NEW_RESULTS=g["results"]; CASE_IDS=g["case_ids"]; SUMMARY=g["summary"]

BLIND = {lab: json.load(open(FILES[lab], encoding="utf-8")) for lab in ORDER}

def per_case_metrics(G, P):
    tp=len(P&G); fp=len(P-G); fn=len(G-P)
    recall=tp/len(G) if G else None
    prec=tp/len(P) if P else None
    f1=(2*prec*recall/(prec+recall)) if (prec and recall and (prec+recall)>0) else (0.0 if tp==0 else None)
    jac=tp/(tp+fp+fn) if (tp+fp+fn)>0 else 0.0
    return dict(tp=tp,fp=fp,fn=fn,recall=recall,prec=prec,f1=f1,jac=jac)

PER={}
for cid in CASE_IDS:
    G=set(NEW_RESULTS[cid]['gold_members'])
    d={}
    for lab in ORDER:
        rec=BLIND[lab].get(cid)
        if rec is None: d[lab]=None; continue
        Pm=normalize_acupoints(rec.get('主穴',[]))
        Pa=normalize_acupoints(rec.get('主穴',[])+rec.get('佐穴',[]))
        d[lab]=dict(units_main=len(rec.get('主穴',[])),points_main=len(Pm),points_all=len(Pa),
                    main=per_case_metrics(G,Pm),all=per_case_metrics(G,Pa),
                    pred_main=sorted(Pm),layers=rec.get('主穴分层',{}))
    PER[cid]=dict(gold=sorted(G),gc=len(G),new=d,chain=SUMMARY['chain_map'].get(cid,'first_visit'),note=NEW_RESULTS[cid]['note'])

SCORED=[c for c in CASE_IDS if PER[c]['gc']>0]
UNSCORED=[c for c in CASE_IDS if PER[c]['gc']==0]

def macro(lab,subset,metric,cids=None):
    cids=cids or SCORED; v=[]
    for c in cids:
        dd=PER[c]['new'].get(lab)
        if dd is None: continue
        x=dd[subset][metric]
        if x is not None: v.append(x)
    return statistics.mean(v) if v else None
def micro(lab,subset,metric,cids=None):
    cids=cids or SCORED; tp=fp=fn=0
    for c in cids:
        dd=PER[c]['new'].get(lab)
        if dd is None: continue
        m=dd[subset]; tp+=m['tp'];fp+=m['fp'];fn+=m['fn']
    if metric=='recall': return tp/(tp+fn) if (tp+fn) else None
    if metric=='prec': return tp/(tp+fp) if (tp+fp) else None
    if metric=='f1':
        r=tp/(tp+fn) if (tp+fn) else 0; p=tp/(tp+fp) if (tp+fp) else 0
        return 2*p*r/(p+r) if (p+r) else 0.0
    if metric=='jac': return tp/(tp+fp+fn) if (tp+fp+fn) else 0.0

def dist(vals):
    b={'100%':0,'80-99%':0,'60-79%':0,'40-59%':0,'<40%':0}
    for x in vals:
        if x is None: continue
        if x>=0.999:b['100%']+=1
        elif x>=0.8:b['80-99%']+=1
        elif x>=0.6:b['60-79%']+=1
        elif x>=0.4:b['40-59%']+=1
        else:b['<40%']+=1
    return b

ro=lambda x:None if x is None else round(x,4)

# ---- 汇总 ----
S=dict(n_cases=len(CASE_IDS),n_scorable=len(SCORED),n_unscored=len(UNSCORED),
       unscored={c:PER[c]['note'] for c in UNSCORED})
for lab in CMP:
    ms={}
    for subset in ('main','all'):
        ms[subset]=dict(
            macro=dict(recall=ro(macro(lab,subset,'recall')),prec=ro(macro(lab,subset,'prec')),
                       f1=ro(macro(lab,subset,'f1')),jac=ro(macro(lab,subset,'jac'))),
            micro=dict(recall=ro(micro(lab,subset,'recall')),prec=ro(micro(lab,subset,'prec')),
                       f1=ro(micro(lab,subset,'f1')),jac=ro(micro(lab,subset,'jac'))))
    units=[PER[c]['new'][lab]['units_main'] for c in SCORED if PER[c]['new'].get(lab)]
    points=[PER[c]['new'][lab]['points_main'] for c in SCORED if PER[c]['new'].get(lab)]
    S[lab]=dict(metrics=ms,mean_units_main=round(statistics.mean(units),3) if units else None,
                mean_points_main=round(statistics.mean(points),3) if points else None,
                sum_tp_main=sum(PER[c]['new'][lab]['main']['tp'] for c in SCORED if PER[c]['new'].get(lab)))

S['dist_v10_recall_main']=dist([PER[c]['new']['v10']['main']['recall'] for c in SCORED])
S['dist_v10_jac_main']=dist([PER[c]['new']['v10']['main']['jac'] for c in SCORED])
# 分布对照
for lab in ['v5','v6','v9','v10']:
    S[f'dist_{lab}_recall_main']=dist([PER[c]['new'][lab]['main']['recall'] for c in SCORED])

# 层间 v10
LAYERS=['对症','俞募背俞','八脉交会','特效奇穴']
def layer_stats(lab):
    out={}
    for L in LAYERS:
        u=0;hc=0
        for c in SCORED:
            lu=PER[c]['new'][lab]['layers'].get(L,[])
            u+=len(lu)
            p=normalize_acupoints(lu)
            if p&set(NEW_RESULTS[c]['gold_members']):hc+=1
        out[L]=dict(出单元=u,命中案=hc)
    return out
S['层_v10']=layer_stats('v10'); S['层_v9']=layer_stats('v9')

# 链分层 v9 vs v10
follow=[c for c in SCORED if PER[c]['chain'].startswith('followup')]
anchor=[c for c in SCORED if PER[c]['chain'] in ('first_visit',) or PER[c]['chain'].startswith('anchor')]
S['链分层']={}
for lab in ['v9','v10']:
    S['链分层'][lab]=dict(
        followup=dict(n=len(follow),macro_recall=ro(macro(lab,'main','recall',follow)),macro_prec=ro(macro(lab,'main','prec',follow))),
        anchor_first=dict(n=len(anchor),macro_recall=ro(macro(lab,'main','recall',anchor)),macro_prec=ro(macro(lab,'main','prec',anchor))))

# 零命中
S['v10零命中']=[c for c in SCORED if PER[c]['new']['v10']['main']['tp']==0]
S['v9零命中']=[c for c in SCORED if PER[c]['new']['v9']['main']['tp']==0]
S['v10满分']=[c for c in SCORED if PER[c]['new']['v10']['main']['recall'] and PER[c]['new']['v10']['main']['recall']>=0.999]

# 逐案 v9 vs v10
pc=[]
for c in SCORED:
    a=PER[c]['new']['v9']['main']; b=PER[c]['new']['v10']['main']
    pc.append(dict(case_id=c,v9_recall=ro(a['recall']),v10_recall=ro(b['recall']),
                   v9_f1=ro(a['f1']),v10_f1=ro(b['f1']),dv_f1=ro((b['f1'] or 0)-(a['f1'] or 0))))
S['逐案_v9_v10']=sorted(pc,key=lambda x:abs(x['dv_f1'] or 0),reverse=True)
S['显著_absdvf1>=0.2']=[p for p in S['逐案_v9_v10'] if abs(p['dv_f1'] or 0)>=0.2]

# 执行方差 v10 vs v9
diff=[];same=0;du=0
for c in CASE_IDS:
    a=set(BLIND['v9'][c].get('主穴',[]));b=set(BLIND['v10'][c].get('主穴',[]))
    if a==b:same+=1
    else:diff.append(dict(case_id=c,v9=sorted(a^b) and sorted(a-b),v10=sorted(b-a)));du+=len(a^b)
S['执行方差_v10_vs_v9']=dict(一致案=same,差异案=len(diff),差异单元总数=du,差异清单=diff)

# 重点案
for c in ['107_01','156_05','311_01','60_01','340_01','201_01','207_01','318_01','216_04']:
    n=PER[c]['new']['v10']
    S.setdefault('重点',{})[c]=dict(gold=PER[c]['gold'],recall=ro(n['main']['recall']),prec=ro(n['main']['prec']),tp=n['main']['tp'],命中=n['pred_main'])

# ---- 明细 CSV ----
header=['case_id','chain','gold穴数','v10单元数','v10点数','v10_tp','v10_recall_main','v10_prec_main','v10_f1_main','v10_jac_main','命中清单','漏穴清单','未命中清单','备注']
rows=[]
for c in SCORED:
    n=PER[c]['new']['v10'];G=set(PER[c]['gold']);P=set(n['pred_main'])
    rows.append([c,PER[c]['chain'],PER[c]['gc'],n['units_main'],n['points_main'],n['main']['tp'],
        ro(n['main']['recall']),ro(n['main']['prec']),ro(n['main']['f1']),ro(n['main']['jac']),
        ';'.join(sorted(P&G)),';'.join(sorted(G-P)),';'.join(sorted(P-G)),PER[c]['note']])
for c in UNSCORED:
    rows.append([c,PER[c]['chain'],0,'','','','','','','','','','',PER[c]['note']])
csv.writer(open(os.path.join(HERE,'判分明细v10.csv'),'w',newline='',encoding='utf-8-sig')).writerows([header]+rows)
json.dump(S,open(os.path.join(HERE,'判分汇总v10.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

# ---- 审计日志（含主穴记录抽检）----
audit={}
for c in SCORED:
    rec=BLIND['v10'][c]
    audit[c]=dict(gold=PER[c]['gold'],gold_count=PER[c]['gc'],chain=PER[c]['chain'],
                   main_units=rec.get('主穴',[]),main_points=PER[c]['new']['v10']['pred_main'],
                   主穴记录=rec.get('主穴记录',[]))
json.dump(audit,open(os.path.join(HERE,'审计日志v10.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

# ---- 控制台 ----
print('=== v5/v6/v9/v10 宏 main/all ===')
for lab in CMP:
    m=S[lab]['metrics']
    print(f"{lab} main: R={m['main']['macro']['recall']} P={m['main']['macro']['prec']} F1={m['main']['macro']['f1']} Jac={m['main']['macro']['jac']} | units均={S[lab]['mean_units_main']} 点均={S[lab]['mean_points_main']} tp={S[lab]['sum_tp_main']}")
    print(f"{lab} all : R={m['all']['macro']['recall']} P={m['all']['macro']['prec']} F1={m['all']['macro']['f1']} Jac={m['all']['macro']['jac']}")
print('分布 v10 recall:',S['dist_v10_recall_main'])
print('零命中 v10:',S['v10零命中'],'v9:',S['v9零命中'])
print('执行方差 v10vs v9:',S['执行方差_v10_vs_v9']['一致案'],S['执行方差_v10_vs_v9']['差异案'],S['执行方差_v10_vs_v9']['差异单元总数'])
print('显著|Δf1|>=0.2:',json.dumps(S['显著_absdvf1>=0.2'],ensure_ascii=False))
