# -*- coding: utf-8 -*-
"""make_manifest.py — 冻结 manifest（BENCHMARK-AUDIT-01 工作项 A）

对冻结基线计算 SHA-256 生成只读清单 manifest.json：
  - v9 技能 SKILL.md 与 references
  - 93 案症状 + 93 案 gold（处方）
  - v140..v9 各轮盲法输出 JSON
  - 旧评分/解析脚本与旧判分产物
  - benchmark_v2 新产物（评分器/归一化器/gold v2/判分/审计/差异报告）
并输出校验脚本所需数据（verify 时按 manifest 重新计算比对）。
"""
import json, os, hashlib, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BLIND = os.path.dirname(HERE)          # 盲法对照实验目录
ROOT = os.path.dirname(BLIND)           # 项目根（由脚本位置推导）


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def collect(group, paths):
    out = []
    for p in paths:
        if not os.path.exists(p):
            out.append({'path': p, 'exists': False, 'sha256': None})
            continue
        out.append({'path': p, 'exists': True, 'sha256': sha256(p),
                    'size': os.path.getsize(p)})
    return out

manifest = {
    'generated_at': datetime.datetime.now().isoformat(timespec='seconds'),
    'purpose': 'BENCHMARK-AUDIT-01 冻结基线；当前结果只归档不覆盖；新评分输出至 benchmark_v2/',
    'groups': {},
}

# A1 技能（v9 最终版）
skill_files = [
    os.path.join(ROOT, 'doubao-acupuncture-diagnosis', 'skill', 'SKILL.md'),
]
ref_dir = os.path.join(ROOT, 'doubao-acupuncture-diagnosis', 'skill', 'references')
if os.path.isdir(ref_dir):
    for fn in sorted(os.listdir(ref_dir)):
        skill_files.append(os.path.join(ref_dir, fn))
manifest['groups']['skill_v9'] = collect('skill', skill_files)

# A2 测试集：93 案症状 + 处方（gold）
sym_dir = os.path.join(BLIND, '盲法93', 'symptoms')
pres_dir = os.path.join(BLIND, '盲法93', 'prescriptions')
manifest['groups']['symptoms93'] = collect('symptoms', [os.path.join(sym_dir, f) for f in sorted(os.listdir(sym_dir))])
manifest['groups']['prescriptions93'] = collect('prescriptions', [os.path.join(pres_dir, f) for f in sorted(os.listdir(pres_dir))])

# A3 各轮盲法输出 JSON
blind_files = [
    (os.path.join(BLIND, '盲法140', '_blind140_results.json'), 'v140'),
    (os.path.join(BLIND, '盲法93', '_blind93_results.json'), 'v2'),
    (os.path.join(BLIND, '盲法93_v3', '_blind93v3_results.json'), 'v3'),
    (os.path.join(BLIND, '盲法93_v4', '_blind93v4_results.json'), 'v4'),
    (os.path.join(BLIND, '盲法93_v5', '_blind93v5_results.json'), 'v5'),
    (os.path.join(BLIND, '盲法93_v6', '_blind93v6_results.json'), 'v6'),
    (os.path.join(BLIND, '盲法93_v7', '_blind93v7_results.json'), 'v7'),
    (os.path.join(BLIND, '盲法93_v8', '_blind93v8_results.json'), 'v8'),
    (os.path.join(BLIND, '盲法93_v9', '_blind93v9_results.json'), 'v9'),
]
manifest['groups']['blind_outputs'] = [
    {'tag': tag, 'path': p, 'exists': os.path.exists(p),
     'sha256': sha256(p) if os.path.exists(p) else None}
    for p, tag in blind_files]

# A4 旧脚本与旧判分产物（只读基线）
old_files = [
    (os.path.join(BLIND, '盲法93_v9', 'gold_parse93v9.py'), 'gold_parse93v9.py'),
    (os.path.join(BLIND, '盲法93_v9', 'score93v9.py'), 'score93v9.py'),
    (os.path.join(BLIND, '盲法93_v9', '_gold_results93v9.pkl'), '_gold_results93v9.pkl'),
    (os.path.join(BLIND, '盲法93_v9', '判分汇总.json'), '判分汇总.json(旧)'),
    (os.path.join(BLIND, '盲法93_v9', '判分明细.csv'), '判分明细.csv(旧)'),
    (os.path.join(BLIND, '盲法93_v9', '盲法93v9回归报告.md'), '盲法93v9回归报告.md'),
    (os.path.join(BLIND, '技能迭代收敛报告.md'), '技能迭代收敛报告.md'),
    (os.path.join(BLIND, 'GH蒸馏落地报告.md'), 'GH蒸馏落地报告.md'),
]
manifest['groups']['old_baseline'] = [
    {'tag': tag, 'path': p, 'exists': os.path.exists(p),
     'sha256': sha256(p) if os.path.exists(p) else None}
    for p, tag in old_files]

# A5 benchmark_v2 新产物（本阶段冻结）
new_files = [
    ('normalize_acupoints.py', os.path.join(HERE, 'normalize_acupoints.py')),
    ('gold_parse93v2.py', os.path.join(HERE, 'gold_parse93v2.py')),
    ('score_benchmark_v2.py', os.path.join(HERE, 'score_benchmark_v2.py')),
    ('verify_benchmark_v2.py', os.path.join(HERE, 'verify_benchmark_v2.py')),
    ('analyze_diff_v2.py', os.path.join(HERE, 'analyze_diff_v2.py')),
    ('_gold_results93v2.json', os.path.join(HERE, '_gold_results93v2.json')),
    ('_gold_results93v2.pkl', os.path.join(HERE, '_gold_results93v2.pkl')),
    ('判分汇总v2.json', os.path.join(HERE, '判分汇总v2.json')),
    ('判分明细v2.csv', os.path.join(HERE, '判分明细v2.csv')),
    ('审计日志v2.json', os.path.join(HERE, '审计日志v2.json')),
    ('旧新口径差异报告.md', os.path.join(HERE, '旧新口径差异报告.md')),
]
manifest['groups']['benchmark_v2'] = [
    {'tag': tag, 'path': p, 'exists': os.path.exists(p),
     'sha256': sha256(p) if os.path.exists(p) else None}
    for tag, p in new_files]

with open(os.path.join(HERE, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# 汇总统计
total = sum(len(v) for v in manifest['groups'].values())
missing = [e for g in manifest['groups'].values() for e in g if not e.get('exists')]
print(f"manifest 已生成: {total} 个文件条目, 缺失 {len(missing)}")
for e in missing:
    print("  MISSING:", e.get('path'))
print("保存至:", os.path.join(HERE, 'manifest.json'))
