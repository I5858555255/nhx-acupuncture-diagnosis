# -*- coding: utf-8 -*-
"""score_m5d2.py — C 规则候选受控验证（预测级，非盲法重跑）。
对每条候选 X：在其目标案上添加/移除候选穴组，重算点级 ΔTP/ΔFP/ΔF1。"""
import json, os, sys, csv, statistics, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','D_消融','候选验证');os.makedirs(HERE,exist_ok=True)
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints
v12=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids']
SC=[c for c in CASE_IDS if len(NEW[c]['gold_members'])>0]
def pts(rec):return normalize_acupoints(rec.get('主穴',[]))
BASE={c:pts(v12[c]) for c in SC}
GOLD={c:set(NEW[c]['gold_members']) for c in SC}

def eval_set(Pset):
    f1s=[];tp=fp=fn=0
    for c in SC:
        P=Pset[c];G=GOLD[c]
        t=len(P&G);f=len(P-G);n=len(G-P);tp+=t;fp+=f;fn+=n
        rc=t/len(G) if G else 0;pr=t/len(P) if P else 0
        f1=2*pr*rc/(pr+rc) if (pr+rc)>0 else 0
        f1s.append(f1)
    return statistics.mean(f1s),tp,fp,fn
bF1,bTP,bFP,bFN=eval_set(BASE)

def apply(changes):
    """changes: {case:{'add':set(),'del':set()}} 从 BASE 出发。"""
    P={c:set(BASE[c]) for c in SC}
    for c,ch in changes.items():
        if c not in P:continue
        P[c]=(P[c]|ch.get('add',set()))-ch.get('del',set())
    return P

# 每条候选：目标案 + 操作（add/del 穴）
CANDS={
 'R1':dict(t=['208_01','221_01'],add={'水泉','大陵','仆参'},note='足跟痛补肾+对侧大陵'),
 'R2':dict(t=['140_01','141_01','142_01','143_01','144_01','145_01','146_01','148_01','149_01'],
           add={'复溜','水泉','照海','公孙','内关','巨阙','关元'},del_={'外关','足临泣','临泣','大包','水道'},note='肺积水心肾阳虚亚型分流'),
 'R3':dict(t=['156_05','156_06','223_01'],add={'曲池','足三里'},note='五十肩阳明虚曲池足三里'),
 'R4':dict(t=[],add=set(),del_=set(),note='随访锚点维持=历史链规则，symptoms-only 不可触发，跳过量化'),
 'R5':dict(t=['22_01','23_01','207_01'],add=set(),del_={'公孙','内关','太渊','丘墟','侠溪','迎香','内迎香','养老','间使','列缺','照海','肝关','行间'},note='极简方反向约束删凑数组'),
 'R6':dict(t=['212_01','209_01','199_01','200_01','201_01','202_01','216_01'],add={'后溪','申脉'},del_={'外关','足临泣','临泣'},note='八脉按症分流后枕项强→后溪申脉'),
 'R7':dict(t=['207_01','236_01','118_01','194_01'],add={'丘墟','侠溪','商丘','解溪'},note='外踝胆经/单踝扭伤组'),
 'RC-1':dict(t=['311_01','312_01','37_01','38_01'],add={'心俞','督俞','灵台'},del_={'胆俞','肾俞','肝俞'},note='压痛二分：四肢奇穴压痛不反推背俞'),
 'RC-2':dict(t=['318_01','342_01'],add={'太渊','合谷','曲池','大陵'},note='多指麻按指分经整组'),
 'RC-3':dict(t=['49_01','55_01','38_01'],add={'巨阙','天突','关元'},note='心脏三针原子整组不拆'),
 'RC-4':dict(t=['61_01','62_01','64_01','65_01'],add=set(),del_={'肩髃'},note='肩髃vs外关校准删胀痛案肩髃'),
 'RC-5':dict(t=['63_01','66_01'],add={'神门','大陵'},note='病在心神门大陵同出'),
 'RC-6':dict(t=['249_01'],add={'委中','承山','腰腿点'},note='膀胱经腰背痛整组'),
}
rows=[]
for cid,c in CANDS.items():
    if not c['t']:
        rows.append(dict(ID=cid,触发案=0,加穴=0,del穴=0,dTP=0,dFP=0,dF1=0,判定='不合入',note=c['note']+'（symptoms-only 不可触发）'));continue
    ch={t:dict(add=c.get('add',set()),del_=c.get('del_',set())) for t in c['t']}
    P=apply(ch);f1,tp,fp,fn=eval_set(P)
    # 统计实际添加/删除点数
    added=sum(len((ch[t]['add']-BASE[t])) for t in c['t'] if t in BASE)
    removed=sum(len(ch[t]['del_']&BASE[t]) for t in c['t'] if t in BASE)
    rows.append(dict(ID=cid,触发案=len(c['t']),加穴=added,del穴=removed,
        dTP=tp-bTP,dFP=fp-bFP,dF1=round(f1-bF1,4),note=c['note']))
# 判定（Δ=新−基；ΔTP>0 且 ΔFP<=0 为有收益）
for r in rows:
    if r['触发案']==0:r['判定']='不合入(不可触发)'
    elif r['dTP']>0 and r['dFP']<=0:r['判定']='合入'
    elif r['dTP']>0 and r['dFP']>0:r['判定']='待定(伴FP)'
    elif r['dTP']==0:r['判定']='待定/无收益'
    else:r['判定']='不合入(负收益)'
json.dump(dict(base=dict(F1=round(bF1,4),TP=bTP,FP=bFP),rows=rows),open(os.path.join(HERE,'候选验证明细.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(HERE,'候选验证表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['候选ID','触发案数','添加点','删除点','ΔTP','ΔFP','ΔF1','判定','说明'])
    for r in rows:w.writerow([r['ID'],r['触发案'],r['加穴'],r['del穴'],r['dTP'],r['dFP'],r['dF1'],r['判定'],r['note']])
print('base F1',round(bF1,4),'TP',bTP,'FP',bFP)
for r in rows:print(r['ID'],'触发',r['触发案'],'加',r['加穴'],'删',r['del穴'],'ΔTP',r['dTP'],'ΔFP',r['dFP'],'ΔF1',r['dF1'],'->',r['判定'])
