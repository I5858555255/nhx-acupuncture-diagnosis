# -*- coding: utf-8 -*-
import json, os, sys, pickle
ROOT=r'D:\projectAGI\nhx\盲法对照实验'
BENCH=os.path.join(ROOT,'benchmark_v2')
sys.path.insert(0,BENCH)
from normalize_acupoints import normalize_acupoints

SHARD=['107_01','117_01','118_01','136_01','137_01','13_01','140_01','141_01','142_01','143_01','144_01','145_01','146_01','148_01','149_01','156_03','156_04','156_05','156_06','160_01','194_01','195_01','198_01','199_01','1_01','200_01','201_01','202_01','207_01','208_01','209_01','212_01','213_01','214_01','216_01','216_02','216_03','216_04','216_05','221_01','223_01','225_01','22_01','234_01','236_01','23_01']

BLIND=json.load(open(os.path.join(ROOT,'盲法93_v12','_blind93v12_results.json'),encoding='utf-8'))
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results']

out=[]
for cid in SHARD:
    rec=BLIND[cid]
    G=set(NEW[cid]['gold_members'])
    Punits=rec.get('主穴',[])
    P=set(normalize_acupoints(Punits))
    tp=sorted(P&G); fp=sorted(P-G); fn=sorted(G-P)
    out.append(dict(case=cid,
        gold=sorted(G), gold_n=len(G),
        pred_units=Punits, pred_points=sorted(P),
        tp=tp, fp=fp, fn=fn,
        zuoxue=rec.get('佐穴',[]),
        cankao=rec.get('临床参考建议',[])))

json.dump(out, open(os.path.join(ROOT,'sf10_阶段M5','C_残余归因','_shard1_extract.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
# print compact table
for r in out:
    print(f"=== {r['case']} (gold={r['gold_n']}) ===")
    print(f"  GOLD: {','.join(r['gold'])}")
    print(f"  PRED(units): {','.join(r['pred_units'])}")
    print(f"  PRED(pts):   {','.join(r['pred_points'])}")
    print(f"  TP: {','.join(r['tp'])}")
    print(f"  FP: {','.join(r['fp'])}")
    print(f"  FN: {','.join(r['fn'])}")
