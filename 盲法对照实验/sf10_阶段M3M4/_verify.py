# -*- coding: utf-8 -*-
import json
from collections import Counter
j = json.load(open(r'D:\projectAGI\nhx\盲法对照实验\盲法93_v12\判分汇总v12.json', encoding='utf-8'))
m86, m64 = j['全量86'], j['核心集64']
checks = [
    ('86 v12 main宏', [m86['v12']['metrics']['main']['macro'][k] for k in ('recall','prec','f1','jac')], [0.5221,0.4959,0.4854,0.3423]),
    ('64 v12 main宏', [m64['v12']['metrics']['main']['macro'][k] for k in ('recall','prec','f1','jac')], [0.5698,0.4975,0.5052,0.3591]),
]
for n, got, want in checks:
    ok = all(abs(a-b) < 1e-9 for a, b in zip(got, want))
    print(n, got, 'OK' if ok else 'MISMATCH want=' + str(want))
d_f1_86 = m86['v12']['metrics']['main']['macro']['f1'] - m86['v11']['metrics']['main']['macro']['f1']
d_f1_64 = m64['v12']['metrics']['main']['macro']['f1'] - m64['v11']['metrics']['main']['macro']['f1']
d_r_86 = m86['v12']['metrics']['main']['macro']['recall'] - m86['v11']['metrics']['main']['macro']['recall']
print('dF1 86=%.4f  64=%.4f  dR 86=%.4f' % (d_f1_86, d_f1_64, d_r_86))
print('复诊 v12:', j['visit分层']['复诊']['v12'], ' v11:', j['visit分层']['复诊']['v11'])
print('首诊 v12:', j['visit分层']['首诊']['v12'], ' v11:', j['visit分层']['首诊']['v11'])
print('followup v12:', j['chain分层']['followup']['v12'], ' v11:', j['chain分层']['followup']['v11'])
print('anchor v12:', j['chain分层']['anchor_first']['v12'], ' v11:', j['chain分层']['anchor_first']['v11'])
verdicts = [r[4] for r in j['M2逐条收益']]
print('M2判定分布:', dict(Counter(verdicts)), '条数:', len(verdicts))
print('执行方差:', j['执行方差_v12_vs_v11'], '零命中:', j['零命中']['v12'], '满分:', len(j['v12满分']))
