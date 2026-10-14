# -*- coding: utf-8 -*-
"""score_sf10_v12.py — v12 统一评分（benchmark_v2）。
CMP=[v5,v6,v9,v10,v11,v12]；86全量/64核心集/visit/chain分层 + M2 逐条收益（v12−v11）。"""
import json, os, sys, csv, statistics, pickle

ROOT=r'D:\projectAGI\nhx\盲法对照实验'
BENCH=os.path.join(ROOT,'benchmark_v2'); HERE=os.path.join(ROOT,'盲法93_v12')
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints
FILES={
 'v5':os.path.join(ROOT,'盲法93_v5','_blind93v5_results.json'),
 'v6':os.path.join(ROOT,'盲法93_v6','_blind93v6_results.json'),
 'v9':os.path.join(ROOT,'盲法93_v9','_blind93v9_results.json'),
 'v10':os.path.join(ROOT,'盲法93_v10','_blind93v10_results.json'),
 'v11':os.path.join(ROOT,'盲法93_v11','_blind93v11_results.json'),
 'v12':os.path.join(HERE,'_blind93v12_results.json'),
}
CMP=['v5','v6','v9','v10','v11','v12']
BLIND={lab:json.load(open(fp,encoding='utf-8')) for lab,fp in FILES.items()}
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
VT={}
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段D','组装清单.csv'),encoding='utf-8-sig')):
    v=r['visit_type'];VT[r['case_id']]='复诊' if v.startswith('复诊') else ('首诊' if v.startswith('首诊') else '其他')

def pm(G,P):
    tp=len(P&G);fp=len(P-G);fn=len(G-P)
    recall=tp/len(G) if G else None;prec=tp/len(P) if P else None
    f1=(2*prec*recall/(prec+recall)) if (prec and recall and (prec+recall)>0) else (0.0 if tp==0 else None)
    jac=tp/(tp+fp+fn) if (tp+fp+fn)>0 else 0.0
    return dict(tp=tp,fp=fp,fn=fn,recall=recall,prec=prec,f1=f1,jac=jac)
PER={}
for cid in CASE_IDS:
    G=set(NEW[cid]['gold_members']);d={}
    for lab in CMP:
        rec=BLIND[lab].get(cid)
        if rec is None:d[lab]=None;continue
        Pm=normalize_acupoints(rec.get('主穴',[]));Pa=normalize_acupoints(rec.get('主穴',[])+rec.get('佐穴',[]))
        d[lab]=dict(units_main=len(rec.get('主穴',[])),points_main=len(Pm),points_all=len(Pa),
                    main=pm(G,Pm),all=pm(G,Pa),pred_main=sorted(Pm),main_units=rec.get('主穴',[]))
    PER[cid]=dict(G=sorted(G),gc=len(G),new=d,chain=SUMMARY['chain_map'].get(cid,'first_visit'),vt=VT.get(cid,''),
                  note=NEW[cid]['note'],core=cid not in EXCLUDE)
SCORED=[c for c in CASE_IDS if PER[c]['gc']>0]
UNSCORED=[c for c in CASE_IDS if PER[c]['gc']==0]
CORE=[c for c in SCORED if PER[c]['core']]
def macro(lab,subset,metric,cids):
    v=[PER[c]['new'][lab][subset][metric] for c in cids if PER[c]['new'].get(lab) and PER[c]['new'][lab][subset][metric] is not None]
    return statistics.mean(v) if v else None
def micro(lab,subset,metric,cids):
    tp=fp=fn=0
    for c in cids:
        dd=PER[c]['new'].get(lab)
        if dd is None:continue
        m=dd[subset];tp+=m['tp'];fp+=m['fp'];fn+=m['fn']
    if metric=='recall':return tp/(tp+fn) if (tp+fn) else None
    if metric=='prec':return tp/(tp+fp) if (tp+fp) else None
    if metric=='f1':
        r=tp/(tp+fn) if (tp+fn) else 0;p=tp/(tp+fp) if (tp+fp) else 0
        return 2*p*r/(p+r) if (p+r) else 0.0
    if metric=='jac':return tp/(tp+fp+fn) if (tp+fp+fn) else 0.0
