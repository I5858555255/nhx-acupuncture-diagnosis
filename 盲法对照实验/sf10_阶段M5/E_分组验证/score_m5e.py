# -*- coding: utf-8 -*-
"""M5-E：86 案按患者链分桶分组验证（in-sample，非独立交叉验证）。"""
import csv, json, os, statistics, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','E_分组验证');os.makedirs(HERE,exist_ok=True)
import sys;sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];SUMMARY=g['summary']
v11=json.load(open(os.path.join(ROOT,'盲法93_v11','_blind93v11_results.json'),encoding='utf-8'))
v12=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
# 患者链：anchor_XX/followup_XX 归 XX 链；first_visit 单独成链
chains={}
for cid,ch in SUMMARY['chain_map'].items():
    if len(NEW[cid]['gold_members'])==0:continue
    if ch.startswith('anchor') or ch.startswith('followup'):
        key=ch.split('_')[1]  # 66/146/198/216
    else:
        key='S_'+cid  # 单案链
    chains.setdefault(key,[]).append(cid)
def score(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_acupoints(rec.get('主穴',[]))
    tp=len(P&G);rc=tp/len(G) if G else 0;pr=tp/len(P) if P else 0
    f1=2*pr*rc/(pr+rc) if (pr+rc)>0 else 0
    return rc,f1
rows=[]
for key,cs in sorted(chains.items()):
    if len(cs)==0:continue
    f11=[score(v11[c],c)[1] for c in cs];f12=[score(v12[c],c)[1] for c in cs]
    r11=[score(v11[c],c)[0] for c in cs];r12=[score(v12[c],c)[0] for c in cs]
    nf=sum(1 for c in cs if SUMMARY['chain_map'][c]=='first_visit' or SUMMARY['chain_map'][c].startswith('anchor'))
    nb=sum(1 for c in cs if SUMMARY['chain_map'][c].startswith('followup'))
    rows.append([key,len(cs),nf,nb,round(statistics.mean(r11),4),round(statistics.mean(f11),4),
                 round(statistics.mean(r12),4),round(statistics.mean(f12),4),
                 round(statistics.mean(f12)-statistics.mean(f11),4),';'.join(cs)])
with open(os.path.join(HERE,'分组交叉验证表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['患者链','案数','首诊/锚案数','复诊跟随数','v11_R','v11_F1','v12_R','v12_F1','ΔF1','案号']);w.writerows(rows)
print('链数=',len(rows),'总案数=',sum(r[1] for r in rows))
for r in rows:print(r[0],'n=',r[1],'首',r[2],'复',r[3],'v12_F1=',r[7],'Δ=',r[8])
