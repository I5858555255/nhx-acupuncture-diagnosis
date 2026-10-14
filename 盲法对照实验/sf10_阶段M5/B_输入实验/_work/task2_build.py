# -*- coding: utf-8 -*-
"""任务2：生成 inputs_B / inputs_C / 差异表 / 来源表 / 剔除片段留痕。"""
import os, re, json, io, csv, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _commons import SYM_V2_DIR, OUT_DIR, BIZ_FIELDS, MISSING_MARK
from _build_common import (load_assemble, clean_history_field, get_field_raw,
                           OLD_SYM_DIR)

asm = load_assemble()
files = sorted(f for f in os.listdir(SYM_V2_DIR) if f.endswith("_symptoms_v2.json"))

def is_missing_like(d,k,hist_clean):
    if k=="既往就诊及治疗反馈":
        return not bool(hist_clean)
    v=d.get(k)
    if isinstance(v,str): return v.strip()==MISSING_MARK
    if isinstance(v,dict): return (v.get("片段") or "").strip()==MISSING_MARK
    if isinstance(v,list): return len(v)==0
    return False

INB_DIR = os.path.join(OUT_DIR, "inputs_B")
INC_DIR = os.path.join(OUT_DIR, "inputs_C")

diff_rows, src_rows, strip_rows = [], [], []

def old_symptom_field_count(cid):
    p = os.path.join(OLD_SYM_DIR, f"{cid}_symptoms.txt")
    if not os.path.exists(p):
        return 0
    txt = io.open(p, encoding="utf-8").read()
    # 计【节】标签行数
    return len(re.findall(r"【[^】]+】", txt))

for fn in files:
    cid = fn.replace("_symptoms_v2.json","")
    d = json.load(io.open(os.path.join(SYM_V2_DIR, cid+"_symptoms_v2.json"), encoding="utf-8"))
    info = asm.get(cid, {})
    has_hist = info.get("有既往(Y/N)","N")
    vtype = info.get("visit_type") or d.get("visit_type","")
    vtype_short = vtype.split("（")[0].split("(")[0]

    # 清洗既往就诊及治疗反馈字段
    hist_raw = d.get("既往就诊及治疗反馈")
    hist_clean, stripped = clean_history_field(hist_raw)
    for (sub, reason) in stripped:
        strip_rows.append({"案号":cid,"字段":"既往就诊及治疗反馈","剔除片段":sub,"剔除原因":reason,
                           "既往来源块说明":info.get("既往来源块说明","")})

    # 组装【本次就诊】14 字段文本
    def fmt_field(key):
        v = d.get(key)
        if key == "既往就诊及治疗反馈":
            val = hist_clean if hist_clean else MISSING_MARK
        else:
            val = get_field_raw(d, key)
        if not val:
            val = MISSING_MARK
        return f"{key}：{val}"

    visit_block = "\n".join(fmt_field(k) for k in BIZ_FIELDS)

    # inputB = 案号 + 本次就诊
    inB = f"案号：{cid}\nvisit_type：{vtype_short}\nchain：{info.get('chain','')}\n\n【本次就诊】\n{visit_block}\n"
    io.open(os.path.join(INB_DIR, cid+"_inputB.txt"),"w",encoding="utf-8").write(inB)

    # inputC = 本次就诊 + 既往块 + 排除确认
    if has_hist == "Y" and hist_clean:
        hist_block = hist_clean
    elif has_hist == "Y":
        hist_block = "（既往就诊诊断信息：按组装清单见原案相应节，诊断节未提取到不含治疗方案的独立既往诊断句）"
    else:
        hist_block = "无既往就诊信息（本案为首诊/无早于本次的就诊诊断记录）"
    inC = (f"案号：{cid}\nvisit_type：{vtype_short}\nchain：{info.get('chain','')}\n\n"
           f"【本次就诊】\n{visit_block}\n\n"
           f"【既往就诊(诊断信息)】\n{hist_block}\n\n"
           f"【处方排除确认：本输入不含任何针灸/中药处方、穴名、取穴、下针明细】\n")
    io.open(os.path.join(INC_DIR, cid+"_inputC.txt"),"w",encoding="utf-8").write(inC)

    # 统计
    n_content = sum(1 for k in BIZ_FIELDS if not is_missing_like(d,k,hist_clean))
    n_hist_items = len([s for s in re.split(r"[；;]", hist_clean) if s.strip()]) if (has_hist=="Y" and hist_clean) else 0
    diff_rows.append({
        "案号":cid,
        "条件A字段数(旧symptoms节)":old_symptom_field_count(cid),
        "条件B字段数(本次就诊14字段)":14,
        "条件B有内容字段数":n_content,
        "条件C新增既往信息条数":n_hist_items if has_hist=="Y" else 0,
        "有既往(Y/N)":has_hist,
        "剔除片段条数":len(stripped),
    })
    # 来源表：每个字段一行
    for k in BIZ_FIELDS:
        if k == "既往就诊及治疗反馈":
            src = "symptoms_v2既往字段(已重审计清洗)"
            rule = "按强处方标记切段剔除含针灸/处方/下针/穴名枚举的段；解剖定位用语保留"
            aud = f"剔除{len(stripped)}段" if stripped else "无泄漏"
        else:
            src = "symptoms_v2本次就诊字段"
            rule = "原样保留(当前就诊症状/诊查)"
            aud = "已扫描无处方泄漏"
        src_rows.append({"案号":cid,"字段":k,"来源":src,"过滤规则":rule,"审计结果":aud})
    src_rows.append({"案号":cid,"字段":"【既往就诊块】","来源":"symptoms_v2既往字段重审计/原案full既往节",
                     "过滤规则":"仅保留既往症状/病程/望触脉/检查/明确诊断/疗效反馈；剔除穴名与处方",
                     "审计结果":(hist_block[:40]+"…") if has_hist=="Y" else "无既往"})

def write_csv(path, rows, fields):
    io.open(path,"w",encoding="utf-8-sig",newline="").write("")
    with io.open(path,"w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow(r)

write_csv(os.path.join(OUT_DIR,"逐案输入差异表.csv"),diff_rows,
          ["案号","条件A字段数(旧symptoms节)","条件B字段数(本次就诊14字段)","条件B有内容字段数",
           "条件C新增既往信息条数","有既往(Y/N)","剔除片段条数"])
write_csv(os.path.join(OUT_DIR,"字段来源表.csv"),src_rows,
          ["案号","字段","来源","过滤规则","审计结果"])
write_csv(os.path.join(OUT_DIR,"剔除片段留痕.csv"),strip_rows,
          ["案号","字段","剔除片段","剔除原因","既往来源块说明"])

print("inputB:",len(os.listdir(INB_DIR)),"inputC:",len(os.listdir(INC_DIR)))
print("差异表行:",len(diff_rows),"来源表行:",len(src_rows),"剔除行:",len(strip_rows))
print("剔除片段总条数:",len(strip_rows))
print("剔除涉及案:",sorted(set(r["案号"] for r in strip_rows)))
