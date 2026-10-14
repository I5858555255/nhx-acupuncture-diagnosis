# -*- coding: utf-8 -*-
"""score_sf10_v11.py — v11 统一评分（benchmark_v2 口径）。
ORDER/CMP=[v5,v6,v9,v10,v11]；86全量 / 64核心集 / visit分层 / chain分层。"""
import json, os, sys, csv, statistics, pickle, hashlib

ROOT=r'D:\projectAGI\nhx\盲法对照实验'
BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'盲法93_v11')
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints

FILES={
 'v5':os.path.join(ROOT,'盲法93_v5','_blind93v5_results.json'),
 'v6':os.path.join(ROOT,'盲法93_v6','_blind93v6_results.json'),
 'v9':os.path.join(ROOT,'盲法93_v9','_blind93v9_results.json'),
 'v10':os.path.join(ROOT,'盲法93_v10','_blind93v10_results.json'),
 'v11':os.path.join(HERE,'_blind93v11_results.json'),
}
CMP=['v5','v6','v9','v10','v11']
BLIND={lab:json.load(open(fp,encoding='utf-8')) for lab,fp in FILES.items()}

g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']

# 排除清单 22 案
EXCLUDE=set()
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')):
    EXCLUDE.add(r['case_id'])
# visit_type 前缀分桶
VT={}
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段D','组装清单.csv'),encoding='utf-8-sig')):
    v=r['visit_type']
    bucket='复诊' if v.startswith('复诊') else ('首诊' if v.startswith('首诊') else '其他')
    VT[r['case_id']]=bucket

def pm(G,P):
    tp=len(P&G);fp=len(P-G);fn=len(G-P)
    recall=tp/len(G) if G else None
    prec=tp/len(P) if P else None
    f1=(2*prec*recall/(prec+recall)) if (prec and recall and (prec+recall)>0) else (0.0 if tp==0 else None)
    jac=tp/(tp+fp+fn) if (tp+fp+fn)>0 else 0.0
    return dict(tp=tp,fp=fp,fn=fn,recall=recall,prec=prec,f1=f1,jac=jac)

PER={}
for cid in CASE_IDS:
    G=set(NEW[cid]['gold_members'])
    d={}
    for lab in CMP:
        rec=BLIND[lab].get(cid)
        if rec is None: d[lab]=None; continue
        Pm=normalize_acupoints(rec.get('主穴',[])); Pa=normalize_acupoints(rec.get('主穴',[])+rec.get('佐穴',[]))
        d[lab]=dict(units_main=len(rec.get('主穴',[])),points_main=len(Pm),points_all=len(Pa),
                    main=pm(G,Pm),all=pm(G,Pa),pred_main=sorted(Pm),main_units=rec.get('主穴',[]))
    PER[cid]=dict(G=sorted(G),gc=len(G),new=d,chain=SUMMARY['chain_map'].get(cid,'first_visit'),
                  vt=VT.get(cid,''),note=NEW[cid]['note'],core=cid not in EXCLUDE)

SCORED=[c for c in CASE_IDS if PER[c]['gc']>0]
UNSCORED=[c for c in CASE_IDS if PER[c]['gc']==0]
CORE=[c for c in SCORED if PER[c]['core']]

def macro(lab,subset,metric,cids):
    v=[]
    for c in cids:
        dd=PER[c]['new'].get(lab)
        if dd is None: continue
        x=dd[subset][metric]
        if x is not None: v.append(x)
    return statistics.mean(v) if v else None
def micro(lab,subset,metric,cids):
    tp=fp=fn=0
    for c in cids:
        dd=PER[c]['new'].get(lab)
        if dd is None: continue
        m=dd[subset];tp+=m['tp'];fp+=m['fp'];fn+=m['fn']
    if metric=='recall': return tp/(tp+fn) if (tp+fn) else None
    if metric=='prec': return tp/(tp+fp) if (tp+fp) else None
    if metric=='f1':
        r=tp/(tp+fn) if (tp+fn) else 0;p=tp/(tp+fp) if (tp+fp) else 0
        return 2*p*r/(p+r) if (p+r) else 0.0
    if metric=='jac': return tp/(tp+fp+fn) if (tp+fp+fn) else 0.0
