# -*- coding: utf-8 -*-
"""任务1：symptoms_v2 字段完整性核验 + 泄漏隔离审计（修正 list 处理 + 分类）。"""
import os, re, json, io, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _commons import SYM_V2_DIR, OUT_DIR, BIZ_FIELDS, MISSING_MARK, scan_text

ANATOMY_POINTS = {"缺盆","膏肓","膻中","禾髎","迎香"}
RX = ["針灸處方","针灸处方","針處方","中藥處方","中药处方","下針","下针","取穴","配穴",
      "埋針","埋耳針","放血","同前穴","針同前","開四關","膝五針","三皇穴","眼四針",
      "處方","处方","針灸","针灸"]
SCRIPT_WORD = {"針灸處方","针灸处方","針處方","中藥處方","中药处方","下針","下针","取穴",
               "配穴","埋針","埋耳針","放血","同前穴","針同前","開四關","膝五針","三皇穴","眼四針"}
rx_dir = re.compile(r"針\s*[左右雙患]")

def classify(snip):
    acu = set(w for (k,w,_) in scan_text(snip) if k=="穴名")
    rxhit = [w for w in RX if w in snip]
    dirhit = bool(rx_dir.search(snip))
    has_script_word = bool(SCRIPT_WORD & set(rxhit))
    has_zhenjiu = ("針灸" in snip) or ("针灸" in snip)
    sym_words = any(w in snip for w in ["痛","腫","肿","麻","癢","痒","處","结","結","下一寸",
                                        "酸","軟","无力","無力","拉","抽","感","位置","處","達"])
    bare_enum = (len(acu) >= 2 and "、" in snip and not sym_words)
    # 真泄漏：处方词/针刺方位动词/针灸+具体穴名/裸穴名枚举
    if dirhit or has_script_word or (has_zhenjiu and acu) or bare_enum:
        why=[]
        if dirhit: why.append("针刺方位动词(針+左右雙)")
        if has_script_word: why.append("处方词("+"/".join(sorted(SCRIPT_WORD & set(rxhit)))+")")
        if has_zhenjiu and acu: why.append("针灸+具体穴名("+"/".join(sorted(acu))+")")
        if bare_enum: why.append("裸穴名枚举("+"/".join(sorted(acu))+")")
        return "泄漏", "；".join(why)
    if rxhit:
        return "疑似", "元注释：提及处方/针灸字样但未列具体穴位("+"/".join(rxhit)+")"
    if acu:
        if ("子宮" in acu and ("卵巢" in snip or "切除" in snip or "奶水" in snip)):
            return "干净", "误命中：'子宮'指子宫器官(手术/妇科史)"
        if "膝關" in acu and "關節" in snip:
            return "干净", "误命中：'膝關'系'膝關節'片段"
        if "日月" in acu and "月經" in snip:
            return "干净", "误命中：'日月'系'月經/日期'片段"
        return "疑似", "解剖定位/测量用语(描述症状部位，非治疗处方)"
    return "干净", "无穴名/处方词"

def segs_of(v):
    if isinstance(v,list):
        return [(it.get("片段","") if isinstance(it,dict) else str(it)) for it in v]
    if isinstance(v,dict):
        return [v.get("片段","") or ""]
    if isinstance(v,str):
        return [v]
    return []

files = sorted(f for f in os.listdir(SYM_V2_DIR) if f.endswith("_symptoms_v2.json"))
rows_complete, rows_leak = [], []
case_verdict = {}

for fn in files:
    cid = fn.replace("_symptoms_v2.json","")
    d = json.load(io.open(os.path.join(SYM_V2_DIR,fn),encoding="utf-8"))
    present=[k for k in BIZ_FIELDS if k in d]
    missing_key=[k for k in BIZ_FIELDS if k not in d]
    bad_struct=[]; miss_content=[]
    for k in present:
        v=d.get(k)
        if isinstance(v,dict) and ("片段" not in v or "定位" not in v): bad_struct.append(k)
        if not isinstance(v,(dict,list,str)): bad_struct.append(k)
        for s in segs_of(v):
            if isinstance(s,str) and s.strip()==MISSING_MARK:
                miss_content.append(k); break
    excl=d.get("当前处方排除确认")
    hits=[]
    for k in present:
        for s in segs_of(d.get(k)):
            if not s or s==MISSING_MARK: continue
            if not scan_text(s): continue
            verdict,note=classify(s)
            acu=sorted(set(w for (kk,w,_) in scan_text(s) if kk=="穴名"))
            rxh=sorted(set(w for w in RX if w in s))
            hits.append((k,s,verdict))
            rows_leak.append({"案号":cid,"字段":k,"命中穴名":"/".join(acu),"处方词":"/".join(rxh),
                              "片段":s.replace("\n"," ")[:280],"判定":verdict,"判定说明":note})
    n_leak=sum(1 for h in hits if h[2]=="泄漏"); n_sus=sum(1 for h in hits if h[2]=="疑似")
    v = "泄漏" if n_leak else ("疑似" if n_sus else "干净")
    case_verdict[cid]=v
    rows_complete.append({"案号":cid,"结构业务字段数":len(present),
        "缺结构字段":";".join(missing_key) or "","结构异常字段":";".join(bad_struct) or "",
        "有内容字段数":len(present)-len(miss_content),
        "缺失清单(原文未记录)":";".join(sorted(set(miss_content))),
        "处方排除确认":excl,"泄漏命中段数":len(hits),"其中泄漏段":n_leak,"其中疑似段":n_sus,
        "泄漏判定":v})

def write_csv(path,rows,fields):
    io.open(path,"w",encoding="utf-8-sig",newline="").write("")
    with io.open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

write_csv(os.path.join(OUT_DIR,"字段完整性核验表.csv"),rows_complete,
    ["案号","结构业务字段数","缺结构字段","结构异常字段","有内容字段数","缺失清单(原文未记录)",
     "处方排除确认","泄漏命中段数","其中泄漏段","其中疑似段","泄漏判定"])
write_csv(os.path.join(OUT_DIR,"symptoms_v2泄漏审计明细.csv"),rows_leak,
    ["案号","字段","命中穴名","处方词","片段","判定","判定说明"])

from collections import Counter
print("文件数:",len(files))
print("判定分布:",Counter(case_verdict.values()))
print("泄漏案:",[c for c,x in case_verdict.items() if x=="泄漏"])
print("疑似案:",[c for c,x in case_verdict.items() if x=="疑似"])
print("明细行数:",len(rows_leak),"明细判定:",Counter(r["判定"] for r in rows_leak))
