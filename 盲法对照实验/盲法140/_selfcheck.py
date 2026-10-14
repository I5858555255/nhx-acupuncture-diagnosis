# -*- coding: utf-8 -*-
import json, csv, os, statistics
BASE=r"D:\projectAGI\nhx\盲法对照实验\盲法140"
blind=json.load(open(os.path.join(BASE,'_blind140_results.json'),encoding='utf-8'))
rows=list(csv.DictReader(open(os.path.join(BASE,'判分明细.csv'),encoding='utf-8-sig')))
print("1) CSV行数:", len(rows), "==146?", len(rows)==146)
csv_ids=set(r['case_id'] for r in rows)
print("2) case_id与blind键一致:", csv_ids==set(blind.keys()))
# 复算均值
rs=[]; rmas=[]; precs=[]
for r in rows:
    if r['重合率主']:
        rs.append(float(r['重合率主'])); rmas.append(float(r['重合率主佐'])); precs.append(float(r['精确率']))
print("3) 复算均值: 重合主=%.4f 主佐=%.4f 精确=%.4f 中位主=%.4f"%(
    statistics.mean(rs), statistics.mean(rmas), statistics.mean(precs), statistics.median(rs)))
summ=json.load(open(os.path.join(BASE,'判分汇总.json'),encoding='utf-8'))
print("   JSON汇总: 重合主=%.4f 主佐=%.4f 精确=%.4f 中位主=%.4f"%(
    summ['mean_r_main'],summ['mean_r_ma'],summ['mean_prec'],summ['median_r_main']))
md=open(os.path.join(BASE,'盲法140判分报告.md'),encoding='utf-8').read()
for sec in ['146','基线','四层','特效奇穴','教程未录','无法解析','人工核读','140']:
    print(f"4) 报告含[{sec}]:", sec in md)
print("5) 文件大小:")
for f in ['判分明细.csv','判分汇总.json','盲法140判分报告.md','gold_parse.py']:
    print("  ", f, os.path.getsize(os.path.join(BASE,f)), "bytes")
