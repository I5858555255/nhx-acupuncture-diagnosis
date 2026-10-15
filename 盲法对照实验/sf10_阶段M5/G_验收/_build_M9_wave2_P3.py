# -*- coding: utf-8 -*-
import json, io, os, datetime
G=r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收"

preds = {
 "323_01": ["阳白透鱼腰","颊车","合谷","太冲","风池","外关+足临泣"],
 "340_01": ["耳针肾膀胱区压痛点","太溪"],
 "342_01": ["太渊","膻中","复溜","足三里","公孙+内关"],
 "345_01": ["复溜","风池","太溪","百会","后溪+申脉"],
 "346_01": ["膏肓","风池","风门","天突","合谷","列缺+照海"],
 "347_01": ["大杼","太渊","足三里","公孙+内关","肩井"],
}
chains = {
 "S_323_01": ["323_01"],
 "S_340_01": ["340_01"],
 "S_342_01": ["342_01"],
 "S_345_01": ["345_01"],
 "S_346_01": ["346_01"],
 "S_347_01": ["347_01"],
}
ts=datetime.datetime.now().isoformat(timespec="seconds")
wave2={}
for chain, cases in chains.items():
    rules=json.load(io.open(os.path.join(G,f"M9-fold_{chain}_rules.json"),encoding="utf-8"))
    pred={c:{"主穴":preds[c]} for c in cases}
    with io.open(os.path.join(G,f"M9-fold_{chain}_pred.json"),"w",encoding="utf-8") as f:
        json.dump(pred,f,ensure_ascii=False,indent=1)
    locked={"heldout":chain,"ts":ts,
            "规则判定":{r["id"]:r["判定"] for r in rules["规则"]},
            "预测":pred}
    with io.open(os.path.join(G,f"M9-fold_{chain}_locked.json"),"w",encoding="utf-8") as f:
        json.dump(locked,f,ensure_ascii=False,indent=1)
    wave2.update(pred)
    print(f"{chain}: {cases} -> pred/locked written")
with io.open(os.path.join(G,"M9-wave2_preds_P3.json"),"w",encoding="utf-8") as f:
    json.dump(wave2,f,ensure_ascii=False,indent=1)
print("---- wave2 (6 cases) ----")
for c,v in wave2.items(): print(f"  {c}: {v['主穴']}")
print("wave2 written:", os.path.join(G,"M9-wave2_preds_P3.json"))
