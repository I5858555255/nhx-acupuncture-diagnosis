# -*- coding: utf-8 -*-
import csv, os, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
OUT = os.path.join(BASE, "sf10_阶段E")

# ① 93行与明细ID一致
src = list(csv.DictReader(open(os.path.join(BASE,r"盲法93_v10\判分明细v10.csv"),encoding='utf-8-sig')))
mine = list(csv.DictReader(open(os.path.join(OUT,"误差分类表v10.csv"),encoding='utf-8-sig')))
src_ids = [r['case_id'] for r in src]
mine_ids = [r['case_id'] for r in mine]
print("① 明细行数:",len(src_ids)," 表行数:",len(mine_ids)," ID集合一致:",set(src_ids)==set(mine_ids)," 顺序一致:",src_ids==mine_ids)

# ② 频次重算一致
fn=Counter(); fp=Counter()
for r in src:
    for p in r['漏穴清单'].split(';'):
        if p: fn[p]+=1
    for p in r['未命中清单'].split(';'):
        if p: fp[p]+=1
hf = {r['归一化后点']:int(r['出现案数']) for r in csv.DictReader(open(os.path.join(OUT,"高频漏穴表.csv"),encoding='utf-8-sig'))}
hf2 = {r['穴名']:int(r['出现案数']) for r in csv.DictReader(open(os.path.join(OUT,"高频误加穴表.csv"),encoding='utf-8-sig'))}
ok1=all(hf.get(p)==n for p,n in fn.items()) and len(hf)==len(fn)
ok2=all(hf2.get(p)==n for p,n in fp.items()) and len(hf2)==len(fp)
print("② 漏穴频次重算一致:",ok1," 误加频次重算一致:",ok2)

# ③ 五案四类齐备
md = open(os.path.join(OUT,"五案归因报告.md"),encoding='utf-8').read()
for cid in ['201_01','207_01','318_01','216_04','156_05']:
    i = md.find(f"## ")
# 检查每案小节内四类标签
for cid in ['201_01','207_01','318_01','216_04','156_05']:
    seg = md[md.find(cid):md.find(cid)+2500]
    need = ['① 资料缺失','② 复诊历史缺失','③ 规则未命中','④ 个体偏好']
    miss=[n for n in need if n not in seg]
    print(f"③ {cid} 四类齐备:", not miss, miss if miss else "")

# 列名核对
print("列名:", list(mine[0].keys()))
# 主诉类型覆盖
comp = Counter(r['主诉类型'] for r in mine)
print("主诉类型分布:", dict(comp))
