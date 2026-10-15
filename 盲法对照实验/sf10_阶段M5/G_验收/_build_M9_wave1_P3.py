# -*- coding: utf-8 -*-
import json, io, os, datetime
G=r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段M5\G_验收"

# 各案主穴（扁平列表，按本折规则判定+症状独立辨证）
preds = {
 # followup_146 链：肺積水雙足水腫，R2启用整组
 "146_01": ["复溜","水泉","照海","公孙","内关","巨阙","关元"],
 "148_01": ["复溜","水泉","照海","公孙","内关","巨阙","关元"],
 "149_01": ["复溜","水泉","照海","公孙","内关","巨阙","关元"],
 # followup_216 链：面瘫后遗症，无规则池信号，按v14面瘫局部组
 "216_01": ["阳白透鱼腰","地仓透颊车","合谷","太冲","风池"],
 "216_02": ["迎香","巨髎","合谷","太冲","风池"],
 "216_03": ["廉泉","合谷","太冲","风池"],
 # S_156 链：腹水/小便不利，v14水肿利水组（R2信号=肺積水/雙腳水腫不命中腹水案）
 "156_03": ["阴陵泉","地机","三阴交","水分","水道","中极","章门","复溜"],
 "156_04": ["阴陵泉","地机","三阴交","水分","水道","章门","中极"],
 "156_05": ["阴陵泉","三阴交","水道","中极","复溜","太冲"],
 "156_06": ["阴陵泉","地机","三阴交","水道","中极","中脘"],
 # S_160_01：白血病+频尿，M2-13启用整组
 "160_01": ["关元","中极","水道","阴陵泉","三阴交","太冲"],
}

chains = {
 "followup_146": ["146_01","148_01","149_01"],
 "followup_216": ["216_01","216_02","216_03"],
 "S_156_03": ["156_03"],
 "S_156_04": ["156_04"],
 "S_156_05": ["156_05"],
 "S_156_06": ["156_06"],
 "S_160_01": ["160_01"],
}

ts = datetime.datetime.now().isoformat(timespec="seconds")
wave1 = {}
for chain, cases in chains.items():
    rules = json.load(io.open(os.path.join(G,f"M9-fold_{chain}_rules.json"),encoding="utf-8"))
    pred = {c: {"主穴": preds[c]} for c in cases}
    # pred.json
    with io.open(os.path.join(G,f"M9-fold_{chain}_pred.json"),"w",encoding="utf-8") as f:
        json.dump(pred,f,ensure_ascii=False,indent=1)
    # locked snapshot
    locked = {"heldout":chain,"ts":ts,
              "规则判定":{r["id"]:r["判定"] for r in rules["规则"]},
              "预测":pred}
    with io.open(os.path.join(G,f"M9-fold_{chain}_locked.json"),"w",encoding="utf-8") as f:
        json.dump(locked,f,ensure_ascii=False,indent=1)
    wave1.update(pred)
    print(f"{chain}: {cases} -> pred/locked written")

with io.open(os.path.join(G,"M9-wave1_preds_P3.json"),"w",encoding="utf-8") as f:
    json.dump(wave1,f,ensure_ascii=False,indent=1)

print("---- wave1 summary (11 cases) ----")
for c,v in wave1.items():
    print(f"  {c}: {v['主穴']}")
print("wave1 written:", os.path.join(G,"M9-wave1_preds_P3.json"))