ro=lambda x:None if x is None else round(x,4)
def block(cids):
    S={}
    for lab in CMP:
        ms={}
        for subset in ('main','all'):
            mac=dict(recall=ro(macro(lab,subset,'recall',cids)),prec=ro(macro(lab,subset,'prec',cids)),f1=ro(macro(lab,subset,'f1',cids)),jac=ro(macro(lab,subset,'jac',cids)))
            mic=dict(recall=ro(micro(lab,subset,'recall',cids)),prec=ro(micro(lab,subset,'prec',cids)),f1=ro(micro(lab,subset,'f1',cids)),jac=ro(micro(lab,subset,'jac',cids)))
            ms[subset]=dict(macro=mac,micro=mic)
        units=[PER[c]['new'][lab]['units_main'] for c in cids if PER[c]['new'].get(lab)]
        points=[PER[c]['new'][lab]['points_main'] for c in cids if PER[c]['new'].get(lab)]
        S[lab]=dict(metrics=ms,mean_units_main=round(statistics.mean(units),3) if units else None,
                    mean_points_main=round(statistics.mean(points),3) if points else None,
                    sum_tp_main=sum(PER[c]['new'][lab]['main']['tp'] for c in cids if PER[c]['new'].get(lab)))
    return S
S=dict(n_cases=len(CASE_IDS),n_scored=len(SCORED),n_core=len(CORE),n_unscored=len(UNSCORED),
       unscored={c:PER[c]['note'] for c in UNSCORED},全量86=block(SCORED),核心集64=block(CORE))
for bucket in ('复诊','首诊'):
    cs=[c for c in SCORED if PER[c]['vt']==bucket];S.setdefault('visit分层',{})[bucket]=dict(n=len(cs))
    for lab in CMP:S['visit分层'][bucket][lab]=dict(recall=ro(macro(lab,'main','recall',cs)),f1=ro(macro(lab,'main','f1',cs)))
follow=[c for c in SCORED if PER[c]['chain'].startswith('followup')]
anchor=[c for c in SCORED if PER[c]['chain']=='first_visit' or PER[c]['chain'].startswith('anchor')]
for nm,cs in [('followup',follow),('anchor_first',anchor)]:
    S.setdefault('chain分层',{})[nm]=dict(n=len(cs))
    for lab in CMP:S['chain分层'][nm][lab]=dict(recall=ro(macro(lab,'main','recall',cs)),f1=ro(macro(lab,'main','f1',cs)))
S['零命中']={lab:[c for c in SCORED if PER[c]['new'][lab]['main']['tp']==0] for lab in CMP}
S['v12满分']=[c for c in SCORED if PER[c]['new']['v12']['main']['recall'] and PER[c]['new']['v12']['main']['recall']>=0.999]
pts=[PER[c]['new']['v12']['points_main'] for c in SCORED]
S['v12主穴统计']=dict(mean_units=round(statistics.mean([PER[c]['new']['v12']['units_main'] for c in SCORED]),3),mean_points=round(statistics.mean(pts),3),min=min(pts),max=max(pts))
same=diff=du=0
for c in CASE_IDS:
    a=set(BLIND['v11'][c].get('主穴',[]));b=set(BLIND['v12'][c].get('主穴',[]))
    if a==b:same+=1
    else:diff+=1;du+=len(a^b)
S['执行方差_v12_vs_v11']=dict(一致案=same,差异案=diff,差异单元=du)
# 控制组核对
exp={'86_v11':(S['全量86']['v11'],dict(recall=0.4488,prec=0.4518,f1=0.4223,jac=0.2871)),
     '86_v9':(S['全量86']['v9'],dict(recall=0.4390,prec=0.3653,f1=0.3795,jac=0.2499)),
     '核心_v11':(S['核心集64']['v11'],dict(recall=0.4999,prec=0.4582,f1=0.4470,jac=0.3075)),
     '核心_v9':(S['核心集64']['v9'],dict(recall=0.4914,prec=0.3827,f1=0.4074,jac=0.2722))}
ok=True;det={}
for k,(blk,w) in exp.items():
    row={}
    for m,want in w.items():
        got=blk['metrics']['main']['macro'][m];match=got==want
        row[m]=dict(got=got,want=want,match=match)
        if not match:ok=False
    det[k]=row
S['控制组核对']=dict(一致=ok,detail=det)
# 明细 CSV
hdr=['case_id','visit_type','chain','核心集','gold穴数']
for lab in CMP:hdr+=[f'{lab}_主穴数',f'{lab}_TP',f'{lab}_FP',f'{lab}_FN',f'{lab}_R',f'{lab}_P',f'{lab}_F1',f'{lab}_Jac']
rows=[]
for c in CASE_IDS:
    row=[c,PER[c]['vt'],PER[c]['chain'],'Y' if PER[c]['core'] else 'N',PER[c]['gc']]
    for lab in CMP:
        dd=PER[c]['new'].get(lab)
        if dd is None or PER[c]['gc']==0:row+=['','','','','','','','']
        else:
            m=dd['main'];row+=[dd['units_main'],m['tp'],m['fp'],m['fn'],ro(m['recall']),ro(m['prec']),ro(m['f1']),ro(m['jac'])]
    rows.append(row)