ro=lambda x:None if x is None else round(x,4)

def block(cids):
    S={}
    for lab in CMP:
        ms={}
        for subset in ('main','all'):
            ms[subset]=dict(macro=dict(recall=ro(macro(lab,subset,'recall',cids)),prec=ro(macro(lab,subset,'prec',cids)),
                                       f1=ro(macro(lab,subset,'f1',cids)),jac=ro(macro(lab,subset,'jac',cids))),
                            micro=dict(recall=ro(micro(lab,subset,'recall',cids)),prec=ro(micro(lab,subset,'prec',cids)),
                                       f1=ro(micro(lab,subset,'f1',cids)),jac=ro(micro(lab,subset,'jac',cids))))
        units=[PER[c]['new'][lab]['units_main'] for c in cids if PER[c]['new'].get(lab)]
        points=[PER[c]['new'][lab]['points_main'] for c in cids if PER[c]['new'].get(lab)]
        S[lab]=dict(metrics=ms,mean_units_main=round(statistics.mean(units),3) if units else None,
                    mean_points_main=round(statistics.mean(points),3) if points else None,
                    sum_tp_main=sum(PER[c]['new'][lab]['main']['tp'] for c in cids if PER[c]['new'].get(lab)))
    return S

S=dict(n_cases=len(CASE_IDS),n_scored=len(SCORED),n_core=len(CORE),n_unscored=len(UNSCORED),
       exclude=sorted(EXCLUDE),unscored={c:PER[c]['note'] for c in UNSCORED},
       全量86=block(SCORED),核心集64=block(CORE))

# visit 分层
for bucket in ('复诊','首诊'):
    cs=[c for c in SCORED if PER[c]['vt']==bucket]
    S.setdefault('visit分层',{})[bucket]=dict(n=len(cs))
    for lab in CMP:
        S['visit分层'][bucket][lab]=dict(recall=ro(macro(lab,'main','recall',cs)),f1=ro(macro(lab,'main','f1',cs)),
                                          prec=ro(macro(lab,'main','prec',cs)),jac=ro(macro(lab,'main','jac',cs)))
# chain 分层
follow=[c for c in SCORED if PER[c]['chain'].startswith('followup')]
anchor=[c for c in SCORED if PER[c]['chain']=='first_visit' or PER[c]['chain'].startswith('anchor')]
for nm,cs in [('followup',follow),('anchor_first',anchor)]:
    S.setdefault('chain分层',{})[nm]=dict(n=len(cs))
    for lab in CMP:
        S['chain分层'][nm][lab]=dict(recall=ro(macro(lab,'main','recall',cs)),f1=ro(macro(lab,'main','f1',cs)),
                                     prec=ro(macro(lab,'main','prec',cs)),jac=ro(macro(lab,'main','jac',cs)))

# 零命中/满分
S['v11零命中']=[c for c in SCORED if PER[c]['new']['v11']['main']['tp']==0]
S['v11满分']=[c for c in SCORED if PER[c]['new']['v11']['main']['recall'] and PER[c]['new']['v11']['main']['recall']>=0.999]
# v11 主穴统计
pts=[PER[c]['new']['v11']['points_main'] for c in SCORED]
S['v11主穴统计']=dict(mean_units=round(statistics.mean([PER[c]['new']['v11']['units_main'] for c in SCORED]),3),
                     mean_points=round(statistics.mean(pts),3),min=min(pts),max=max(pts))
# 执行方差 v11 vs v9
same=diff=du=0
for c in CASE_IDS:
    a=set(BLIND['v9'][c].get('主穴',[]));b=set(BLIND['v11'][c].get('主穴',[]))
    if a==b: same+=1
    else: diff+=1;du+=len(a^b)
