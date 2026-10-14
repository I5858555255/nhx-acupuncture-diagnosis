# -*- coding: utf-8 -*-
"""score_m5d.py — M5-D 预测级消融（非盲法级重跑）。
对每个 M2 条目 X：在触发案中，移除 v12 相对 v11 新增、且属于 X 规则穴集的点，重算点级分。"""
import json, os, sys, csv, statistics, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验'; BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','D_消融'); os.makedirs(HERE,exist_ok=True)
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints

v11=json.load(open(os.path.join(ROOT,'盲法93_v11','_blind93v11_results.json'),encoding='utf-8'))
v12=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids']
SC=[c for c in CASE_IDS if len(NEW[c]['gold_members'])>0]

def points(rec): return normalize_acupoints(rec.get('主穴',[]))
# 每案 v11/v12 点集与 TP
CASE={}
for c in SC:
    G=set(NEW[c]['gold_members'])
    P11=points(v11[c]); P12=points(v12[c])
    new=P12-P11
    CASE[c]=dict(G=G,P11=P11,P12=P12,new=new,
                 tp11=len(P11&G),tp12=len(P12&G),fp12=len(P12-G))

def macro_F1(ablated):
    """ablated: dict c->点集(消融后)。宏 F1。"""
    f1s=[];tp=fp=fn=0
    for c in SC:
        P=ablated[c];G=CASE[c]['G']
        t=len(P&G);f=len(P-G);n=len(G-P)
        tp+=t;fp+=f;fn+=n
        rc=t/len(G) if G else 0;pr=t/len(P) if P else 0
        f1=2*pr*rc/(pr+rc) if (pr+rc)>0 else 0
        f1s.append(f1)
    return statistics.mean(f1s),tp,fp,fn

base={c:CASE[c]['P12'] for c in SC}
base_F1,base_tp,base_fp,base_fn=macro_F1(base)

# M2 规则穴集 + 触发案
RULES={
 'M2-01':(set(['肩髃']),['60_01','63_01','66_01']),
 'M2-02':(set(['神门','大陵']),['63_01','66_01']),
 'M2-03':(set(['大陵']),['66_01','318_01']),
 'M2-04':(set(['外关','足临泣','临泣']),['60_01','61_01','62_01','65_01','66_01']),
 'M2-05':(set(['巨阙','天突','关元','中脘','公孙','内关']),['1_01','57_01','140_01']),
 'M2-06':(set(['阴陵泉','地机','三阴交','复溜','水泉','照海','关元','中极','水分','水道','太冲']),['140_01','156_05']),
 'M2-07':(set(['肩井','足三里']),['13_01']),
 'M2-09':(set(['三间','后溪','鹤顶','内膝眼','外膝眼','阴陵泉','曲池','足三里']),['8_01']),
 'M2-10':(set(['迎香','内迎香']),['1_01']),
 'M2-11':(set(['肝关']),['1_01']),
 'M2-12':(set(['鱼际','行间','侠溪','太阳','率谷','耳心点']),['57_01']),
 'M2-13':(set(['关元','中极','水道','阴陵泉','三阴交','太冲']),['198_01']),
}
def ablate(items):
    """对给定条目集，在其触发案中移除 new∩规则集 的点。"""
    rm={}
    pts={c:set(base[c]) for c in SC}
    for X,(pset,cases) in items.items():
        for c in cases:
            if c not in pts:continue
            drop=CASE[c]['new']&pset
            pts[c]-=drop
            rm.setdefault(c,set()).update(drop)
    return pts,rm

rows=[]
for X,(pset,cases) in RULES.items():
    pts,rm=ablate({X:(pset,cases)})
    f1,tp,fp,fn=macro_F1(pts)
    removed=sum(len(v) for v in rm.values())
    rows.append(dict(条目=X,触发案=len(cases),移除点=removed,
        dTP=base_tp-tp,dFP=base_fp-fp,dF1=round(base_F1-f1,4),
        移除明细={c:sorted(v) for c,v in rm.items()}))

# 重叠案：组合 vs 边际
overlap={
 '1_01(M2-05/10/11)':['M2-05','M2-10','M2-11'],
 '57_01(M2-05/12)':['M2-05','M2-12'],
}
comb=[]
for nm,items in overlap.items():
    it={X:RULES[X] for X in items}
    pts,rm=ablate(it);f1,tp,fp,fn=macro_F1(pts)
    comb.append(dict(案=nm,组合移除点={c:sorted(v) for c,v in rm.items()},组合dTP=base_tp-tp,组合dFP=base_fp-fp,组合dF1=round(base_F1-f1,4)))

out=dict(base_F1=round(base_F1,4),base_tp=base_tp,base_fp=base_fp,base_fn=base_fn,逐条=rows,组合=comb)
json.dump(out,open(os.path.join(HERE,'消融明细.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(HERE,'逐条消融表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['条目','触发案数','移除点计数','ΔTP','ΔFP','ΔF1','移除明细'])
    for r in rows:
        w.writerow([r['条目'],r['触发案'],r['移除点'],r['dTP'],r['dFP'],r['dF1'],json.dumps(r['移除明细'],ensure_ascii=False)])
print('base F1=',round(base_F1,4),'TP',base_tp,'FP',base_fp)
for r in rows:print(r['条目'],'移除',r['移除点'],'ΔTP',r['dTP'],'ΔFP',r['dFP'],'ΔF1',r['dF1'],r['移除明细'])
print('组合:',comb)
