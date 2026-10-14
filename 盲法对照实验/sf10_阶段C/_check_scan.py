# -*- coding: utf-8 -*-
import json, io
rows = json.load(io.open(r'D:\projectAGI\nhx\盲法对照实验\全集针灸首诊\_scan_all.json', encoding='utf-8'))
cases = ['311_01','312_01','318_01','323_01','340_01','342_01','345_01','346_01','347_01','355_01','37_01','38_01','49_01','55_01','57_01','60_01','61_01','62_01','63_01']
for c in cases:
    n, b = c.split('_')
    n, b = int(n), int(b)
    found = False
    for r in rows:
        if r.get('doc')==n and r.get('block')==b:
            print(c, '| chu=', r.get('初診日期'), '| lai=', r.get('來診日期'), '| first=', r.get('首诊'), '| acup=', r.get('含針灸'))
            found = True
            break
    if not found:
        print(c, '| NOT FOUND')