S['执行方差_v11_vs_v9']=dict(一致案=same,差异案=diff,差异单元=du)

# ---- 控制组核对 ----
chk={
 '86全量_v5':S['全量86']['v5']['metrics']['main']['macro'],
 '86全量_v9':S['全量86']['v9']['metrics']['main']['macro'],
 '86全量_v10':S['全量86']['v10']['metrics']['main']['macro'],
 '核心集_v5':S['核心集64']['v5']['metrics']['main']['macro'],
 '核心集_v9':S['核心集64']['v9']['metrics']['main']['macro'],
 '核心集_v10':S['核心集64']['v10']['metrics']['main']['macro'],
}
exp={'86全量_v5':dict(recall=0.4308,prec=0.4090,f1=0.3988,jac=0.2670),
     '86全量_v9':dict(recall=0.4390,prec=0.3653,f1=0.3795,jac=0.2499),
     '86全量_v10':dict(recall=0.4125,prec=0.3732,f1=0.3685,jac=0.2440),
     '核心集_v5':dict(recall=0.4768,prec=0.4247,f1=0.4240,jac=0.2875),
     '核心集_v9':dict(recall=0.4914,prec=0.3827,f1=0.4074,jac=0.2722),
     '核心集_v10':dict(recall=0.4748,prec=0.3991,f1=0.4068,jac=0.2737)}
ok=True;detail={}
for k in exp:
    row={}
    for m in ('recall','prec','f1','jac'):
        got=chk[k][m];want=exp[k][m]
        match=got==want
        row[m]=dict(got=got,want=want,match=match)
        if not match: ok=False
    detail[k]=row
S['控制组核对']=dict(一致=ok,detail=detail)

# ---- 明细 CSV（93行）----
hdr=['case_id','visit_type','chain','核心集','gold穴数']
for lab in CMP:
    hdr+= [f'{lab}_主穴数',f'{lab}_点数',f'{lab}_TP',f'{lab}_FP',f'{lab}_FN',f'{lab}_R',f'{lab}_P',f'{lab}_F1',f'{lab}_Jac']
rows=[]
for c in CASE_IDS:
    row=[c,PER[c]['vt'],PER[c]['chain'],'Y' if PER[c]['core'] else 'N',PER[c]['gc']]
    for lab in CMP:
        dd=PER[c]['new'].get(lab)
        if dd is None or PER[c]['gc']==0: row+=['','','','','','','','','']
        else:
            m=dd['main']
            row+=[dd['units_main'],dd['points_main'],m['tp'],m['fp'],m['fn'],ro(m['recall']),ro(m['prec']),ro(m['f1']),ro(m['jac'])]
    rows.append(row)
csv.writer(open(os.path.join(HERE,'判分明细v11.csv'),'w',newline='',encoding='utf-8-sig')).writerows([hdr]+rows)

# ---- 逐案新旧差异 v11 vs v9 ----
dhdr=['case_id','核心集','v9主穴','v11主穴','新增','删除','v9_TP','v11_TP','ΔTP','v9_FP','v11_FP','ΔFP','v9_R','v11_R','ΔR','v9_F1','v11_F1','ΔF1','v9_P','v11_P','ΔP']
drows=[]
for c in SCORED:
    a=PER[c]['new']['v9'];b=PER[c]['new']['v11']
    drows.append([c,'Y' if PER[c]['core'] else 'N',';'.join(a['main_units']),';'.join(b['main_units']),
                  ';'.join(sorted(set(b['main_units'])-set(a['main_units']))),';'.join(sorted(set(a['main_units'])-set(b['main_units']))),
                  a['main']['tp'],b['main']['tp'],b['main']['tp']-a['main']['tp'],
                  a['main']['fp'],b['main']['fp'],b['main']['fp']-a['main']['fp'],
                  ro(a['main']['recall']),ro(b['main']['recall']),ro((b['main']['recall'] or 0)-(a['main']['recall'] or 0)),
                  ro(a['main']['f1']),ro(b['main']['f1']),ro((b['main']['f1'] or 0)-(a['main']['f1'] or 0)),
                  ro(a['main']['prec']),ro(b['main']['prec']),ro((b['main']['prec'] or 0)-(a['main']['prec'] or 0))])
