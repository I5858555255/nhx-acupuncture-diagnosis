# -*- coding: utf-8 -*-
"""score_m5a.py — M5-A 方法迁移核验（只读既有数据）。
分组：M1已审计28案 / 未参与M1的58案 / 全量86 / 核心集64；v12−v11 迁移核验。"""
import csv, json, statistics, os

ROOT=r'D:\projectAGI\nhx\盲法对照实验'
HERE=os.path.join(ROOT,'sf10_阶段M5','A_迁移核验')
os.makedirs(HERE,exist_ok=True)

# 明细（含六版本逐案 TP/FP/FN/R/P/F1/Jac）
rows=list(csv.DictReader(open(os.path.join(ROOT,'盲法93_v12','判分明细v12.csv'),encoding='utf-8-sig')))
SC=[r for r in rows if r['gold穴数'] not in ('','0')]  # 86 可判分

M1=set()
for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M1','归因汇总表.csv'),encoding='utf-8-sig')):
    M1.add(r['案号'])
M1_S=[r for r in SC if r['case_id'] in M1]
NON=[r for r in SC if r['case_id'] not in M1]
CORE=[r for r in SC if r['核心集']=='Y']

def num(x): return None if x in ('',None) else float(x)
def group_metrics(group):
    out={}
    for lab in ('v11','v12'):
        R=[num(r[f'{lab}_R']) for r in group if num(r[f'{lab}_R']) is not None]
        P=[num(r[f'{lab}_P']) for r in group if num(r[f'{lab}_P']) is not None]
        F1=[num(r[f'{lab}_F1']) for r in group if num(r[f'{lab}_F1']) is not None]
        J=[num(r[f'{lab}_Jac']) for r in group if num(r[f'{lab}_Jac']) is not None]
        tp=sum(int(r[f'{lab}_TP']) for r in group);fp=sum(int(r[f'{lab}_FP']) for r in group);fn=sum(int(r[f'{lab}_FN']) for r in group)
        units=[int(r[f'{lab}_主穴数']) for r in group]
        out[lab]=dict(macro_R=statistics.mean(R),macro_P=statistics.mean(P),macro_F1=statistics.mean(F1),macro_Jac=statistics.mean(J),
                      sum_tp=tp,sum_fp=fp,sum_fn=fn,
                      micro_R=tp/(tp+fn) if tp+fn else None,micro_P=tp/(tp+fp) if tp+fp else None,
                      mean_units=statistics.mean(units))
    return out

groups={'M1已审计28':M1_S,'未参与M1_58':NON,'全量86':SC,'核心集64':CORE}
G={nm:group_metrics(g) for nm,g in groups.items()}

def delta(a,b): return None if a is None or b is None else round(b-a,4)
summary={}
for nm in groups:
    a=G[nm]['v11'];b=G[nm]['v12']
    summary[nm]=dict(
        n=len(groups[nm]),
        v11=dict(R=round(a['macro_R'],4),P=round(a['macro_P'],4),F1=round(a['macro_F1'],4),Jac=round(a['macro_Jac'],4),TP=a['sum_tp'],FP=a['sum_fp'],FN=a['sum_fn']),
        v12=dict(R=round(b['macro_R'],4),P=round(b['macro_P'],4),F1=round(b['macro_F1'],4),Jac=round(b['macro_Jac'],4),TP=b['sum_tp'],FP=b['sum_fp'],FN=b['sum_fn']),
        dR=delta(a['macro_R'],b['macro_R']),dP=delta(a['macro_P'],b['macro_P']),dF1=delta(a['macro_F1'],b['macro_F1']),dJac=delta(a['macro_Jac'],b['macro_Jac']),
        dTP=b['sum_tp']-a['sum_tp'],dFP=b['sum_fp']-a['sum_fp'],dFN=b['sum_fn']-a['sum_fn'])

# 分层：visit_type / chain / v11错误量分桶
def strat(keyfn):
    buckets={}
    for r in SC:
        k=keyfn(r);buckets.setdefault(k,[]).append(r)
    out={}
    for k,g in buckets.items():
        a=group_metrics(g)['v11'];b=group_metrics(g)['v12']
        out[k]=dict(n=len(g),dR=delta(a['macro_R'],b['macro_R']),dP=delta(a['macro_P'],b['macro_P']),dF1=delta(a['macro_F1'],b['macro_F1']),dJac=delta(a['macro_Jac'],b['macro_Jac']))
    return out
