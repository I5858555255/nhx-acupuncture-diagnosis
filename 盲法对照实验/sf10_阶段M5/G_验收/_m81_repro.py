# -*- coding: utf-8 -*-
"""M8.1 可复现触发清单：--root 参数，cwd 无关"""
import os, io, sys, pickle, argparse
ap=argparse.ArgumentParser(); ap.add_argument("--root",default=r"D:\projectAGI\nhx"); a=ap.parse_args()
ROOT=a.root; BLIND=os.path.join(ROOT,"盲法对照实验"); SYMP=os.path.join(BLIND,"盲法93","symptoms")
g=pickle.load(open(os.path.join(BLIND,"benchmark_v2","_gold_results93v2.pkl"),"rb"))
SC=[c for c in g["case_ids"] if len(g["results"][c]["gold_members"])>0]
TRIG=["项强","項強","脖子僵硬","脖子鬆","脖子松","後枕","后枕","後項","后项","頸項痛","颈项痛","項痛","项痛","後項會很緊"]
EXCL=["頸部及手足關節痛","颈部及手足关节痛","頸部淋巴結","颈部淋巴结"]
found=[]
for cid in SC:
    t=io.open(os.path.join(SYMP,cid+"_symptoms.txt"),encoding="utf-8").read()
    hits=[w for w in TRIG if w in t]; excl=[w for w in EXCL if w in t]
    if hits and not excl: found.append(cid)
print("ROOT=",ROOT); print("触发案(6)=",sorted(found))
assert sorted(found)==sorted(["199_01","200_01","225_01","323_01","345_01","346_01"]), "复现失败"
print("复现断言通过: 与冻结6案一致")