csv.writer(open(os.path.join(HERE,'判分明细v12.csv'),'w',newline='',encoding='utf-8-sig')).writerows([hdr]+rows)
# 逐案差异 v12 vs v11
dhdr=['case_id','核心集','v11主穴','v12主穴','新增','删除','ΔTP','ΔFP','ΔR','ΔP','ΔF1']
drows=[]
for c in SCORED:
    a=PER[c]['new']['v11'];b=PER[c]['new']['v12']
    drows.append([c,'Y' if PER[c]['core'] else 'N',';'.join(a['main_units']),';'.join(b['main_units']),
        ';'.join(sorted(set(b['main_units'])-set(a['main_units']))),';'.join(sorted(set(a['main_units'])-set(b['main_units']))),
        b['main']['tp']-a['main']['tp'],b['main']['fp']-a['main']['fp'],
        ro((b['main']['recall'] or 0)-(a['main']['recall'] or 0)),ro((b['main']['prec'] or 0)-(a['main']['prec'] or 0)),
        ro((b['main']['f1'] or 0)-(a['main']['f1'] or 0))])
csv.writer(open(os.path.join(HERE,'逐案新旧差异表v12_vs_v11.csv'),'w',newline='',encoding='utf-8-sig')).writerows([dhdr]+drows)
# 误差分类表
def classify_fp(p):
    if any(k in p for k in ['公孙','内关','后溪','申脉','列缺','照海','外关','临泣','足临泣']):return '八脉加组'
    if p=='肘尖' or '灸' in p:return '灸法奇穴'
    if p.endswith('俞') or p.endswith('募'):return '背俞'
    if p=='阿是':return '个体偏好'
    return ''
erows=[[c,'Y' if PER[c]['core'] else 'N',';'.join(sorted(set(PER[c]['G'])-set(PER[c]['new']['v12']['pred_main']))),
        ';'.join(sorted(set(PER[c]['new']['v12']['pred_main'])-set(PER[c]['G']))),'',
        ';'.join(classify_fp(p) for p in sorted(set(PER[c]['new']['v12']['pred_main'])-set(PER[c]['G'])))] for c in SCORED]
csv.writer(open(os.path.join(HERE,'误差分类表v12.csv'),'w',newline='',encoding='utf-8-sig')).writerows([['case_id','核心集','FN穴','FP穴','FN疑似归类','FP疑似归类']]+erows)
# ---- M2 逐条收益（v12−v11，审计触发案聚合）----
M2={
 'M2-01':['60_01','63_01','66_01'],'M2-02':['63_01','66_01'],'M2-03':['66_01','318_01'],
 'M2-04':['60_01','61_01','62_01','65_01','66_01'],'M2-05':['1_01','57_01','140_01'],
 'M2-06':['140_01','156_05'],'M2-07':['13_01'],'M2-09':['8_01'],'M2-10':['1_01'],
 'M2-11':['1_01'],'M2-12':['57_01'],'M2-13':['198_01']}
m2rows=[]
for item,cases in M2.items():
    dTP=sum(PER[c]['new']['v12']['main']['tp']-PER[c]['new']['v11']['main']['tp'] for c in cases if c in PER and PER[c]['gc']>0)
    dFP=sum(PER[c]['new']['v12']['main']['fp']-PER[c]['new']['v11']['main']['fp'] for c in cases if c in PER and PER[c]['gc']>0)
    if dTP>=1 and dFP<=0:verdict='有收益'
    elif dTP>=1:verdict='有收益(伴FP)'
    elif dTP==0:verdict='无收益'
    else:verdict='负收益'
    m2rows.append([item,len(cases),dTP,dFP,verdict,';'.join(cases)])
S['M2逐条收益']=m2rows
csv.writer(open(os.path.join(HERE,'逐条M2收益表.csv'),'w',newline='',encoding='utf-8-sig')).writerows(
    [['条目','目标案数','ΔTP合计','ΔFP合计','判定','依据案号']]+m2rows)
json.dump(S,open(os.path.join(HERE,'判分汇总v12.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('控制组一致=',ok)
print('=== 86全量 main macro ===')
for lab in CMP:
    m=S['全量86'][lab]['metrics']['main']['macro'];print(f'{lab}: R={m["recall"]} P={m["prec"]} F1={m["f1"]} Jac={m["jac"]} 单元均={S["全量86"][lab]["mean_units_main"]}')
print('=== 64核心集 ===')
for lab in CMP:
    m=S['核心集64'][lab]['metrics']['main']['macro'];print(f'{lab}: R={m["recall"]} P={m["prec"]} F1={m["f1"]} Jac={m["jac"]}')
print('零命中v12=',S['零命中']['v12'],'满分=',S['v12满分'])
print('执行方差=',S['执行方差_v12_vs_v11'])
print('主穴统计=',S['v12主穴统计'])
print('M2收益:')
for r in m2rows:print(' ',r)
