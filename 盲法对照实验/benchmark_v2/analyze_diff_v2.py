# -*- coding: utf-8 -*-
"""analyze_diff_v2.py — 新旧口径差异归因统计（工作项 B：差异报告数据）"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, '判分汇总v2.json'), encoding='utf-8'))

diffs = S['新旧差异_v9']
gc_changed = [d for d in diffs if d['old_gc'] != d['new_gc']]
print(f"可判分案数: {len(diffs)}")
print(f"gold 穴数变化案数（膝五针/三皇穴口径）: {len(gc_changed)}")
for d in gc_changed:
    print(f"  {d['case_id']}: old_gc={d['old_gc']} -> new_gc={d['new_gc']} (recall {d['old_r_main']} -> {d['new_recall']})")

print()
print("recall 变化分布（new - old）:")
up = [d for d in diffs if d['old_r_main'] is not None and d['new_recall'] - d['old_r_main'] > 1e-9]
down = [d for d in diffs if d['old_r_main'] is not None and d['new_recall'] - d['old_r_main'] < -1e-9]
same = [d for d in diffs if d['old_r_main'] is not None and abs(d['new_recall'] - d['old_r_main']) <= 1e-9]
print(f"  上升 {len(up)} 案, 下降 {len(down)} 案, 不变 {len(same)} 案")
big = sorted(up, key=lambda d: -(d['new_recall'] - d['old_r_main']))[:8]
print("  上升最多:", [(d['case_id'], round(d['old_r_main'],3), round(d['new_recall'],3)) for d in big])
badd = sorted(down, key=lambda d: (d['new_recall'] - d['old_r_main']))[:5]
print("  下降最多:", [(d['case_id'], round(d['old_r_main'],3), round(d['new_recall'],3)) for d in badd])

print()
print("prec 变化（旧单元数分母 -> 新点数分母）:")
old_p = [d['old_prec'] for d in diffs if d['old_prec'] is not None]
new_p = [d['new_prec'] for d in diffs if d['new_prec'] is not None]
import statistics
print(f"  旧 prec 宏: {statistics.mean(old_p):.4f}  新 prec 宏: {statistics.mean(new_p):.4f}")
print(f"  旧 r_main 宏: {statistics.mean([d['old_r_main'] for d in diffs]):.4f}  新 recall 宏: {statistics.mean([d['new_recall'] for d in diffs]):.4f}")

print()
print("九轮新口径（宏平均 recall/prec/f1/jac, 主穴）:")
for lab in ['v140','v2','v3','v4','v5','v6','v7','v8','v9']:
    m = S[lab]['metrics']['main']['macro']
    print(f"  {lab}: {m['recall']:.4f}/{m['prec']:.4f}/{m['f1']:.4f}/{m['jac']:.4f}")
print("九轮新口径（主+佐 recall）:")
for lab in ['v140','v2','v3','v4','v5','v6','v7','v8','v9']:
    m = S[lab]['metrics']['all']['macro']
    print(f"  {lab}: {m['recall']:.4f}/{m['prec']:.4f}/{m['f1']:.4f}/{m['jac']:.4f}")