def v11_errbucket(r):
    e=int(r['v11_FP'])+int(r['v11_FN'])
    return '0-3' if e<=3 else ('4-6' if e<=6 else '7+')
S_strat=dict(visit=strat(lambda r:r['visit_type']),chain=strat(lambda r:r['chain']),v11错误量=strat(v11_errbucket))

# M2 目标集（逐条M2收益表）
M2_targets={'M2-01':{'60_01','63_01','66_01'},'M2-02':{'63_01','66_01'},'M2-03':{'66_01','318_01'},
 'M2-04':{'60_01','61_01','62_01','65_01','66_01'},'M2-05':{'1_01','57_01','140_01'},
 'M2-06':{'140_01','156_05'},'M2-07':{'13_01'},'M2-09':{'8_01'},'M2-10':{'1_01'},'M2-11':{'1_01'},
 'M2-12':{'57_01'},'M2-13':{'198_01'}}
all_targets=set().union(*M2_targets.values())

# 逐案表
pc=[]
nontarget_gain=0;target_gain=0
for r in SC:
    dTP=int(r['v12_TP'])-int(r['v11_TP']);dFP=int(r['v12_FP'])-int(r['v11_FP']);dFN=int(r['v12_FN'])-int(r['v11_FN'])
    cid=r['case_id'];in_m1=cid in M1
    rules=[k for k,vs in M2_targets.items() if cid in vs]
    if dTP>0:
        if rules:tag='M2目标案增益('+','.join(rules)+')';target_gain+=1
        else:tag='非目标案增益(规则扩散/主穴数增加)';nontarget_gain+=1
    elif dTP==0 and dFP!=0:tag='ΔTP=0但ΔFP变化'
    elif dTP==0:tag='无变化'
    else:tag='ΔTP<0(退步)'
    pc.append([cid,'Y' if in_m1 else 'N',r['visit_type'],r['chain'],
               int(r['v11_TP']),int(r['v12_TP']),dTP,int(r['v11_FP']),int(r['v12_FP']),dFP,dFN,
               delta(num(r['v11_R']),num(r['v12_R'])),delta(num(r['v11_F1']),num(r['v12_F1'])),tag])
# 58 案改善/持平/退步
improved=[p for p in pc if p[1]=='N' and p[12] is not None and p[12]>0.0001]
worse=[p for p in pc if p[1]=='N' and p[12] is not None and p[12]<-0.0001]
flat=[p for p in pc if p[1]=='N' and p not in improved and p not in worse]

summary['归因统计']=dict(M2目标案增益=target_gain,非目标案增益=nontarget_gain,
                        非M158案_改善=len(improved),非M158案_持平=len(flat),非M158案_退步=len(worse))
json.dump(dict(分组=summary,分层=S_strat),open(os.path.join(HERE,'迁移核验汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
# 分组表
with open(os.path.join(HERE,'迁移核验分组表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['组','n','v11_R','v11_P','v11_F1','v11_Jac','v11_TP','v11_FP','v11_FN',
        'v12_R','v12_P','v12_F1','v12_Jac','v12_TP','v12_FP','v12_FN','ΔR','ΔP','ΔF1','ΔJac','ΔTP','ΔFP','ΔFN'])
    for nm,s in summary.items():
        if not isinstance(s,dict) or 'v11' not in s:continue
        a=s['v11'];b=s['v12']
        w.writerow([nm,s['n'],a['R'],a['P'],a['F1'],a['Jac'],a['TP'],a['FP'],a['FN'],
                    b['R'],b['P'],b['F1'],b['Jac'],b['TP'],b['FP'],b['FN'],
                    s['dR'],s['dP'],s['dF1'],s['dJac'],s['dTP'],s['dFP'],s['dFN']])
# 逐案表
with open(os.path.join(HERE,'迁移核验逐案表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','M1审计案','visit_type','chain','v11_TP','v12_TP','ΔTP','v11_FP','v12_FP','ΔFP','ΔFN','ΔR','ΔF1','归因标签'])
    w.writerows(pc)
print(json.dumps(summary,ensure_ascii=False,indent=1))
print('分层 visit:',json.dumps(S_strat['visit'],ensure_ascii=False))
print('分层 v11错误量:',json.dumps(S_strat['v11错误量'],ensure_ascii=False))
print('归因统计:',summary['归因统计'])
