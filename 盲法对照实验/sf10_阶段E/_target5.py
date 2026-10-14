# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)

for cid in ['201_01','207_01','318_01','216_04','156_05']:
    c = cons[cid]
    print("="*100)
    print(f"### {cid}  visit={c['visit_type']} chain={c['chain']} 有既往={c['有既往']} 缺字段={c['n_missing']}")
    print(f"來診原因: {c['cause']}")
    print(f"缺失字段: {c['missing']}")
    print(f"gold({c['gold_n_csv']}): {c['gold_members']}")
    print(f"gold_note: {c['gold_note']}")
    print(f"gold_raw: {c['gold_raw']}")
    print(f"TP={c['TP']}\nFN={c['FN']}\nFP={c['FP']}")
    print(f"HIST: TP={c['hist'].get('TP')} FN={c['hist'].get('FN')} FP={c['hist'].get('FP')}")
    print("-- v10 主穴记录 --")
    for p, recs in c['pointmap'].items():
        for r in recs:
            print(f"   {p} [{r['层']}] 单元={r['单元']} 推断={r['推断']} 规则={r['直接规则']} | 依据={r['依据']}")
    print(f"-- 推理要点 --\n{c['推理要点']}")
    print(f"-- 临床参考建议: {json.dumps(c['临床参考建议'], ensure_ascii=False)}")