csv.writer(open(os.path.join(HERE,'逐案新旧差异表v11_vs_v9.csv'),'w',newline='',encoding='utf-8-sig')).writerows([dhdr]+drows)

# ---- 误差分类表 v11（FN/FP 穴，能判则判）----
ehdr=['case_id','核心集','FN穴(gold漏)','FP穴(预测错)','FN疑似归类','FP疑似归类']
def classify_fp(p):
    # 粗略归类（判不准留空）
    if any(k in p for k in ['公孙','内关','后溪','申脉','列缺','照海','外关','临泣','足临泣']): return '八脉加组'
    if '灸' in p or p in ['肘尖']: return '灸法奇穴'
    if p.endswith('俞') or p.endswith('募'): return '背俞'
    if p in ['阿是']: return '个体偏好'
    return ''
def classify_fn(p,gold,c):
    return ''
erows=[]
for c in SCORED:
    dd=PER[c]['new']['v11'];G=set(PER[c]['G']);P=set(dd['pred_main'])
    fns=sorted(G-P);fps=sorted(P-G)
    erows.append([c,'Y' if PER[c]['core'] else 'N',';'.join(fns),';'.join(fps),
                  ';'.join('' for _ in fns),  # FN 不硬造
                  ';'.join(classify_fp(p) for p in fps)])
csv.writer(open(os.path.join(HERE,'误差分类表v11.csv'),'w',newline='',encoding='utf-8-sig')).writerows([ehdr]+erows)

# ---- 改动前后分差表 ----
sim={'C1':dict(dF1=0.0049,dJac=0.0038),'C2':dict(dF1=0.0071,dJac=0.0055),
     'C3':dict(dF1=0.0045,dJac=0.0037),'C5':dict(dF1=0.0212,dJac=0.0164),'318':None}
def delta(blockname,lab_a='v10',lab_b='v11'):
    blk=S[blockname]
    ra=blk[lab_a]['metrics']['main']['macro'];rb=blk[lab_b]['metrics']['main']['macro']
    return dict(dF1=ro((rb['f1'] or 0)-(ra['f1'] or 0)),dJac=ro((rb['jac'] or 0)-(ra['jac'] or 0)),
                dR=ro((rb['recall'] or 0)-(ra['recall'] or 0)),dP=ro((rb['prec'] or 0)-(ra['prec'] or 0)))
S['改动前后分差']=dict(
    说明='实测为 C1/C2/C3/C5 五改动聚合结果（v11−v10），单项归因以模拟轨为准',
    模拟轨=sim,
    实测轨_全量86=delta('全量86'),
    实测轨_核心集64=delta('核心集64'))

json.dump(S,open(os.path.join(HERE,'判分汇总v11.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)

# ---- 控制台 ----
print('控制组一致=',S['控制组核对']['一致'])
for k in exp: print(k,detail[k])
print('=== 全量86 main macro ===')
for lab in CMP:
    m=S['全量86'][lab]['metrics']['main']['macro'];u=S['全量86'][lab]['mean_units_main']
    print(f'{lab}: R={m["recall"]} P={m["prec"]} F1={m["f1"]} Jac={m["jac"]} 单元均={u}')
print('=== 核心集64 main macro ===')
for lab in CMP:
    m=S['核心集64'][lab]['metrics']['main']['macro']
    print(f'{lab}: R={m["recall"]} P={m["prec"]} F1={m["f1"]} Jac={m["jac"]}')
print('v11主穴统计=',S['v11主穴统计'])
print('执行方差=',S['执行方差_v11_vs_v9'])
print('零命中v11=',S['v11零命中'],'满分=',S['v11满分'])
print('实测分差全量=',S['改动前后分差']['实测轨_全量86'],'核心=',S['改动前后分差']['实测轨_核心集64'])
