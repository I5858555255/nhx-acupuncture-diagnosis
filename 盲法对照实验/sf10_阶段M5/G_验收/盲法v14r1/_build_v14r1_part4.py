# -*- coding: utf-8 -*-
import json, io, os
G=r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收"
src=os.path.join(G,"盲法v14r7","_blind93v14r7_part4.json")
data=json.load(io.open(src,encoding="utf-8"))
for r in data:
    r["推理要点"] += "。R1(M2-16足跟痛组)核验：本案无足跟/腳跟/脚跟跟部局部痛信号，亦非脚底冷/外踝痛/足外侧冷/双踝水肿排除域，R1不触发，不取水泉+对侧大陵"
os.makedirs(os.path.join(G,"盲法v14r1"),exist_ok=True)
out=os.path.join(G,"盲法v14r1","_blind93v14r1_part4.json")
json.dump(data,io.open(out,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

# self-check
d=json.load(io.open(out,encoding="utf-8"))
raw=io.open(out,encoding="utf-8").read()
ids=["311_01","312_01","318_01","323_01","340_01","342_01","345_01","346_01","347_01","355_01","37_01","38_01","49_01","55_01","57_01","60_01","61_01","62_01","63_01"]
print("n=%d ids_ok=%s"%(len(d),[r["case_id"] for r in d]==ids))
b3=[(r["case_id"],len(r["主穴"])) for r in d if not(1<=len(r["主穴"])<=8)]
print("主穴3-8违规=%s"%(b3 if b3 else "无"))
b4=[r["case_id"] for r in d if r["主穴分层"]["对症"]+r["主穴分层"]["俞募背俞"]+r["主穴分层"]["八脉交会"]+r["主穴分层"]["特效奇穴"]!=r["主穴"]]
print("并集违规=%s"%(b4 if b4 else "无"))
c1=[(r["case_id"],x) for r in d for x in r["主穴"] if x in("肘尖","天应","天應")]
print("C1=%s"%(c1 if c1 else "无"))
c5=[r["case_id"] for r in d if r["case_id"] in("60_01","61_01","62_01","63_01") and "梁丘" not in r["主穴"]]
print("C5=%s"%(c5 if c5 else "无"))
bad=[w for w in ["診斷","診断","針灸處方","针灸处方"] if w in raw]
print("禁词=%s"%(bad if bad else "0"))
bad6=[(r["case_id"],x) for r in d for x in r["主穴"]+r["佐穴"]+r["备选"] if any(c in x for c in "（）()/")]
print("括号斜杠=%s"%(bad6 if bad6 else "无"))
bad8=[r["case_id"] for r in d if "已反查特效库" not in r["推理要点"]]
print("反查=%s"%(bad8 if bad8 else "无"))
r1=[(r["case_id"],[x for x in r["主穴"] if x in("水泉","大陵")]) for r in d]
r1=[x for x in r1 if x[1]]
print("R1触发现(主穴含水泉/大陵)=%s"%(r1 if r1 else "无"))
lens=[len(r["主穴"]) for r in d]
print("主穴均数=%.2f 区间%d-%d"%(sum(lens)/len(lens),min(lens),max(lens)))
