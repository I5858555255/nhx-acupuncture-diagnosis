# -*- coding: utf-8 -*-
"""自检①：扫描 inputs_C(及 inputs_B) 残留穴名/处方词。"""
import os, io, sys, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _commons import OUT_DIR, scan_text

INC = os.path.join(OUT_DIR, "inputs_C")
INB = os.path.join(OUT_DIR, "inputs_B")

# 处方词（强）
RX = ["針灸處方","针灸处方","針處方","中藥處方","中药处方","下針","下针","取穴","配穴",
      "埋針","埋耳針","放血","同前穴","針同前","開四關","膝五針","三皇穴","眼四針",
      "處方","处方","針灸","针灸"]

def scan_dir(d):
    rows=[]
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".txt"): continue
        txt=io.open(os.path.join(d,fn),encoding="utf-8").read()
        cid=fn.replace("_inputC.txt","").replace("_inputB.txt","")
        # 排除排除确认声明行本身
        body=txt.replace("【处方排除确认：本输入不含任何针灸/中药处方、穴名、取穴、下针明细】","")
        acu_hits=set(); rx_hits=set()
        for k,w,s in scan_text(body):
            if k=="穴名": acu_hits.add(w)
        for w in RX:
            if w in body: rx_hits.add(w)
        if acu_hits or rx_hits:
            rows.append((cid,sorted(acu_hits),sorted(rx_hits)))
    return rows

print("=== inputs_C 残留命中 ===")
c=scan_dir(INC)
for cid,a,r in c:
    print(cid,"| 穴名:",a,"| 处方词:",r)
print("inputs_C 有残留案数:",len(c))
print("=== inputs_B 残留命中 ===")
b=scan_dir(INB)
for cid,a,r in b:
    print(cid,"| 穴名:",a,"| 处方词:",r)
print("inputs_B 有残留案数:",len(b))
