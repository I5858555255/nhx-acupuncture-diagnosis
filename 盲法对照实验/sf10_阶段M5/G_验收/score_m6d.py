# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
v12=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
v13=json.load(open(os.path.join(HERE,'盲法v13rc1','_blind93v13rc1_results.json'),encoding='utf-8'))
def s(rec,c):
    G=set(NEW[c]['gold_members']);P=normalize_units(rec.get('主穴',[]));m=per_case_metrics(G,P);return m
chains={}
for c in CASE_IDS:
    if len(NEW[c]['gold_members'])==0:continue
    ch=SUMMARY['chain_map'].get(c,'')
    if ch.startswith('anchor') or ch.startswith('followup'):key=ch.split('_')[1]
    else:key='S_'+c
    chains.setdefault(key,[]).append(c)
RULE_TRIG={'R2':['140_01','141_01'],'R3':['156_05'],'RC-5':['60_01','66_01','68_01','73_01','76_01','77_01','234_01'],
           'RC-6':['136_01','137_01','194_01','249_01','70_01']}
rows=[]
for key,cs in sorted(chains.items()):
    f12=[s(v12[c],c)['f1'] for c in cs if s(v12[c],c)['f1'] is not None]
    f13=[s(v13[c],c)['f1'] for c in cs if s(v13[c],c)['f1'] is not None]
    tp=sum(s(v13[c],c)['tp'] for c in cs);fp=sum(s(v13[c],c)['fp'] for c in cs);fn=sum(s(v13[c],c)['fn'] for c in cs)
    nf=sum(1 for c in cs if not SUMMARY['chain_map'][c].startswith('followup'))
    nb=len(cs)-nf
    trig=[r for r,ts in RULE_TRIG.items() if set(ts)&set(cs)]
    rows.append([key,len(cs),nf,nb,round(statistics.mean(f12),4),round(statistics.mean(f13),4),
                 round(statistics.mean(f13)-statistics.mean(f12),4),tp,fp,fn,';'.join(trig)])
with open(os.path.join(HERE,'按链留出验证表.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['链','案数','首诊数','复诊数','v12_F1','v13_F1','ΔF1','v13_TP','v13_FP','v13_FN','含规则触发案']);w.writerows(rows)
print('链数',len(rows),'总案',sum(r[1] for r in rows),'TP和',sum(r[7] for r in rows),'FP和',sum(r[8] for r in rows),'FN和',sum(r[9] for r in rows))
fs=[r[5] for r in rows];print('v13链F1 均值',round(statistics.mean(fs),4),'最小',min(fs),'最大',max(fs))
print('多案链:',[r for r in rows if r[1]>1])
